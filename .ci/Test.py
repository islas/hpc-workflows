from Step          import Step
from SubmitOptions import SubmitOptions

class Test():
  
  def __init__( self, name, testDict ) :
    self.name_      = name
    self.test_      = testDict

    self.steps_         = {}
    self.submitOptions_ = None
    
    self.parse()

  def parse( self ) :
    key = "submit_options"
    if key in self.test_ :
      self.submitOptions_ = SubmitOptions( self.test_[ key ] )
    # We don't need to validate submission options yet
    
    key = "steps"
    if key in self.test_ :
      for stepname, stepDict in self.test_[ key ].items() :
        self.steps_[ stepname ] = Step( stepname, stepDict, self.submitOptions_ )
    
    # Now that steps are fully parsed, attempt to organize dependencies
    Step.sortDependencies( self.steps_ )

  def run( self ) :

    steps = []
    # print( len( steps )  )
    # print( len( self.steps_ ) )
    while len( steps ) != len( self.steps_ ) :
      for step in self.steps_.values() :
        if step.runnable() :
          step.run()
          steps.append( step.name_ )
      print( "Checking remaining jobs..." )

    print( "No remaining steps, test submission complete" )