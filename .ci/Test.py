import os
import sys
import json
import time
from collections import OrderedDict
from datetime import timedelta

from SubmitAction  import SubmitAction
from SubmitOptions import SubmitOptions
from Step          import Step

HPC_DELAY_PERIOD_SECONDS = 60
HPC_POLL_PERIOD_SECONDS = 120

class Test( SubmitAction ):

  def scope( self ) :
    return "test"
  
  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.steps_         = {}
    self.waitResults_    = False
    super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )

  def parseSpecificOptions( self ) :

    key = "steps"
    if key in self.options_ :
      if key == "results" :
        self.log( "Keyword 'results' not allowed as step name, reason: reserved" )
        exit( 1 )
      for stepname, stepDict in self.options_[ key ].items() :
        self.steps_[ stepname ] = Step( stepname, stepDict, self.submitOptions_, self.globalOpts_, parent=self.ancestry(), rootDir=self.rootDir_ )
    
    # Now that steps are fully parsed, attempt to organize dependencies
    Step.sortDependencies( self.steps_ )


  def executeAction( self ) :
    self.checkWaitResults()

    steps = []
    while len( steps ) != len( self.steps_ ) :
      for step in self.steps_.values() :

        if step.runnable() :
          step.run()
          steps.append( step.name_ )
      self.log( "Checking remaining steps..." )

    self.log( "No remaining steps, test submission complete" )

    return self.postProcessResults( steps )

  def checkWaitResults( self ) :
    # Do we need to add a results step?
    if self.globalOpts_.nowait :
      self.log( "No waiting for HPC submissions requested, skipping results sync" )
      return
    
    self.log( "Checking if results wait is required" )
    self.log_push()
    # Get all current steps submission type
    subs = [ step.submitOptions_.submitType_ for step in self.steps_.values() if step.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL ]
    
    if len( subs ) > 0 :
      self.log( "Final results will wait for all jobs complete" )
      self.waitResults_ = True
    else :
      self.log( "No HPC submissions, no results job added" )

    self.log_pop()
  
  def waitOnSteps( self, stepOrder ) :
    if self.globalOpts_.dryRun :
      self.log( "Doing dry-run, assumed complete" )
      return

    self.log( "Waiting for HPC jobs to finish..." )
    self.log_push()
    self.log( "*ATTENTION* : This is a blocking/sync phase to wait for all jobs to complete - BE PATIENT" )
    time.sleep( HPC_DELAY_PERIOD_SECONDS )

    # Filter steps already done
    completedSteps = [ stepname for stepname in stepOrder if self.steps_[ stepname ].submitOptions_.submitType_ == SubmitOptions.SubmissionType.LOCAL ]

    while len( completedSteps ) != len( stepOrder ) :
      # Wait N seconds before checking all steps again
      time.sleep( HPC_POLL_PERIOD_SECONDS )

      for stepname in stepOrder :
        if stepname not in completedSteps :
          self.steps_[ stepname ].log_push()
          finished = self.steps_[ stepname ].checkJobComplete()
          self.steps_[ stepname ].log_pop()
          if finished :
            completedSteps.append( stepname )

    self.log( "All HPC steps complete" )
    self.log_pop()

  def postProcessResults( self, stepOrder ) :
    # Do we need to post-process HPC submission files
    errs = False
    if not self.globalOpts_.nopost :
      if self.globalOpts_.nowait :
        self.log( "Post-processing requires waiting for HPC submissions, skipped" )
      elif self.waitResults_ :
        # Wait for grid steps to complete
        self.waitOnSteps( stepOrder )

      # All results are ready
      # We go through the steps in the order submitted
      self.log( "Outputting results..." )
      self.log_push()

      stepsLog = OrderedDict()
      for stepname in stepOrder :
        if stepname != "results" :
          success, err = self.steps_[ stepname ].postProcessResults()
          stepsLog[ stepname ] = {}
          stepsLog[ stepname ][ "logfile" ] = self.steps_[ stepname ].logfile_
          stepsLog[ stepname ][ "success" ] = success
          stepsLog[ stepname ][ "message" ] = err

      self.log( "Writing relevant logfiles to view in master log file : " )
      self.log_push()
      self.log( self.logfile_ )
      self.log_pop()

      with open( self.logfile_, "w" ) as f :
        json.dump( stepsLog, f, indent=2 )

      errs = self.reportErrs( stepsLog )

      if errs and not self.globalOpts_.nofatal :
        exit( 1 )

      self.log_pop()
    return not errs
  
  def reportErrs( self, stepsLog ) :
    success = True
    for stepname, stepResult in stepsLog.items() :
      success = success and stepResult[ "success" ]
    if not success :
      self.log( "{fail} : Steps [ {steps} ] failed".format(
                                                            fail=SubmitAction.FAILURE_STR,
                                                            steps=", ".join( [ key for key in stepsLog.keys() if not stepsLog[key]["success"] ] ) 
                                                            )
              )
      self.log( "\n".join( [ logs["message"] for step, logs in stepsLog.items() if not logs["success"] ] ) )
    else :
      # We got here without errors
        self.log( "{succ} : Test {name} completed successfully".format( succ=SubmitAction.SUCCESS_STR, name=self.name_ ) )

    return not success

  def getMaxHPCResources( self ) :
    # NOTE NOTE NOTE NOTE NOTE
    # I have made some assumptions about when things can run
    # with regards to dependency type - this could be fixed but requires
    # more complex logic. For now, try not to add too many divergent branches of testing
    self.log( "Computing maximum HPC resources per runnable step phase..." )

    # Walk through all steps and determine what HPC resources would be needed
    checked  = { }

    # Maybe use one day for complex branch analysis...
    # deps     = { depType : {} for depType in Step.DependencyType }

    # # Get all variations of dependencies
    # for step in self.steps_ :
    #   for stepname, depType in step.dependencies_ :
    #     deps[ depType ][ stepname ] = None

    maxResources = ""
    maxTimelimit = timedelta()
    hpcSubmit = [ step.submitOptions_.submitType_ for step in self.steps_.values() if step.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL ]
    if not hpcSubmit :
      self.log( "No HPC steps in this test" )
      return maxResources, maxTimelimit

    longestStep = len( max( [ stepname for stepname in self.steps_.keys() ], key=len ) )
    phase = 0
    self.log( "Joining steps..." )
    self.log_push()
    while len( checked ) != len( self.steps_ ) :
      # Gather set of runnables
      runnable = [ step for step in self.steps_.values() if step.runnable() ]

      # Add all concurrent resources together
      currentResources = SubmitOptions.joinHPCResourcesOp( runnable, lambda rhs,lhs : rhs + lhs, print=self.log  )
      currentTimelimit = max( [ SubmitOptions.parseTimelimit( step.submitOptions_.timelimit_, hpcSubmit[0] ) for step in runnable ] )
      # Get maximum
      maxResources = SubmitOptions.joinHPCResourcesStrOp(
                                                          maxResources,
                                                          currentResources,
                                                          hpcSubmit[0],
                                                          max,
                                                          print=self.log
                                                          )
      # Add to current timelimit
      maxTimelimit += currentTimelimit
      self.log( "[PHASE {phase}] Resources for [ {steps} ] : '{res}'".format(
                                                                              phase=phase,
                                                                              steps="".join(
                                                                                            "{0:>{1}}".format(
                                                                                                              step, longestStep + ( 1 if len( runnable ) > 1 else 0 ) )
                                                                                                              for step in ",[:space:]".join(
                                                                                                                 [ step.name_ for step in runnable ]
                                                                                                              ).split( '[:space:]' )
                                                                                            ),
                                                                              res=currentResources
                                                                              )
                )
      phase += 1

      # Add to checked
      checked.update( { step.name_ : step for step in runnable } )

      # For all runnable assume ran
      for step in runnable :
        step.jobid_     = 0
        step.retval_    = 0
        step.submitted_ = True
        step.notifyChildren( )
    
    # Reset the pipeline
    for step in self.steps_.values() :
      step.resetRunnable()
    self.log_pop()
    self.log( "Maximum HPC resources required will be '{0}' with timelimit '{1}'".format(
                                                                                          maxResources,
                                                                                          SubmitOptions.formatTimelimit(
                                                                                            maxTimelimit,
                                                                                            hpcSubmit[0]
                                                                                          )
                                                                                        )
              )
    return maxResources, maxTimelimit





