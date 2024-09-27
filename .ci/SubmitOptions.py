import copy
import re
import heapq
from collections import OrderedDict
from datetime import timedelta

import SubmitCommon as sc
from SubmitArgpacks import SubmitArgpacks
from HpcArgpacks    import HpcArgpacks


PBS_RESOURCE_REGEX_STR = r"(?P<start>[ ]*-l[ ]+)?(?P<res>\w+)=(?P<amount>.*?)(?=:|[ ]*-l[ ]|$)"
PBS_RESOURCE_REGEX     = re.compile( PBS_RESOURCE_REGEX_STR )


PBS_TIMELIMIT_REGEX_STR    = r"^(?P<hh>\d+):(?P<mm>\d+):(?P<ss>\d+)$"
PBS_TIMELIMIT_REGEX        = re.compile( PBS_TIMELIMIT_REGEX_STR )
PBS_TIMELIMIT_FORMAT_STR   = "{:02}:{:02}:{:02}"



class SubmitOptions( ) :

  def __init__( self, optDict={}, isHostSpecific=False, lockSubmitType=False, origin=None, print=print ) :
    self.submit_            = optDict
    self.workingDirectory_  = None
    self.queue_             = None
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
    self.logfile_          = None

    self.hpcArguments_     = HpcArgpacks   ( OrderedDict() )
    self.arguments_        = SubmitArgpacks( OrderedDict() )

    # Allow host-specific submit options
    self.isHostSpecific_      = isHostSpecific
    self.hostSpecificOptions_ = {}
    self.parse( origin=origin, print=print )

  def parse( self, print=print, origin=None ):
    try :
      submitKeys = []

      key = "working_directory"
      submitKeys.append( key )
      if key in self.submit_ :
        self.workingDirectory_ = self.submit_[ key ]
      
      key = "queue"
      submitKeys.append( key )
      if key in self.submit_ :
        self.queue_ = self.submit_[ key ]
      
      key = "timelimit"
      submitKeys.append( key )
      if key in self.submit_ :
        self.timelimit_ = self.submit_[ key ]
      
      key = "wait"
      submitKeys.append( key )
      if key in self.submit_ :
        self.wait_ = self.submit_[ key ]

      key = "hpc_arguments"
      submitKeys.append( key )
      if key in self.submit_ :
        self.hpcArguments_.update( HpcArgpacks( self.submit_[ key ], origin ), print )
      
      key = "arguments"
      submitKeys.append( key )
      if key in self.submit_ :
        self.arguments_.update( SubmitArgpacks( self.submit_[ key ], origin ), print )
      
      # Allow parsing of per-action submission
      key = "submission"
      submitKeys.append( key )
      if key in self.submit_ :
        if not self.lockSubmitType_ :
          self.submitType_ = sc.SubmissionType( self.submit_[ key ] )


      # Process all other keys as host-specific options
      for key, value in self.submit_.items() :
        if key not in submitKeys :
          if not self.isHostSpecific_ :
            # ok to parse
            self.hostSpecificOptions_[ key ] = SubmitOptions( value, isHostSpecific=True )
            self.hostSpecificOptions_[ key ].parse( origin=origin )
          else :
            print( "Warning: Host-specific options cannot have sub-host-specific options" )
    except Exception as e :
      msg = print( "ERROR! Failed parse for submit options : {{ {fields} }}".format( fields=str( self.submit_ ) )
            )
      if msg is None :
        # just re-raise, we don't have enough info
        raise e
      else :
        raise sc.SubmitParseException( msg ) from e


  # Updates and overrides current with values from rhs if they exist
  def update( self, rhs, print=print ) :
    if rhs.workingDirectory_    is not None : self.workingDirectory_  = rhs.workingDirectory_
    if rhs.queue_               is not None : self.queue_             = rhs.queue_
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

    if rhs.hpcArguments_.arguments_         : self.hpcArguments_.update( rhs.hpcArguments_, print=print )    
    if rhs.arguments_.arguments_            : self.arguments_   .update( rhs.arguments_, print=print )

    for rhsHostOpt in rhs.hostSpecificOptions_ :
      if rhsHostOpt in self.hostSpecificOptions_ :
        self.hostSpecificOptions_[rhsHostOpt].update( rhs.hostSpecificOptions_[rhsHostOpt] )
      else :
        self.hostSpecificOptions_[rhsHostOpt] = copy.deepcopy( rhs.hostSpecificOptions_[rhsHostOpt] )


    # This keeps things consistent but should not affect anything
    sc.recursiveUpdate( self.submit_, rhs.submit_ )
    # self.parse( print=print )
  
  # Check non-optional fields
  def validate( self, print=print ) :
    err          = None

    if self.submitType_ is None :
      err   = "submission type"
    elif self.name_     is None :
      err = "submission job name"
    elif self.submitType_ is not sc.SubmissionType.LOCAL :
      if self.account_ is None :
        err = "account"
      elif self.queue_ is None :
        err = "queue"

      if err is not None :
        err += " on non-LOCAL submission"

    if err is not None :
      errMsg = "Error: Invalid submission options [Missing {opt}]\n{opts}".format( opt=err, opts=self )
      print( errMsg )
      raise Exception( errMsg )
    
    if self.hpcArguments_.arguments_ :
      self.hpcArguments_.selectAncestrySpecificSubmitArgpacks( print=print )



  def setName( self, name ) :
    self.name_ = name
    self.arguments_.setName( name )
    self.hpcArguments_.setName( name )

    for hostOpt in self.hostSpecificOptions_.values() :
      hostOpt.setName( name )

  def selectHostSpecificSubmitOptions( self, host=None, print=print ) :

    # Have to do string matching rather than in dict
    hostSpecificOptKey = next( ( hostOpt for hostOpt in self.hostSpecificOptions_ if hostOpt in host ), None )

    # Quickly generate a stand-in SubmitOptions in spitting image
    currentSubmitOptions = copy.deepcopy( self )

    if hostSpecificOptKey is not None :
      # Update with host-specifics
      currentSubmitOptions.update( self.hostSpecificOptions_[ hostSpecificOptKey ], print )

    return currentSubmitOptions


  def format( self, print=print ) :
    # Why this can't be with the enum
    # https://stackoverflow.com/a/45716067
    # Why this can't be a dict value of the enum
    # https://github.com/python/cpython/issues/88508
    submitDict = {}
    if self.submitType_ == sc.SubmissionType.PBS :
      submitDict    = { "submit" : "qsub",   "arguments"  : "{0}",
                        "name"   : "-N {0}", "dependency" : "-W depend={0}",
                        "queue"  : "-q {0}", "account"    : "-A {0}",
                        "output" : "-j oe -o {0}",
                        "time"   : "-l walltime={0}",
                        "wait"   : "-W block=true" }
    elif self.submitType_ == sc.SubmissionType.SLURM :
      submitDict    = { "submit" : "sbtach", "arguments"  : "{0}",
                        "name"   : "-J {0}", "dependency" : "-d {0}",
                        "queue"  : "-p {0}", "account"    : "-A {0}",
                        "output" : "-j -o {0}",
                        "time"   : "-t {0}",
                        "wait"   : "-W" }
    elif self.submitType_ == sc.SubmissionType.LOCAL :
      submitDict    = { "submit" : "",       "arguments"  : "",
                        "name"   : "",       "dependency" : "",
                        "queue"  : "",       "account"    : "",
                        "output" : "-o {0}",
                        "time"   : "",
                        "wait"   : "" }

    if self.arguments_.arguments_ :
      print( "Gathering argument packs..." )
    additionalArgs = self.arguments_.selectAncestrySpecificSubmitArgpacks( print=print ).format( print=print )

    if self.submitType_ == sc.SubmissionType.LOCAL :
      return [], additionalArgs
    else :
      cmd = [ submitDict[ "submit" ] ]

      # Set through config
      if self.hpcArguments_.arguments_ :
        print( "Gathering HPC argument packs..." )

        cmd.extend( submitDict[ "arguments" ].format(
                                                      self.hpcArguments_.
                                                        selectAncestrySpecificSubmitArgpacks( print=print ).
                                                        format( self.submitType_, print=print ) ).
                                                        split( " " )
                                                      )

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
        cmd.extend( submitDict[ "output" ].format( self.logfile_ ).split( " " ) )


      if self.dependencies_ is not None :
        cmd.extend( submitDict[ "dependency" ].format( self.dependencies_ ).split( " " ) )

      if self.submitType_ == sc.SubmissionType.PBS :
        # Extra bit to delineate command + args
        cmd.append( "--" )

      return cmd, additionalArgs

  def __str__( self ) :
    output = {
              "working_directory" : self.workingDirectory_,
              "queue"             : self.queue_,
              "hpc_arguments"     : self.hpcArguments_,
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

  @staticmethod
  def parseTimelimit( timelimit, submitType ) :
    timeMatch = None
    if submitType == sc.SubmissionType.PBS :
      timeMatch = PBS_TIMELIMIT_REGEX.match( timelimit )
    elif submitType == sc.SubmissionType.SLURM :
      pass
    if timeMatch is not None :
      timeGroups = timeMatch.groupdict()
      return timedelta(
                        hours  =int( timeGroups["hh"] ),
                        minutes=int( timeGroups["mm"] ),
                        seconds=int( timeGroups["ss"] )
                      )
    else :
      return None
  
  @staticmethod
  def formatTimelimit( timelimit, submitType ) :
    totalSeconds = timelimit.total_seconds()
    if submitType == sc.SubmissionType.PBS :
      return '{:02}:{:02}:{:02}'.format(
                                        int(totalSeconds//3600),
                                        int(totalSeconds%3600//60),
                                        int(totalSeconds%60)
                                        )
    elif submitType == sc.SubmissionType.SLURM :
      return None
