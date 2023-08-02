import os
from SubmitOptions import SubmitOptions

class SubmitAction() :
  def __init__( self, name, options, defaultSubmitOptions = SubmitOptions(), parent = "", rootDir = "./" ) :
    self.name_          = name
    self.parent_        = parent
    self.options_       = options
    self.submitOptions_ = defaultSubmitOptions
    self.rootDir_       = rootDir
    self.printDir_      = False

    self.parse()


  def parseSpecificOptions( self ) :
    # Children should override this for their respective parse()
    pass

  def parse( self ) :
    key = "submit_options"
    if key in self.options_ :
      self.submitOptions_.update( SubmitOptions( self.options_[ key ] ) )
    
    # Now call child parse
    self.parseSpecificOptions()

  def setWorkingDirectory( self ) :
    # Set directory
    os.chdir( self.rootDir_ )
    if self.submitOptions_.workingDirectory_ is not None :
      if self.printDir_ :
        print( "Current directory : {0}".format( os.getcwd() ) )
        print( "Setting working directory to {0}".format( self.submitOptions_.workingDirectory_ ) )
      os.chdir( self.submitOptions_.workingDirectory_ )

  def run( self ) :
    self.setWorkingDirectory()
    self.executeAction()
