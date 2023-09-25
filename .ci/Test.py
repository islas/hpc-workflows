import os
import sys
import json
import time

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
    self.masterlog_     = None
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

    # Master logfile
    self.masterlog_ = os.path.abspath( "{0}/{1}".format( self.rootDir_, self.ancestry() + ".log" ) )


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

    self.postProcessResults( steps )

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

        # We go through the steps in the order submitted
        self.log( "Outputting results..." )
        self.log_push()

        errLogs = {}
        msgs    = []
        for stepname in stepOrder :
          if stepname != "results" and self.steps_[ stepname ].submitOptions_ != SubmitOptions.SubmissionType.LOCAL :
            success, err = self.steps_[ stepname ].postProcessResults()
            if not success :
              errs = True
              errLogs[ stepname ] = {}
              errLogs[ stepname ][ "logfile" ] = self.steps_[ stepname ].logfile_
              msgs.append( err )
        
        if errs :
          self.log( "Steps [ {steps} ] failed".format( steps=", ".join( errLogs.keys() ) ) )
          self.log( "Writing relevant logfiles to view in master log file : " )
          self.log( self.masterlog_ )

          with open( self.masterlog_, "w" ) as f :
            json.dump( errLogs, f )
          
          if not self.globalOpts_.nofatal :
            raise Exception( "\n".join( msgs ) )
        self.log_pop()
        if not errs :
          # We got here without errors
          self.log( "[SUCCESS] : Test {0} completed successfully".format( self.name_ ) )

