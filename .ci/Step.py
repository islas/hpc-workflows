from enum import Enum
import subprocess
import sys
import os
import re
import io

from SubmitCommon  import SubmissionType
from SubmitAction  import SubmitAction
from SubmitOptions import SubmitOptions

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

  def scope( self ) :
    return "step"

  def __init__( self, name, options, defaultSubmitOptions, globalOpts, lock, notifier, parent = "", rootDir = "./" ) :
    self.submitted_ = False
    self.jobid_     = None
    self.retval_    = None
    self.command_       = None
    self.arguments_     = None
    self.dependencies_  = {} # our steps we are dependent on and their type
    self.depSignOff_    = {} # steps we are dependent on will need to tell us when to go
    self.children_      = [] # steps that are dependent on us that we will need to sign off for
    # DO NOT MODIFY THIS UNLESS YOU UNDERSTAND THE IMPLICATIONS
    self.addWorkingDirArg_ = True
    self.lock_          = lock
    self.wakeTest_      = notifier

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
    self.submitOptions_ = self.submitOptions_.selectHostSpecificSubmitOptions()
    self.submitOptions_.setName( self.ancestry() )

    valid, msg = self.submitOptions_.validate()
    if not valid :
      err = "Error: Invalid submission options [{msg}]\n{opts}".format( msg=msg, opts=self.submitOptions_ )
      self.log( err )
      raise Exception( err )


  def formatDependencies( self ) :
    allDepsJobID = True
    deps         = { depType : [] for depType in Step.DependencyType }

    for dep, signoff in self.depSignOff_.items() :
      allDepsJobID = ( signoff[ "jobid" ] is not None ) and allDepsJobID
      deps[ self.dependencies_[ dep ] ].append( signoff[ "jobid" ] )

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
  
  def resetRunnable( self ) :
    self.submitted_ = False
    self.jobid_     = None
    if self.depSignOff_ :
      for key in self.depSignOff_.keys() :
        self.depSignOff_[ key ][ "jobid"  ] = None
        self.depSignOff_[ key ][ "retval" ] = None
  
  def executeInfo( self ) :
    if self.submitOptions_.lockSubmitType_ and "submission" in self.submitOptions_.submit_ :
      self.log( "{{ '{0}' : {1} }} overridden by cli".format( "submission", self.submitOptions_.submit_[ "submission" ] ) )

  def prepExecuteAction( self ) :
    # We are about to execute - these are the first to happen
    # Acquire the lock until we have finished submitting our step
    self.lock_.acquire()
    # Immediately consider ourselves submitted, thus not runnable anymore
    self.submitted_ = True

  def executeAction( self ) :
    try :
      # Do submission logic....
      self.log( "Submitting step {0}...".format( self.name_ ) )
      self.log_push()
      self.executeInfo()
      redirect = ( self.submitOptions_.submitType_ == SubmissionType.LOCAL and not self.globalOpts_.inlineLocal )
      output = None
      err    = ""
      self.retval_ = -1
      self.submitOptions_.logfile_ = self.logfile_
      args, additionalArgs   = self.submitOptions_.format( print=self.log )
      workingDir = os.getcwd()
      

      self.log( "Script : {0}".format( self.command_ ) )
      args.append( os.path.abspath( self.command_ ) )
      if self.addWorkingDirArg_ :
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
      self.log( "  {0}".format( command ) )
      self.log(  "*" * 15 + "{:^15}".format( "START " + self.name_ ) + "*" * 15 + "\n" )

      if not self.globalOpts_.dryRun :
        ############################################################################
        ##
        ## Call step
        ##
        # https://stackoverflow.com/a/18422264
        logfileOutput = open( self.logfile_, "w+", buffering=1 )
        if redirect :
          self.log( "Local step will be redirected to logfile {0}".format( self.logfile_ ) )
        else :
          # Just keep in memory as a string
          output = io.BytesIO()

        proc = subprocess.Popen(
                                args,
                                stdin =subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT
                                )

        # We are at this point only reading in the step running, no need to hold others up
        self.lock_.release()

        for c in iter( lambda: proc.stdout.read(1), b"" ):
          # Always store in logfile
          logfileOutput.write( c.decode( 'utf-8', 'replace' ) )
          logfileOutput.flush()
          if not redirect :
            output.write( c )
            sys.stdout.buffer.write(c)
            sys.stdout.flush()

        # We don't mind doing this as the process should block us until we are ready to continue
        dump, err    = proc.communicate()
        self.retval_ = proc.returncode
        ##
        ## 
        ##
        ############################################################################
      else :
        self.log( "Doing dry-run, no ouptut" )
        self.retval_ = 0
        output       = "12345"
        self.lock_.release()


      print( "\n", flush=True, end="" )
      self.log(  "*" * 15 + "{:^15}".format( "STOP " + self.name_ ) + "*" * 15 )

      # if submitted properly
      if self.retval_ == 0 :
        # Process output
        if self.submitOptions_.submitType_ != SubmissionType.LOCAL :
          content = None
          if not self.globalOpts_.dryRun :
            if redirect :
              output.seek(0)
              content = output.read()
            else : 
              content = output.getvalue().decode( 'utf-8' )
            output.close()
          else :
            content = output

          self.log( "Finding job ID in \"{0}\"".format( content.rstrip() ) )
          # Find job id
          self.jobid_ = int( jobidRegex.match( content ).group(1) )
        else:
          self.jobid_ = 0
      else:
        self.jobid_ = -1
        msg = "Error: Failed to run step '{0}' exit code {1}".format(
                                                                      self.name_,
                                                                      self.retval_ 
                                                                    )
        self.log( msg )

        if self.submitOptions_.submitType_ != SubmissionType.LOCAL and not self.globalOpts_.nofatal :
          raise Exception( msg )

      # If we get this far sign off
      if self.children_ :
        self.log( "Notifying children..." )
        # Step is done and we need to write to other steps so re-acquire the lock for safe writing 
        # ALSO do this after all error handling so we know we are safe to lock without leaving us in a catatonic state
        self.lock_.acquire()
        self.notifyChildren( )
        self.lock_.release()

      self.log_pop()
      
      self.log( "Finished submitting step {0}\n".format( self.name_ ) )

      # Tell our test to wake up and check any changes to states
      self.wakeTest_.release()

    except Exception as e :
        # If we fail, we need to tell our parent test :(
        self.wakeTest_.release()
        # And release other lock
        self.lock_.release()
        # and propagate the exception
        raise e

  def notifyChildren( self ) :
    if self.children_ :
      # Go to all children and mark ok
      for child in self.children_ :
        child.depSignOff_[ self.name_ ][ "jobid"  ] = self.jobid_
        child.depSignOff_[ self.name_ ][ "retval" ] = self.retval_
  
  def checkJobComplete( self ) :
    if self.globalOpts_.dryRun :
      self.log( "Doing dry-run, assumed complete" )
      return True

    if self.submitOptions_.submitType_ == SubmissionType.LOCAL :
      self.log( "Step is local run, already finished (why are you here?)" )
      return True
    else:
      # Probably different ways to check for PBS/SLURM
      if self.submitOptions_.submitType_ == SubmissionType.PBS :
        proc = subprocess.Popen(
                                [ "qstat", str( self.jobid_ ) ],
                                stdin =subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                                )
        output, err = proc.communicate()
        retVal    = proc.returncode
        ouptut    = output.decode( "utf-8" )
        if retVal > 0 or output == "" : # How else to tell if something is complete in PBS?
          self.log( "Job ID {0} no longer in scheduler queue, assumed complete".format( self.jobid_ ) )
          return True
        else :
          return False
      elif self.submitOptions_.submitType_ == SubmissionType.SLURM :
        self.log( "Don't know how to process SLURM job completion, assumed complete" )
        return True
    
    self.log( "Unknown completion, assumed true to avoid infinite loop" )
    return True
  
  def reportErrs( self, success, lastline ) :
    if not success :
      errMark = "{banner} {msg} {banner}".format( banner="!" * 10, msg=" ".join( ["ERROR"] * 3 ) )
      self.log( errMark )
      self.log( "{fail} : Missing key '{key}' marking success".format( fail=SubmitAction.FAILURE_STR, key=self.globalOpts_.key ) )
      self.log( "Line: \"{0}\"".format( lastline ) )
      msg = "Step {0} has failed! See logfile {1}".format( self.name_, self.logfile_ )
      self.log( msg )
      self.log( errMark )
    else :
      self.log( "{succ} : Step {step} reported \"{line}\"".format( succ=SubmitAction.SUCCESS_STR, step=self.name_, line=lastline ) )

  def postProcessResults( self ) :
    # We've been requested to output our results from this step
    self.log( "Results for {0}".format( self.name_ ) )
    self.log_push()

    if self.globalOpts_.dryRun :
      self.log( "Doing dry-run, assumed success" )
      self.log_pop()
      return True, "Ok"

    self.log( "Opening log file {0}".format( self.logfile_ ) )

    err     = "Uknown"
    success = False


    try :
      f = open( self.logfile_, "rb" )
      f.close()
    except : 
      msg = "Logfile {0} does not exist, did submission fail?".format( self.logfile_ )
      self.log( msg )
      return success, msg

    try :
      self.log( "Checking last line for success <KEY PHRASE> of format '{0}'".format( self.globalOpts_.key ) )
      lastline = SubmitAction.getLastLine( self.logfile_ )
      findKey = re.match( self.globalOpts_.key, lastline )
      success = ( findKey is not None )
      # self.reportErrs( success, lastline )
      if success :
        self.log( SubmitAction.SUCCESS_STR )
      else :
        self.log( SubmitAction.FAILURE_STR )

    except Exception as e :
      raise e
    self.log_pop()
    return success, lastline

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
            step.depSignOff_[ depStep ] = { "jobid" : None, "retval" : None }
            
            # Add step to parent dependency
            for parentStep in steps.values() :
              if parentStep.name_ == depStep :
                parentStep.children_.append( step )
                break
            


