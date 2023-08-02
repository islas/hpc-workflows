from enum import Enum

class SubmitOptions( ) :
  class SubmissionType( dict , Enum ):
    PBS   = { "submit" : "qsub",   "resources"  : "-l select={0}",
              "name"   : "-N {0}", "dependency" : "-W depend={0}",
              "queue"  : "-q {0}", "account"    : "-A {0}",
              "output" : "-j oe -o {0}.log",
              "time"   : "-l walltime={0}" }
    SLURM = { "submit" : "sbtach", "resources"  : "--gres={0}",
              "name"   : "-J {0}", "dependency" : "-d {0}",
              "queue"  : "-p {0}", "account"    : "-A {0}",
              "output" : "-j -o {0}",
              "time"   : "-t {0}" }
    LOCAL = { "submit" : "",       "resources"  : "",
              "name"   : "",       "dependency" : "",
              "queue"  : "",       "account"    : "",
              "output" : "-o {0}.log",
              "time"   : "" }

    def format( self, subOpts ) :
      if self == self.LOCAL :
        return []
      else :
        cmd = [ self[ "submit" ] ]

        # Set through config
        if subOpts.resources_ is not None :
          cmd.extend( self[ "resources" ].format( subOpts.resources_ ).split( " " ) )

        if subOpts.queue_ is not None :
          cmd.extend( self[ "queue" ].format( subOpts.queue_ ).split( " " ) )

        if subOpts.timelimit_ is not None :
          cmd.extend( self[ "time" ].format( subOpts.timelimit_ ).split( " " ) )

        # Set via test runner secrets
        if subOpts.account_ is not None :
          cmd.extend( self[ "account" ].format( subOpts.account_ ).split( " " ) )

        # Set via step
        if subOpts.name_ is not None :
          cmd.extend( self[ "name"   ].format( subOpts.name_ ).split( " " ) )
          cmd.extend( self[ "output" ].format( subOpts.name_ ).split( " " ) )


        if subOpts.dependencies_ is not None :
          cmd.extend( self[ "dependency" ].format( subOpts.dependencies_ ).split( " " ) )

        if self == self.PBS :
          # Extra bit to delineate command + args
          cmd.append( "--" )

        return cmd

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
    return self.submitType_.format( self )
  
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
              "dependencies"      : self.dependencies_ }
    return str( output )



