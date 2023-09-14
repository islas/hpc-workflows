from enum import Enum
import subprocess
import sys
import os
import re
import io

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
    def __str__( self ) :
      return str( self.value )
    def __repr__( self ) :
      return str( self.value )
    # @staticmethod
    # def fromString( s ) :
    #   return DependencyType[ s ]


  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.submitted_ = False
    self.jobid_     = -1
    self.command_       = None
    self.arguments_     = None
    self.logfile_       = None # Filled out after submitted
    self.dependencies_  = {} # our steps we are dependent on and their type
    self.depSignOff_    = {} # steps we are dependent on will need to tell us when to go
    self.children_      = [] # steps that are dependent on us that we will need to sign off for

    super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )

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
    self.log( "Set submission name to {0}".format( self.submitOptions_.name_ ) )

    self.log( "Validating submission options..." )
    valid, msg = self.submitOptions_.validate()
    if not valid :
      err = "Error: Invalid submission options [{msg}]\n{opts}".format( msg=msg, opts=self.submitOptions_ )
      self.log( err )
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
  
  def executeInfo( self ) :
    if self.submitOptions_.lockSubmitType_ and "submission" in self.submitOptions_.submit_ :
      self.log( "{{ '{0}' : {1} }} overridden by cli".format( "submission", self.submitOptions_.submit_[ "submission" ] ) )

  def executeAction( self ) :
    # Do submission logic....
    self.log( "Submitting step {0}...".format( self.name_ ) )
    self.log_push()
    self.submitted_ = True
    self.executeInfo()
  
    output = ""
    err    = ""
    retVal = -1
    args, additionalArgs   = self.submitOptions_.format( print=self.log )
    workingDir = os.getcwd()

    args.append( os.path.abspath( self.command_ ) )
    args.append( workingDir )

    if self.arguments_ :
      args.extend( self.arguments_ )

    # Additional args added by submit_options
    if additionalArgs :
      args.extend( additionalArgs )

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
    # https://stackoverflow.com/a/18422264
    output = io.BytesIO()
    proc = subprocess.Popen(
                            args,
                            stdin =subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT
                            )
    for c in iter( lambda: proc.stdout.read(1), b"" ):
      output.write( c )
      sys.stdout.buffer.write(c)

    # We don't mind doing this as the process should block us until we are ready to continue
    dump, err = proc.communicate()
    retVal    = proc.returncode
    ##
    ## 
    ##
    ############################################################################

    print( "\n", flush=True, end="" )
    self.log(  "*" * 15 + "{:^15}".format( "STOP " + self.name_ ) + "*" * 15 )

    self.logfile_ = "{0}/{1}".format( workingDir, self.submitOptions_.getOutputFilename() )

    # if submitted properly
    if retVal == 0 :
      # Process output
      if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL :
        content = output.getvalue().decode( 'utf-8' )
        output.close()
        self.log( "Finding job ID in \"{0}\"".format( content ) )
        # Find job id
        self.jobid_ = int( jobidRegex.match( content ).group(1) )
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
      self.log( err )

      if not self.globalOpts_.nofatal :
        raise Exception( err )
    
    self.log_pop()
    
    self.log( "Finished submitting step {0}\n".format( self.name_ ) )
  
  def postProcessResults( self ) :
    # We've been requested to output our results from this step
    try:
      self.log( "Opening log file {0}...".format( self.logfile_ ) )
      f = open( self.logfile_, "rb" )
      self.log( "Checking last line for success <KEY PHRASE> of format '{0}'".format( self.globalOpts_.key ) )
      # https://stackoverflow.com/a/54278929
      try:  # catch OSError in case of a one line file 
        f.seek( -2, os.SEEK_END )
        while f.read(1) != b'\n' :
          f.seek( -2, os.SEEK_CUR )
      except OSError:
          f.seek(0)
      lastline = f.readline().decode()

      findKey = re.match( self.globalOpts_.key, lastline )
      if findKey is None :
        errMark = "{banner} {msg} {banner}".format( banner="!" * 10, msg="ERROR" * 3 )
        self.log( errMark )
        self.log( "Missing key {0} marking success".format( self.globalOpts_.key ) )
        self.log( "Line: \"{0}\"".format( lastline ) )
        self.log( "Step {0} has failed! See logfile {1}".format( self.name_, self.logfile_ ) )
        self.log( errMark )
        if not self.globalOpts_.nofatal :
          raise Exception( errMark )
      else :
        self.log( "SUCCESS : Step {step} reported {line}".format( step=self.name_, line=lastline ) )
    except Exception as e :
      self.log( "Logfile {0} does not exist, did submission fail?".format( self.logfile_ ) )
      raise e

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
            


