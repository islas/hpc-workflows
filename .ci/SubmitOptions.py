import copy
import socket
import re

from enum import Enum

# https://stackoverflow.com/a/3233356
import collections.abc

LABEL_LENGTH = 12

# Update mapping dest with source
def recursiveUpdate( dest, source ):
  for k, v in source.items():
    if isinstance( v, collections.abc.Mapping ):
      dest[k] = recursiveUpdate( dest.get( k, {} ), v )
    else:
      dest[k] = v
  return dest

class SubmitOptions( ) :
  class SubmissionType( Enum ):
    PBS   = "PBS"
    SLURM = "SLURM"
    LOCAL = "LOCAL"

    def __str__( self ) :
      return self.value
  
  ARGUMENTS_ORIGIN_KEY = "arguments_origin"

  def __init__( self, optDict={}, isHostSpecific=False, lockSubmitType=False, origin=None ) :
    self.submit_            = optDict
    self.workingDirectory_  = None
    self.queue_             = None
    self.resources_         = None
    self.timelimit_         = None
    self.wait_              = None
    
    # Should be set at test level 
    self.debug_             = None
    self.account_           = None

    # Can be set on a per-action basis, but can also be overridden if cmdline opt
    self.submitType_        = None
    self.lockSubmitType_    = lockSubmitType

    # Should be set via the step
    self.name_             = None
    self.dependencies_     = None

    # Should normally be restricted to host-specific options
    self.arguments_        = {}

    # Allow host-specific submit options
    self.isHostSpecific_      = isHostSpecific
    self.hostSpecificOptions_ = {}
    self.parse( origin=origin )

  def parse( self, log=False, origin=None ):
    submitKeys = []

    key = "working_directory"
    submitKeys.append( key )
    if key in self.submit_ :
      self.workingDirectory_ = self.submit_[ key ]
    
    key = "queue"
    submitKeys.append( key )
    if key in self.submit_ :
      self.queue_ = self.submit_[ key ]
    
    key = "resources"
    submitKeys.append( key )
    if key in self.submit_ :
      self.resources_ = self.submit_[ key ]
    
    key = "timelimit"
    submitKeys.append( key )
    if key in self.submit_ :
      self.timelimit_ = self.submit_[ key ]
    
    key = "wait"
    submitKeys.append( key )
    if key in self.submit_ :
      self.wait_ = self.submit_[ key ]
    
    key = "arguments"
    submitKeys.append( key )
    if key in self.submit_ :
      self.arguments_ = self.submit_[ key ]
      if origin is not None :
        self.arguments_[ SubmitOptions.ARGUMENTS_ORIGIN_KEY ] = { argKey : origin for argKey in self.arguments_.keys() }
    
    # Allow parsing of per-action submission
    key = "submission"
    submitKeys.append( key )
    if key in self.submit_ :
      if not self.lockSubmitType_ :
        self.submitType_ = SubmitOptions.SubmissionType( self.submit_[ key ] )


    # Process all other keys as host-specific options
    for key, value in self.submit_.items() :
      if key not in submitKeys :
        if not self.isHostSpecific_ :
          # ok to parse
          self.hostSpecificOptions_[ key ] = SubmitOptions( value, isHostSpecific=True )
          self.hostSpecificOptions_[ key ].parse( origin=origin )
        else :
          print( "Warning: Host-specific options cannot have sub-host-specific options" )


  # Updates and overrides current with values from rhs if they exist
  def update( self, rhs, print=print ) :
    if rhs.workingDirectory_    is not None : self.workingDirectory_ = rhs.workingDirectory_
    if rhs.queue_               is not None : self.queue_             = rhs.queue_
    if rhs.resources_           is not None : self.resources_         = rhs.resources_
    if rhs.timelimit_           is not None : self.timelimit_         = rhs.timelimit_
    if rhs.wait_                is not None : self.wait_              = rhs.wait_
    
    # Should be set at test level 
    # Never do this so children cannot override parent
    # self.lockSubmitType_ = rhs.lockSubmitType_
    if not self.lockSubmitType_ :
      if rhs.submitType_          is not None : self.submitType_        = rhs.submitType_

    if rhs.debug_               is not None : self.debug_             = rhs.debug_
    if rhs.account_             is not None : self.account_           = rhs.account_

    # Should be set via the step
    if rhs.name_                is not None : self.name_             = rhs.name_
    if rhs.dependencies_        is not None : self.dependencies_     = rhs.dependencies_

    # These are both dictionaries
    if rhs.arguments_                       : recursiveUpdate( self.arguments_, rhs.arguments_ )
    if rhs.hostSpecificOptions_             : recursiveUpdate( self.hostSpecificOptions_, rhs.hostSpecificOptions_ )

    # This keeps things consistent but should not affect anything
    recursiveUpdate( self.submit_, rhs.submit_ )
    self.parse( log=True )
  
  # Check non-optional fields
  def validate( self ) :
    err          = None
    errMsgFormat = "Missing {opt}"

    if self.submitType_ is None :
      err   = "submission type"
    elif self.name_     is None :
      err = "submission job name"
    elif self.submitType_ is not self.SubmissionType.LOCAL :
      if self.account_ is None :
        err = "account"
      elif self.queue_ is None :
        err = "queue"
      elif self.resources_ is None :
        err = "resource list"
      
      if err is not None :
        err += " on non-LOCAL submission"

    errMsg = "okay"
    if err is not None :
      errMsg = errMsgFormat.format( opt=err )
    return err is None, errMsg

  def selectHostSpecificSubmitOptions( self ) :
    # Must be valid for this specific host or generically
    fqdn = socket.getfqdn()

    # Have to do string matching rather than in dict
    hostSpecificOptKey = next( ( hostOpt for hostOpt in self.hostSpecificOptions_ if hostOpt in fqdn ), None )

    # Quickly generate a stand-in SubmitOptions in spitting image
    currentSubmitOptions = copy.deepcopy( self )

    if hostSpecificOptKey is not None :
      # Update with host-specifics
      currentSubmitOptions.update( self.hostSpecificOptions_[ hostSpecificOptKey ] )

    return currentSubmitOptions
  
  def getOutputFilename( self ) :
    return "{0}.log".format( self.name_ )

  def format( self, print=print ) :
    # Why this can't be with the enum
    # https://stackoverflow.com/a/45716067
    # Why this can't be a dict value of the enum
    # https://github.com/python/cpython/issues/88508
    submitDict = {}
    if self.submitType_ == self.SubmissionType.PBS :
      submitDict    = { "submit" : "qsub",   "resources"  : "-l select={0}",
                        "name"   : "-N {0}", "dependency" : "-W depend={0}",
                        "queue"  : "-q {0}", "account"    : "-A {0}",
                        "output" : "-j oe -o {0}",
                        "time"   : "-l walltime={0}",
                        "wait"   : "-W block=true" }
    elif self.submitType_ == self.SubmissionType.SLURM :
      submitDict    = { "submit" : "sbtach", "resources"  : "--gres={0}",
                        "name"   : "-J {0}", "dependency" : "-d {0}",
                        "queue"  : "-p {0}", "account"    : "-A {0}",
                        "output" : "-j -o {0}",
                        "time"   : "-t {0}",
                        "wait"   : "-W" }
    elif self.submitType_ == self.SubmissionType.LOCAL :
      submitDict    = { "submit" : "",       "resources"  : "",
                        "name"   : "",       "dependency" : "",
                        "queue"  : "",       "account"    : "",
                        "output" : "-o {0}",
                        "time"   : "",
                        "wait"   : "" }

    additionalArgs = []
    
    if self.arguments_ :
      # Find all argument packs that match our ancestry
      argpacksToUse = []
      for argpack in self.arguments_.keys() :
        if "::" in argpack :
          # print( "Checking scope-specific argument pack {0}".format( argpack ) )
          # Take everything before :: and treat it as a regex to match ancestry
          scopeRegex = argpack.split( "::" )[0]
          if re.match( scopeRegex, self.name_ ) is not None :
            argpacksToUse.append( ( argpack, argpack.split( "::" )[1] ) )
        else :
          # Generic pack, send it off!
          argpacksToUse.append( ( argpack, argpack ) )


      # Format them and pass them out in alphabetical order based on name, NOT REGEX
      longestPack = len( max( [ key[0] for key in argpacksToUse if key != SubmitOptions.ARGUMENTS_ORIGIN_KEY ], key=len ) )
      for key, sortname in sorted( argpacksToUse, key=lambda pack : pack[1] ) :
        if key != SubmitOptions.ARGUMENTS_ORIGIN_KEY :
          print( 
                "From {origin:<{length}} adding arguments pack {key:<{packlength}} : {val}".format(
                                                                                        origin=self.arguments_[SubmitOptions.ARGUMENTS_ORIGIN_KEY][key],
                                                                                        length=LABEL_LENGTH,
                                                                                        packlength=longestPack + 2,
                                                                                        key="'{0}'".format( key ),
                                                                                        val=self.arguments_[key]
                                                                                        )
                )
          additionalArgs.extend( self.arguments_[key] )

    if self.submitType_ == self.SubmissionType.LOCAL :
      return [], additionalArgs
    else :
      cmd = [ submitDict[ "submit" ] ]

      # Set through config
      if self.resources_ is not None :
        cmd.extend( submitDict[ "resources" ].format( self.resources_ ).split( " " ) )

      if self.queue_ is not None :
        cmd.extend( submitDict[ "queue" ].format( self.queue_ ).split( " " ) )

      if self.timelimit_ is not None :
        cmd.extend( submitDict[ "time" ].format( self.timelimit_ ).split( " " ) )
      
      if self.wait_ is not None :
        cmd.extend( submitDict[ "wait" ].format( self.wait_ ).split( " " ) )

      # Set via test runner secrets
      if self.account_ is not None :
        cmd.extend( submitDict[ "account" ].format( self.account_ ).split( " " ) )

      # Set via step
      if self.name_ is not None :
        cmd.extend( submitDict[ "name"   ].format( self.name_ ).split( " " ) )
        cmd.extend( submitDict[ "output" ].format( self.getOutputFilename() ).split( " " ) )


      if self.dependencies_ is not None :
        cmd.extend( submitDict[ "dependency" ].format( self.dependencies_ ).split( " " ) )

      if self.submitType_ == self.SubmissionType.PBS :
        # Extra bit to delineate command + args
        cmd.append( "--" )

      return cmd, additionalArgs

  def __str__( self ) :
    output = {
              "working_directory" : self.workingDirectory_,
              "queue"             : self.queue_,
              "resources"         : self.resources_,
              "timelimit"         : self.timelimit_,
              "wait"              : self.wait_,
              "submitType"        : self.submitType_,
              "lockSubmitType"    : self.lockSubmitType_,
              "debug"             : self.debug_,
              "account"           : self.account_,
              "name"              : self.name_,
              "dependencies"      : self.dependencies_,
              "arguments"         : self.arguments_,
              "union_parse"       : self.submit_ }

    return str( output )



