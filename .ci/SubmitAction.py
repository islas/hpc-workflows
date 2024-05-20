import os
import io
import copy
from SubmitOptions import SubmitOptions
import SubmitOptions as so

class SubmitAction( ) :
  SUCCESS_STR = "[SUCCESS]"
  FAILURE_STR = "[FAILURE]"

  def scope( self ) :
    return "none"

  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :

    self.name_          = name
    self.globalOpts_    = globalOpts # options passed in at CLI
    # Add 8 for [item::] characters
    self.label_            = "{0:<{1}}".format( "[{0}::{1}] ".format( self.scope(), self.name_ ), so.LABEL_LENGTH + 8 )
    self.labelIndentation_ = "  "
    self.labelLevel_       = 0
    self.logfile_        = None

    self.parent_        = parent
    self.options_       = options
    self.submitOptions_ = copy.deepcopy( defaultSubmitOptions )

    self.rootDir_          = rootDir
    self.printDir_         = False

    self.parse()
  
  def ancestry( self ) :
    if self.parent_ :
      return "{0}.{1}".format( self.parent_, self.name_ )
    else :
      return self.name_

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
      self.submitOptions_.update( SubmitOptions( self.options_[ key ], origin=self.ancestry() ), print=self.log )

    # Now call child parse
    self.parseSpecificOptions()

    # Now generate masterlog name
    self.logfile_ = os.path.abspath( "{0}/{1}".format( self.rootDir_, self.ancestry() + ".log" ) )

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
  
  def prepExecuteAction( self ) :
    pass

  def run( self ) :
    self.prepExecuteAction()
    self.setWorkingDirectory()
    return self.executeAction()
  
  @staticmethod
  def getLastLine( filename ) :
    lastline = None
    with open( filename, "rb" ) as f :
      # https://stackoverflow.com/a/54278929
      try:  # catch OSError in case of a one line file 
        f.seek( -2, os.SEEK_END )
        while f.read(1) != b'\n' :
          f.seek( -2, os.SEEK_CUR )
      except OSError:
          f.seek(0)
      lastline = f.readline().decode()

    return lastline.rstrip()
