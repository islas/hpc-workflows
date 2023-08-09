from enum import Enum
import subprocess
import sys
import os
import re

from SubmitAction  import SubmitAction
from SubmitOptions import SubmitOptions

SUBMIT_NAME = "{test}.{step}"
jobidRegex  = re.compile( r"(\d{5,})" )

class Step( SubmitAction ):

  class DependencyType( str, Enum ):
    AFTER      = "after"
    AFTEROK    = "afterok"
    AFTERNOTOK = "afternotok"
    AFTERANY   = "afterany"
    # def __str__( self ) :
    #   return str( self.value )
    # @staticmethod
    # def fromString( s ) :
    #   return DependencyType[ s ]


  def __init__( self, name, options, defaultSubmitOptions = SubmitOptions(), parent = "", rootDir = "./" ) :
    self.submitted_ = False
    self.jobid_     = -1
    self.command_       = None
    self.arguments_     = None
    self.dependencies_  = {} # our steps we are dependent on and their type
    self.depSignOff_    = {} # steps we are dependent on will need to tell us when to go
    self.children_      = [] # steps that are dependent on us that we will need to sign off for

    super().__init__( name, options, defaultSubmitOptions, parent, rootDir )

    self.printDir_ = True

  def parseSpecificOptions( self ) :

    key = "command"
    if key in self.options_ :
      self.command_ = self.options_[ key ]

    key = "arguments"
    if key in self.options_ :
      self.arguments_ = self.options_[ key ]

    key = "dependencies"
    if key in self.options_ :
      for depStep, depType in self.options_[ key ].items() :
        self.dependencies_[ depStep ] = Step.DependencyType( depType )

    # Now set things manually
    self.submitOptions_.name_ = SUBMIT_NAME.format( test=self.parent_, step=self.name_ )

    valid = self.submitOptions_.validate()
    if not valid :
      err = "Error: Invalid submission options\n{0}".format( self.submitOptions_ )
      print( err )
      raise Exception( err )


  def formatDependencies( self ) :
    allDepsJobID = True
    deps         = { depType : [] for depType in Step.DependencyType }

    for dep, jobid in self.depSignOff_.items() :
      allDepsJobID = ( jobid != -1 ) and allDepsJobID
      deps[ self.dependencies_[ dep ] ].append( jobid )

    # only perform list comprehension if we have dependencies,
    # then join all types with ","
    depsFormat = ",".join(
                          [ depType.value + ":" + ":".join( [ str( jobid ) for jobid in depsJobIDs ] )
                            for depType, depsJobIDs in deps.items()
                              if len( depsJobIDs ) > 0 
                          ] 
                          )

    return allDepsJobID, depsFormat

  def runnable( self ) :
    canRun = False
    # If no depenedencies just run
    if not self.submitted_ :
      if not self.depSignOff_ :
        canRun = True
      else:
        # See if our dependencies are satisfied
        canRun, self.submitOptions_.dependencies_ = self.formatDependencies()

    return canRun
  
  def executeAction( self ) :
    # Do submission logic....
    self.log( "Submitting step {0}...".format( self.name_ ) )
    self.submitted_ = True
  
    output = ""
    err    = ""
    retVal = -1
    args   = self.submitOptions_.format() 

    args.append( os.path.abspath( self.command_ ) )
    args.append( os.getcwd() )

    args.extend( self.arguments_ )

    if self.submitOptions_.debug_ :
      self.log( "Arguments: {0}".format( args ) )

    command = " ".join( [ arg if " " not in arg else "\"{0}\"".format( arg ) for arg in args ] )
    self.log( "Running command:" )
    self.log( "\t{0}".format( command ) )

    self.log(  "*" * 15 + "{:^15}".format( "START " + self.name_ ) + "*" * 15 + "\n" )

    ############################################################################
    ##
    ## Call step
    ##
    proc = subprocess.Popen(
                            args,
                            stdin =subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT
                            )
    for c in iter( lambda: proc.stdout.read(1), b"" ):
      sys.stdout.buffer.write(c)

    # We don't mind doing this as the process should block us until we are ready to continue
    output, err = proc.communicate()
    retVal      = proc.returncode
    ##
    ## 
    ##
    ############################################################################

    print( "\n", flush=True, end="" )
    self.log(  "*" * 15 + "{:^15}".format( "STOP " + self.name_ ) + "*" * 15 )


    # if submitted properly
    if retVal == 0 :
      # Process output
      if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL :
        output = output.decode( "utf-8" )
        # Find job id
        self.jobid_ = int( jobidRegex.match( output ).group(1) )
      else:
        self.jobid_ = 0

      if self.children_ :
        self.log( "Notifying children..." )
        # Go to all children and mark ok
        for child in self.children_ :
          child.depSignOff_[ self.name_ ] = self.jobid_
    else:
      err = ( "Error: Failed to run step '{0}' exit code {1}\n\tlog: {2}".format(
                                                                                  self.name_,
                                                                                  retVal,
                                                                                  err if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL else
                                                                                    "See errors above"
                                                                                  )
            )
      print( err )
      raise Exception( err )
    
    self.log( "Finished submitting step {0}\n".format( self.name_ ) )

  @staticmethod
  def sortDependencies( steps ) :
    # stepnames = [ step.name_ for step in steps ]

    for stepname, step in steps.items() :
      if step.dependencies_ :
        for depStep in step.dependencies_ :
          if depStep not in steps.keys() :
            err = "Error: No step name '{0}' to set as dependency for step '{1}'".format( depStep, step.name_ )
            print( err )
            raise Exception( err )
          else:
            # Add dependency to sign off list
            step.depSignOff_[ depStep ] = -1
            
            # Add step to parent dependency
            for parentStep in steps.values() :
              if parentStep.name_ == depStep :
                parentStep.children_.append( step )
                break
            


