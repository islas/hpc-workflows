import os
import io
import copy
from SubmitOptions import SubmitOptions

LABEL_LENGTH = 12

class SubmitAction() :
  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :

    self.name_          = name
    self.globalOpts_    = globalOpts # options passed in at CLI
    self.label_            = "{0:<{1}}".format( "[{0}] ".format( self.name_ ), so.LABEL_LENGTH )
    self.labelIndentation_ = "  "
    self.labelLevel_       = 0
    self.log( "Initializing" )
    self.log_push()

    self.parent_        = parent
    self.options_       = options
    self.submitOptions_ = copy.deepcopy( defaultSubmitOptions ).selectHostSpecificSubmitOptions()

    self.rootDir_          = rootDir
    self.printDir_         = False

    self.parse()
    self.log_pop()

  def log( self, *args, **kwargs ) :
    # https://stackoverflow.com/a/39823534
    output=io.StringIO()
    print( *args, file=output, end="", **kwargs )
    contents = output.getvalue()
    output.close()
    print( self.label_ + self.labelIndentation_ * self.labelLevel_ + contents, flush=True )
  
  def log_push( self ) :
    self.labelLevel_ += 1
  def log_pop( self ) :
    self.labelLevel_ -= 1

  def parseSpecificOptions( self ) :
    # Children should override this for their respective parse()
    pass

  def parse( self ) :
    key = "submit_options"
    if key in self.options_ :
      self.submitOptions_.update( SubmitOptions( self.options_[ key ] ).selectHostSpecificSubmitOptions() )

    # Now call child parse
    self.parseSpecificOptions()

  def setWorkingDirectory( self ) :
    self.log( "Preparing working directory" )
    self.log_push()

    # Set directory
    self.log( "Running from root directory {0}".format( self.rootDir_ ) )

    os.chdir( self.rootDir_ )
    if self.submitOptions_.workingDirectory_ is not None :
      if self.printDir_ :
        self.log( "Setting working directory to {0}".format( self.submitOptions_.workingDirectory_ ) )
      os.chdir( self.submitOptions_.workingDirectory_ )
    
    if self.printDir_ :
      self.log( "Current directory : {0}".format( os.getcwd() ) )

    self.log_pop()

  def run( self ) :
    self.setWorkingDirectory()
    self.executeAction()
