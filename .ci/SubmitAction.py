import os
import io
import copy
from SubmitOptions import SubmitOptions

class SubmitAction() :
  def __init__( self, name, options, defaultSubmitOptions = SubmitOptions(), parent = "", rootDir = "./" ) :
    self.name_          = name
    self.parent_        = parent
    self.options_       = options
    self.submitOptions_ = copy.deepcopy( defaultSubmitOptions )

    self.rootDir_       = rootDir
    self.printDir_      = False
    self.label_         = "{0:<{1}}".format( "[{0}] ".format( self.name_ ), 12 )

    self.parse()

  def log( self, *args, **kwargs ) :
    # https://stackoverflow.com/a/39823534
    output=io.StringIO()
    print( *args, file=output, end="", **kwargs )
    contents = output.getvalue()
    output.close()
    print( self.label_ + contents )

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
    self.log( "Preparing to run from {0}".format( self.rootDir_ ) )

    os.chdir( self.rootDir_ )
    if self.printDir_ :
      self.log( "Current directory : {0}".format( os.getcwd() ) )

    if self.submitOptions_.workingDirectory_ is not None :
      if self.printDir_ :
        self.log( "Setting working directory to {0}".format( self.submitOptions_.workingDirectory_ ) )
      os.chdir( self.submitOptions_.workingDirectory_ )

  def run( self ) :
    self.setWorkingDirectory()
    self.executeAction()
