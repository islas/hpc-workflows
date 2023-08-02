import os

from SubmitAction  import SubmitAction
from SubmitOptions import SubmitOptions
from Step          import Step


class Test( SubmitAction ):
  
  def __init__( self, name, options, defaultSubmitOptions = SubmitOptions(), parent = "", rootDir = "./" ) :
    self.steps_         = {}
    super().__init__( name, options, defaultSubmitOptions, parent, rootDir )

  def parseSpecificOptions( self ) :

    key = "steps"
    if key in self.options_ :
      for stepname, stepDict in self.options_[ key ].items() :
        self.steps_[ stepname ] = Step( stepname, stepDict, self.submitOptions_, parent=self.name_, rootDir=self.rootDir_ )
    
    # Now that steps are fully parsed, attempt to organize dependencies
    Step.sortDependencies( self.steps_ )


  def executeAction( self ) :
    steps = []
    while len( steps ) != len( self.steps_ ) :
      for step in self.steps_.values() :

        if step.runnable() :
          step.run()
          steps.append( step.name_ )
      print( "Checking remaining jobs..." )

    print( "No remaining steps, test submission complete" )