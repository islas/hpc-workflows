import os
import sys
import json
import time
import copy
from collections import OrderedDict
from datetime import timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

from SubmitCommon  import SubmissionType
from SubmitAction  import SubmitAction
from SubmitOptions import SubmitOptions
from Step          import Step
from HpcArgpacks   import HpcArgpacks

HPC_DELAY_PERIOD_SECONDS =  60
HPC_POLL_PERIOD_SECONDS  = 120

class Test( SubmitAction ):

  def scope( self ) :
    return "test"
  
  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.steps_         = {}
    self.waitResults_    = False
    self.multiStepLock_  = threading.Lock()
    self.stepNotifier_   = threading.Semaphore( 0 ) # Starts unable to acquire
    super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )

  def parseSpecificOptions( self ) :

    key = "steps"
    if key in self.options_ :
      if key == "results" :
        msg = "Keyword 'results' not allowed as step name, reason: reserved"
        self.log( msg )
        raise Exception( msg )
      for stepname, stepDict in self.options_[ key ].items() :
        self.steps_[ stepname ] = Step(
                                        stepname,
                                        stepDict,
                                        self.submitOptions_,
                                        self.globalOpts_,
                                        self.multiStepLock_,
                                        self.stepNotifier_,
                                        parent=self.ancestry(),
                                        rootDir=self.rootDir_
                                        )
    
    # Now that steps are fully parsed, attempt to organize dependencies
    Step.sortDependencies( self.steps_ )

  def validate( self ) :
    for step in self.steps_.values() :
      step.validate()

  def executeAction( self ) :
    self.checkWaitResults()

    stepsAlreadyRun = {}
    # Since this might be the limiting computational factor in terms of how processes run
    # use the more supported ThreadPoolExecutor rather than a simple ThreadPool to enable 
    # any future growth 
    executor = ThreadPoolExecutor( max_workers=self.globalOpts_.threadpool )
    while len( stepsAlreadyRun ) != len( self.steps_ ) :
      for step in self.steps_.values() :
        if step.runnable() and step.name_ not in stepsAlreadyRun :
          stepsAlreadyRun[ step.name_ ] = submittedStep = executor.submit( step.run )

      # We have submitted all runnable steps for the current phase, and there is no guarantee
      # that all these steps need to complete at the same time so DO NOT WAIT for all
      # results, but instead patiently wait for one of the submitted steps to wake us up
      # and then check if any of our runnable states has changed, obviously if no steps
      # have completed between our last check and an arbitrary time later then no runnable states
      # will have changed either (THIS DOES NOT WORK WELL WITH LOCAL SUBMISSION AND "AFTER" ONLY DEPENDENCY)
      self.stepNotifier_.acquire()

      # Make sure anything that woke us up was okay
      for stepname, futureObj in stepsAlreadyRun.items() :
        if futureObj.done() :
          try :
            futureObj.result()
          except Exception as e :
            # Kill it all and shut down
            for k,v in stepsAlreadyRun.items() : v.cancel() # This is for prior to python 3.9
            executor.shutdown( wait=True )
            raise e

      self.log( "Checking remaining steps..." )

    # Grab anything that we are still waiting for that has already been submitted
    for stepname, futureObj in stepsAlreadyRun.items() :
      try :
        futureObj.result()
      except Exception as e :
        # Kill it all and shut down
        for k,v in stepsAlreadyRun.items() : v.cancel() # This is for prior to python 3.9
        executor.shutdown( wait=True )
        raise e
    executor.shutdown( wait=True )

    self.log( "No remaining steps, test submission complete" )

    return self.postProcessResults( stepsAlreadyRun.keys() )

  def checkWaitResults( self ) :
    # Do we need to add a results step?
    if self.globalOpts_.nowait :
      self.log( "No waiting for HPC submissions requested, skipping results sync" )
      return
    
    self.log( "Checking if results wait is required..." )
    self.log_push()
    # Get all current steps submission type
    subs = [ step.submitOptions_.submitType_ for step in self.steps_.values() if step.submitOptions_.submitType_ != SubmissionType.LOCAL ]
    
    if len( subs ) > 0 :
      self.log( "Final results will wait for all jobs complete" )
      self.waitResults_ = True
    else :
      self.log( "No HPC submissions, no results waiting required" )

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
    completedSteps = [ stepname for stepname in stepOrder if self.steps_[ stepname ].submitOptions_.submitType_ == SubmissionType.LOCAL ]

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
          stepsLog[ stepname ][ "line"    ] = err
      
      self.log_pop()

      self.log( "Writing relevant logfiles to view in master log file : " )
      self.log_push()
      self.log( self.logfile_ )
      self.log_pop()

      with open( self.logfile_, "w" ) as f :
        json.dump( stepsLog, f, indent=2 )

      errs = self.reportErrs( stepsLog )
    return not errs
  
  def reportErrs( self, stepsLog, simple=False ) :
    success = True
    for stepname, stepResult in stepsLog.items() :
      success = success and stepResult[ "success" ]
    if not success :
      if not simple :
        for stepname, stepResult in stepsLog.items() :
          if not stepResult[ "success" ] :
            self.steps_[ stepname ].log_push()
            self.steps_[ stepname ].reportErrs( stepResult[ "success" ], stepResult[ "line" ] )
            self.steps_[ stepname ].log_pop()
      self.log( "{fail} : Steps [ {steps} ] failed".format(
                                                            fail=SubmitAction.FAILURE_STR,
                                                            steps=", ".join( [ key for key in stepsLog.keys() if not stepsLog[key]["success"] ] ) 
                                                            )
              )
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

    # Maybe use one day for complex branch analysis...
    # deps     = { depType : {} for depType in Step.DependencyType }

    # # Get all variations of dependencies
    # for step in self.steps_ :
    #   for stepname, depType in step.dependencies_ :
    #     deps[ depType ][ stepname ] = None

    maxResources = HpcArgpacks( OrderedDict() )
    maxTimelimit = timedelta()
    maxResources.setName( HpcArgpacks.HPC_JOIN_NAME + "max" )
    hpcSubmit = [ step.submitOptions_.submitType_ for step in self.steps_.values() if step.submitOptions_.submitType_ != SubmissionType.LOCAL ]
    if not hpcSubmit :
      self.log( "No HPC steps in this test" )
      return maxResources, maxTimelimit

    longestStep = len( max( [ stepname for stepname in self.steps_.keys() ], key=len ) )
    phase = 0
    self.log_push()

    # We need to break it down by expected runtime of each test by size of pool
    # as that is the order they will run in. Could we optimize? Yea probably. Will we? Not right now
    self.log( "Calculating expected runtime of steps across {0} thread workers [threadpool size]".format( self.globalOpts_.threadpool ) )
    self.log_push()
    # Gather set of runnable psuedojobs
    psuedoJobs = [ step for step in self.steps_.values() if step.runnable() ]
    # Assume all runnable are in queue to be run, and thus cannot be re-submitted
    for pj in psuedoJobs :
      pj.submitted_ = True

    psuedoRunningMap = {}
    # Continue while we have jobs in queue or running
    while len( psuedoJobs ) > 0 or len( psuedoRunningMap ) > 0 :
      # If we have slots in our pool and jobs left, fill in
      while len( psuedoRunningMap ) < self.globalOpts_.threadpool and len( psuedoJobs ) > 0 :
        pjStep = psuedoJobs.pop(0)
        psuedoRunningMap[ pjStep.name_ ] = { "step" : pjStep, "timelimit" : SubmitOptions.parseTimelimit( pjStep.submitOptions_.timelimit_, hpcSubmit[0] ) }

      # Find smallest job
      runForKey = min( psuedoRunningMap, key= lambda k : psuedoRunningMap[k]["timelimit"] )
      runFor    = copy.deepcopy( psuedoRunningMap[runForKey]["timelimit"] )
      maxTimelimit += runFor
      # "Run" for that amount of time
      self.log( "Simulating threadpool for {0}".format( psuedoRunningMap[runForKey]["timelimit"] ) )
      self.log_push()

      for key in psuedoRunningMap.keys() :
        psuedoRunningMap[ key ][ "timelimit" ] -= runFor
      
      ##################################################################################################################
      # RESOURCE CALCULATIONS
      # What would our max resource consumption be whilst running this set?
      # Add all concurrent resources together
      self.log( "Calculate max instantaneous resources for this phase" )
      self.log_push()
      currentResources = HpcArgpacks.joinAll( [ 
                                                pj[ "step" ].submitOptions_.hpcArguments_.selectAncestrySpecificSubmitArgpacks( print=pj["step"].log )
                                                  for pj in psuedoRunningMap.values() 
                                              ],
                                              hpcSubmit[0],
                                              lambda rhs,lhs : rhs + lhs,
                                              print=self.log
                                            )

      # Get maximum
      maxResources.join(
                        currentResources,
                        hpcSubmit[0],
                        max,
                        print=self.log
                        )
      self.log_pop()
      self.log( "[PHASE {phase}] Resources for [ {steps} ] : '{res}', timelimit = {time}".format(
                                                                                                  phase=phase,
                                                                                                  steps=" ".join(
                                                                                                                "{0:>{1}}".format(
                                                                                                                                  step, longestStep + ( 1 if len( psuedoRunningMap ) > 1 else 0 ) )
                                                                                                                                  for step in psuedoRunningMap.keys()
                                                                                                                ),
                                                                                                  res=currentResources.format( hpcSubmit[0], print=lambda *args : None ),
                                                                                                  time=runFor
                                                                                                  )
                )
      phase += 1
      #
      ##################################################################################################################

      
      # Re-evaluate for any jobs that completed
      completed = []
      for stepname in psuedoRunningMap :
        if psuedoRunningMap[ stepname ][ "timelimit" ].total_seconds() <= 0 :
          completed.append( stepname )
          psuedoRunningMap[ stepname ][ "step" ].jobid_     = 0
          psuedoRunningMap[ stepname ][ "step" ].retval_    = 0
          psuedoRunningMap[ stepname ][ "step" ].notifyChildren( )

      # Remove completed
      for pj in completed :
        psuedoRunningMap.pop( pj )

      # Add any new arrivals to the queue
      for step in self.steps_.values() :
        if step.runnable() :
          # as soon as it is in queue, consider it submitted
          psuedoJobs.append( step )
          step.submitted_ = True

      self.log( "{0} jobs completed during this runtime".format( len( completed ) ) )
      self.log_pop()


    
    self.log_pop()
    self.log( "All jobs simulated, stopping" )
    self.log_pop()


    # Reset the pipeline
    for step in self.steps_.values() :
      step.resetRunnable()
    self.log( "Maximum HPC resources required will be '{0}' with timelimit '{1}'".format(
                                                                                          maxResources.format( hpcSubmit[0], print=lambda *args : None ),
                                                                                          SubmitOptions.formatTimelimit(
                                                                                            maxTimelimit,
                                                                                            hpcSubmit[0]
                                                                                          )
                                                                                        )
              )
    return maxResources, maxTimelimit





