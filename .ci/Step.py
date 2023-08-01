from enum import Enum

import SubmitOptions

class Step():

  class DEP_TYPE( str, Enum ):
    AFTER      = "after"
    AFTEROK    = "afterok"
    AFTERNOTOK = "afternotok"
    AFTERANY   = "afterany"
    # def __str__( self ) :
    #   return str( self.value )
    # @staticmethod
    # def fromString( s ) :
    #   return DEP_TYPE[ s ]
  
  def __init__( self, name, stepDict, defaultSubmitOptions = None ) :
    self.name_      = name
    self.step_      = stepDict
    self.submitted_ = False
    self.script_        = None
    self.arguments_     = None
    self.dependencies_  = {} # our steps we are dependent on and their type
    self.depSignOff_    = {} # steps we are dependent on will need to tell us when to go
    self.children_      = [] # steps that are dependent on us that we will need to sign off for
    self.submitOptions_ = defaultSubmitOptions if not None else {}
    
    self.parse()

  def parse( self ) :
    key = "submit_options"
    if key in self.step_ :
      self.submitOptions_.update( self.step_[ key ] )

    self.submitOptions_.validate()
    
    key = "script"
    if key in self.step_ :
      self.script_ = self.step_[ key ]

    key = "arguments"
    if key in self.step_ :
      self.arguments_ = self.step_[ key ]

    key = "dependencies"
    if key in self.step_ :
      for depStep, depType in self.step_[ key ].items() :
        self.dependencies_[ depStep ] = Step.DEP_TYPE( depType )
  
  def runnable( self ) :
    canRun = False
    # If no depenedencies just run
    if not self.submitted_ :
      if not self.depSignOff_ :
        canRun = True
      else:
        allDepsJobID = True
        for jobid in self.depSignOff_.values() :
          allDepsJobID = ( jobid != -1 ) and allDepsJobID
        
        canRun = allDepsJobID
    
    return canRun
  
  def run( self ) :
    # Do submission logic....
    print( "Submitting step {0}...".format( self.name_ ) )
    self.submitted_ = True

    # if submitted properly
    if True and self.children_ :
      print( "Notifying children..." )
      # Go to all children and mark ok
      for child in self.children_ :
        child.depSignOff_[ self.name_ ] = 0

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
            


