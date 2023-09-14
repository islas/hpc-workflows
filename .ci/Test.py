import os
import sys

from SubmitAction  import SubmitAction
from SubmitOptions import SubmitOptions
from Step          import Step


class Test( SubmitAction ):
  
  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.steps_         = {}
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
    self.setupResultsStep()

    steps = []
    while len( steps ) != len( self.steps_ ) :
      for step in self.steps_.values() :

        if step.runnable() :
          step.run()
          steps.append( step.name_ )
      self.log( "Checking remaining steps..." )

    self.log( "No remaining steps, test submission complete" )

    self.postProcessResults( steps )

  def setupResultsStep( self ) :
    # Do we need to add a results step?
    if self.globalOpts_.nowait :
      self.log( "No waiting for HPC submissions requested, skipping results sync" )
      return
    
    self.log( "Checking if results sync step required" )
    self.log_push()
    # Get all current steps submission type
    subs = [ step.submitOptions_.submitType_ for step in self.steps_.values() if step.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL ]
    
    if len( subs ) > 1 :
      PBS_MIN_RES   = "1:ncpus=1"
      SLURM_MIN_RES = "cpu:1"
      res = None
      submitType = None
      if SubmitOptions.SubmissionType.PBS in subs :
        res = PBS_MIN_RES
        submitType = SubmitOptions.SubmissionType.PBS
      else : # SLURM
        res = SLURM_MIN_RES
        submitType = SubmitOptions.SubmissionType.SLURM
      
      
      if res is not None :
        self.log( "Final results job being created to wait for all jobs complete" )
        
        deps = { stepname : "afterany" for stepname in self.steps_.keys() }
        resultsDict = {
                        "submit_options" :
                        {
                          "resources" : res,
                          "wait"      : True,
                          "submission": submitType
                        },
                        "command" : os.path.dirname( os.path.abspath( sys.argv[0] ) ) + "/" + "results.sh",
                        "dependencies" : deps
                      }

        # Quickly add this step
        self.steps_[ "results" ] = Step(
                                        'results',
                                        resultsDict,
                                        self.submitOptions_,
                                        self.globalOpts_,
                                        parent=self.ancestry(),
                                        rootDir=self.rootDir_
                                        )
        self.log( "Rescanning dependencies under test {0}...".format( self.name_ ) )
        Step.sortDependencies( self.steps_ )
        self.log( "Step results dependencies : {0}".format( self.steps_[ "results" ].dependencies_ ) )

    elif len( subs ) == 1 :
      self.log( "Only one HPC submission exists, setting that job to wait" )
      for stepname, step in self.steps_.items() :
        if step.submitOptions_.submitType_ != SubmitOptions.SubmissionType.LOCAL :
          step.submitOptions_.wait_ = True
          self.log( "Forcing {step} to wait for job completion".format( step=stepname ) )
    else :
      self.log( "No HPC submissions, no results job added" )

    self.log_pop()

  def postProcessResults( self, stepOrder ) :
    # Do we need to post-process HPC submission files
    if not self.globalOpts_.nopost :
      if self.globalOpts_.nowait :
        self.log( "Post-processing requires waiting for HPC submissions, skipped" )
      else :
        # Get all current steps submission type
        subs = [ step.submitOptions_.submitType_ for step in self.steps_.values() ]

        if not ( SubmitOptions.SubmissionType.PBS in subs or SubmitOptions.SubmissionType.SLURM in subs ) :
          self.log( "No HPC submissions, no results to post-process" )
          return
        else :
          # We go through the steps in the order submitted
          self.log( "Outputting results..." )
          self.log_push()

          for stepname in stepOrder :
            if stepname != "results" and self.steps_[ stepname ].submitOptions_ != SubmitOptions.SubmissionType.LOCAL :
              self.steps_[ stepname ].postProcessResults()
          
          self.log_pop()

