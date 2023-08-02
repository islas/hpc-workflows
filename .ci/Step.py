from enum import Enum
import subprocess
import sys

from SubmitOptions import SubmitOptions

SUBMIT_NAME = "{test}_{step}"

class Step():

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


  def __init__( self, testname, name, stepDict, defaultSubmitOptions = SubmitOptions() ) :
    self.test_      = testname
    self.name_      = name
    self.step_      = stepDict
    self.submitted_ = False
    self.jobid_     = -1
    self.command_       = None
    self.arguments_     = None
    self.dependencies_  = {} # our steps we are dependent on and their type
    self.depSignOff_    = {} # steps we are dependent on will need to tell us when to go
    self.children_      = [] # steps that are dependent on us that we will need to sign off for
    self.submitOptions_ = defaultSubmitOptions

    self.parse()

  def parse( self ) :

    key = "command"
    if key in self.step_ :
      self.command_ = self.step_[ key ]

    key = "arguments"
    if key in self.step_ :
      self.arguments_ = self.step_[ key ]

    key = "dependencies"
    if key in self.step_ :
      for depStep, depType in self.step_[ key ].items() :
        self.dependencies_[ depStep ] = Step.DependencyType( depType )
    
    key = "submit_options"
    if key in self.step_ :
      self.submitOptions_.update( SubmitOptions( self.step_[ key ] ) )

    # Now set things manually
    self.submitOptions_.name_ = SUBMIT_NAME.format( test=self.test_, step=self.name_ )

    valid = self.submitOptions_.validate()
    if not valid :
      err = "Error: Invalid submission options\n{0}".format( self.submitOptions_ )
      print( err )
      raise Exception( err )

  def formatDependencies( self ) :
    allDepsJobID = True
    deps         = { depType : [] for depType in DependencyType }

    for dep, jobid in self.depSignOff_.items() :
      allDepsJobID = ( jobid != -1 ) and allDepsJobID
      deps[ self.dependencies_[ dep ] ].append( jobid )

    # only perform list comprehension if we have dependencies,
    # then join all types with ","
    depsFormat = ",".join(
                          [ depType.value + ":" + ":".join( depsJobIDs ) 
                            for depType, depsJobIDs in deps 
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
  
  def run( self ) :
    # Do submission logic....
    print( "Submitting step {0}...".format( self.name_ ) )
    self.submitted_ = True
  
    output = ""
    err    = ""
    retVal = -1
    args   = [ *self.submitOptions_.format(), self.command_, *self.arguments_ ]

    if self.submitOptions_.debug_ :
      print( "Arguments: {0}".format( args ) )

    command = " ".join( [ arg if " " not in arg else "\"{0}\"".format( arg ) for arg in args ] )
    print( "Running command:\n\t{0}".format( command ) )

    if self.submitOptions_.submitType_ == SubmitOptions.SubmissionType.LOCAL :
      print( "*" * 40 )

    ############################################################################
    ##
    ## Call step
    ##
    # proc = subprocess.Popen(
    #                         args,
    #                         stdin =subprocess.PIPE if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL else None,
    #                         stdout=subprocess.PIPE if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL else None,
    #                         stderr=subprocess.PIPE if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL else None
    #                         )
    # output, err = proc.communicate()
    # retVal      = proc.returncode
    ##
    ## 
    ##
    ############################################################################

    if self.submitOptions_.submitType_ == SubmitOptions.SubmissionType.LOCAL :
      print( "*" * 40 )

    # Process output
    if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL :
      # Find job id
      self.jobid_ = 0
    else:
      self.jobid_ = 0


    # if submitted properly
    if retVal == 0 and self.children_ :
      print( "Notifying children..." )
      # Go to all children and mark ok
      for child in self.children_ :
        child.depSignOff_[ self.name_ ] = self.jobid_
    elif retVal != 0 :
      err = ( "Error: Failed to run step '{0}' exit code {1}\n\tlog: {2}".format(
                                                                                  self.name_,
                                                                                  retVal,
                                                                                  err if self.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL else
                                                                                    "See errors above"
                                                                                  )
            )
      print( err )
      raise Exception( err )

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
            


