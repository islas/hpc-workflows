import copy

from enum import Enum

class SubmitOptions( ) :
  class SubmissionType( Enum ):
    PBS   = "PBS"
    SLURM = "SLURM"
    LOCAL = "LOCAL"

    def __str__( self ) :
      return self.value

  def __init__( self, optDict={} ) :
    self.submit_            = optDict
    self.workingDirectory_  = None
    self.queue_             = None
    self.resources_         = None
    self.timelimit_         = None
    
    # Should be set at test level 
    self.submitType_        = None
    self.debug_             = None
    self.account_           = None

    # Should be set via the step
    self.name_             = None
    self.dependencies_     = None

    self.parse()

  def parse( self ):
    key = "working_directory"
    if key in self.submit_ :
      self.workingDirectory_ = self.submit_[ key ]
    
    key = "queue"
    if key in self.submit_ :
      self.queue_ = self.submit_[ key ]
    
    key = "resources"
    if key in self.submit_ :
      self.resources_ = self.submit_[ key ]
    
    key = "timelimit"
    if key in self.submit_ :
      self.timelimit_ = self.submit_[ key ]

  # Updates and overrides current with values from rhs if they exist
  def update( self, rhs ) :
    if rhs.workingDirectory_  is not None : self.workingDirectory_ = rhs.workingDirectory_
    if rhs.queue_             is not None : self.queue_             = rhs.queue_
    if rhs.resources_         is not None : self.resources_         = rhs.resources_
    if rhs.timelimit_         is not None : self.timelimit_         = rhs.timelimit_
    
    # Should be set at test level 
    if rhs.submitType_        is not None : self.submitType_        = rhs.submitType_
    if rhs.debug_             is not None : self.debug_             = rhs.debug_
    if rhs.account_           is not None : self.account_           = rhs.account_

    # Should be set via the step
    if rhs.name_              is not None : self.name_             = rhs.name_
    if rhs.dependencies_      is not None : self.dependencies_     = rhs.dependencies_

    # This keeps things consistent but should not affect anything
    self.submit_.update( rhs.submit_ )
    self.parse()
  
  # Check non-optional fields
  def validate( self ) :
    return (
            self.submitType_ is not None and
            self.queue_      is not None and
            self.resources_  is not None and
            self.name_       is not None
            )

  def format( self ) :
    # Why this can't be with the enum
    # https://stackoverflow.com/a/45716067
    # Why this can't be a dict value of the enum
    # https://github.com/python/cpython/issues/88508
    submitDict = {}
    if self.submitType_ == self.SubmissionType.PBS :
      submitDict    = { "submit" : "qsub",   "resources"  : "-l select={0}",
                        "name"   : "-N {0}", "dependency" : "-W depend={0}",
                        "queue"  : "-q {0}", "account"    : "-A {0}",
                        "output" : "-j oe -o {0}.log",
                        "time"   : "-l walltime={0}" }
    elif self.submitType_ == self.SubmissionType.SLURM :
      submitDict    = { "submit" : "sbtach", "resources"  : "--gres={0}",
                        "name"   : "-J {0}", "dependency" : "-d {0}",
                        "queue"  : "-p {0}", "account"    : "-A {0}",
                        "output" : "-j -o {0}",
                        "time"   : "-t {0}" }
    elif self.submitType_ == self.SubmissionType.LOCAL :
      submitDict    = { "submit" : "",       "resources"  : "",
                        "name"   : "",       "dependency" : "",
                        "queue"  : "",       "account"    : "",
                        "output" : "-o {0}.log",
                        "time"   : "" }


    if self.submitType_ == self.SubmissionType.LOCAL :
      return []
    else :
      cmd = [ submitDict[ "submit" ] ]

      # Set through config
      if self.resources_ is not None :
        cmd.extend( submitDict[ "resources" ].format( self.resources_ ).split( " " ) )

      if self.queue_ is not None :
        cmd.extend( submitDict[ "queue" ].format( self.queue_ ).split( " " ) )

      if self.timelimit_ is not None :
        cmd.extend( submitDict[ "time" ].format( self.timelimit_ ).split( " " ) )

      # Set via test runner secrets
      if self.account_ is not None :
        cmd.extend( submitDict[ "account" ].format( self.account_ ).split( " " ) )

      # Set via step
      if self.name_ is not None :
        cmd.extend( submitDict[ "name"   ].format( self.name_ ).split( " " ) )
        cmd.extend( submitDict[ "output" ].format( self.name_ ).split( " " ) )


      if self.dependencies_ is not None :
        cmd.extend( submitDict[ "dependency" ].format( self.dependencies_ ).split( " " ) )

      if self.submitType_ == self.SubmissionType.PBS :
        # Extra bit to delineate command + args
        cmd.append( "--" )

      return cmd
  
  def __str__( self ) :
    output = {
              "working_directory" : self.workingDirectory_,
              "queue"             : self.queue_,
              "resources"         : self.resources_,
              "timelimit"         : self.timelimit_,
              "submitType"        : self.submitType_,
              "debug"             : self.debug_,
              "account"           : self.account_,
              "name"              : self.name_,
              "dependencies"      : self.dependencies_,
              "original"          : self.submit_ }
    return str( output )



