import copy
import socket
import re
import math
import heapq
from collections import OrderedDict
from enum import Enum
from datetime import timedelta

# https://stackoverflow.com/a/3233356
import collections.abc

LABEL_LENGTH = 12

PBS_RESOURCE_REGEX_STR = r"(?P<start>[ ]*-l[ ]+)?(?P<res>\w+)=(?P<amount>.*?)(?=:|[ ]*-l[ ]|$)"
PBS_RESOURCE_REGEX     = re.compile( PBS_RESOURCE_REGEX_STR )

# http://docs.adaptivecomputing.com/torque/4-1-3/Content/topics/2-jobs/requestingRes.htm
PBS_RESOURCE_SIZE_REGEX_STR = r"(?P<numeric>\d+)(?P<multi>(?P<scale>k|m|g|t)?(?P<unit>b|w))"
PBS_RESOURCE_SIZE_REGEX     = re.compile( PBS_RESOURCE_SIZE_REGEX_STR, re.I )

PBS_TIMELIMIT_REGEX_STR    = r"^(?P<hh>\d+):(?P<mm>\d+):(?P<ss>\d+)$"
PBS_TIMELIMIT_REGEX        = re.compile( PBS_TIMELIMIT_REGEX_STR )
PBS_TIMELIMIT_FORMAT_STR   = "{:02}:{:02}:{:02}"

# Update mapping dest with source
def recursiveUpdate( dest, source ):
  for k, v in source.items():
    if isinstance( v, collections.abc.Mapping ):
      dest[k] = recursiveUpdate( dest.get( k, {} ), v )
    else:
      dest[k] = v
  return dest

# Move this out of nested class for pickle
class SubmissionType( Enum ):
  PBS   = "PBS"
  SLURM = "SLURM"
  LOCAL = "LOCAL"

  def __str__( self ) :
    return self.value

class SubmitOptions( ) :
  
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
    self.logfile_          = None

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
        self.submitType_ = SubmissionType( self.submit_[ key ] )


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
    elif self.submitType_ is not SubmissionType.LOCAL :
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


  def format( self, print=print ) :
    # Why this can't be with the enum
    # https://stackoverflow.com/a/45716067
    # Why this can't be a dict value of the enum
    # https://github.com/python/cpython/issues/88508
    submitDict = {}
    if self.submitType_ == SubmissionType.PBS :
      submitDict    = { "submit" : "qsub",   "resources"  : "{0}",
                        "name"   : "-N {0}", "dependency" : "-W depend={0}",
                        "queue"  : "-q {0}", "account"    : "-A {0}",
                        "output" : "-j oe -o {0}",
                        "time"   : "-l walltime={0}",
                        "wait"   : "-W block=true" }
    elif self.submitType_ == SubmissionType.SLURM :
      submitDict    = { "submit" : "sbtach", "resources"  : "{0}",
                        "name"   : "-J {0}", "dependency" : "-d {0}",
                        "queue"  : "-p {0}", "account"    : "-A {0}",
                        "output" : "-j -o {0}",
                        "time"   : "-t {0}",
                        "wait"   : "-W" }
    elif self.submitType_ == SubmissionType.LOCAL :
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
      longestPack   = len( max( [ key for key, sortname in argpacksToUse if key != SubmitOptions.ARGUMENTS_ORIGIN_KEY ], key=len ) )
      longestOrigin = len( max( [ self.arguments_[SubmitOptions.ARGUMENTS_ORIGIN_KEY][key] for key, sortname in argpacksToUse if key != SubmitOptions.ARGUMENTS_ORIGIN_KEY ], key=len ) )
      for key, sortname in sorted( argpacksToUse, key=lambda pack : pack[1] ) :
        if key != SubmitOptions.ARGUMENTS_ORIGIN_KEY :
          print( 
                "From {origin:<{length}} adding arguments pack {key:<{packlength}} : {val}".format(
                                                                                        origin=self.arguments_[SubmitOptions.ARGUMENTS_ORIGIN_KEY][key],
                                                                                        length=longestOrigin,
                                                                                        packlength=longestPack + 2,
                                                                                        key="'{0}'".format( key ),
                                                                                        val=self.arguments_[key]
                                                                                        )
                )
          additionalArgs.extend( self.arguments_[key] )

    if self.submitType_ == SubmissionType.LOCAL :
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
        cmd.extend( submitDict[ "output" ].format( self.logfile_ ).split( " " ) )


      if self.dependencies_ is not None :
        cmd.extend( submitDict[ "dependency" ].format( self.dependencies_ ).split( " " ) )

      if self.submitType_ == SubmissionType.PBS :
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

  @staticmethod
  def parseTimelimit( timelimit, submitType ) :
    timeMatch = None
    if submitType == SubmissionType.PBS :
      timeMatch = PBS_TIMELIMIT_REGEX.match( timelimit )
    elif submitType == SubmissionType.SLURM :
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
    if submitType == SubmissionType.PBS :
      return '{:02}:{:02}:{:02}'.format(
                                        int(totalSeconds//3600),
                                        int(totalSeconds%3600//60),
                                        int(totalSeconds%60)
                                        )
    elif submitType == SubmissionType.SLURM :
      return None

  @staticmethod
  def resourceMemSizeDict( amountStr, submitType ) :
    memMatch = None 
    if submitType == SubmissionType.PBS :
      memMatch = PBS_RESOURCE_SIZE_REGEX.match( amountStr )
    elif submitType == SubmissionType.SLURM :
      pass

    if memMatch is not None :
      return { k : ( v.lower() if v is not None else v ) for k,v in memMatch.groupdict().items() }
    else :
      return None

  @staticmethod
  def resourceMemSizeBase( amountDict ) :
    multipliers   = { None : 1, "k" : 1024, "m" : 1024**2, "g" : 1024**3, "t" : 1024**4 }
    return multipliers[ amountDict["scale" ] ] * int( amountDict["numeric"] )

  @staticmethod
  def resourceMemSizeFormat( amountDict ) :
    memSizeFormat = "{num}{scale}{unit}"
    return memSizeFormat.format(
                                num=amountDict["numeric"],
                                scale=amountDict[ "scale" ] if amountDict[ "scale" ] else "",
                                unit=amountDict["unit"]
                                )
  
  @staticmethod
  def resourceMemSizeReduce( amountDict ) :
    multipliers   = { None : 1, "k" : 1024, "m" : 1024**2, "g" : 1024**3, "t" : 1024**4 }

    totalAmount = SubmitOptions.resourceMemSizeBase( amountDict )
    
    # Convert to simplified size, round up if needed
    log2 = math.log( totalAmount, 2 )
    scale = None
    if log2 > 30.0 :
      # Do it in gibi
      scale = "g"
    elif log2 > 20.0 :
      # mebi
      scale = "m"
    elif log2 > 10.0 :
      # kibi
      scale = "k"
    
    reducedDict = {
                    "numeric" : math.ceil( totalAmount / float( multipliers[ scale ] ) ),
                    "scale"   : scale,
                    "unit"    : amountDict["unit"]
                  }
    return reducedDict


  @staticmethod
  def breakdownResources( resourceStr, submitType ) :
    resourceBreakDown = OrderedDict()
    if   submitType == SubmissionType.PBS :
      currentKey        = ""
      # Fill first amount up, generating resource groups
      for resFound in PBS_RESOURCE_REGEX.finditer( resourceStr ) :
        groups = resFound.groupdict( )
        if groups[ "start" ] is not None :
          currentKey = groups["res"]
        
        if currentKey not in resourceBreakDown :
          resourceBreakDown[currentKey] = {}
        resourceBreakDown[ currentKey ][ groups[ "res" ] ] = groups[ "amount" ]

    elif submitType == SubmissionType.SLURM :
      pass

    return resourceBreakDown
  
  @staticmethod
  def formatResourceBreakdown( resourceBreakDown, submitType ) :
    finalResources = ""
    if   submitType == SubmissionType.PBS :
      # Do PBS-specific merging
      finalResources = "-l " + " -l ".join( [ ":".join( [ "{0}={1}".format( k,v ) for k,v in resources.items() ] ) for resources in resourceBreakDown.values() ] )
    elif submitType == SubmissionType.SLURM :
      pass
    
    return finalResources

  @staticmethod
  def joinHPCResourcesMax( resourceStrs, submitType, maxN, print=print ) :
    allBreakdowns = [ SubmitOptions.breakdownResources( res, submitType ) for res in resourceStrs ]

    # # Flatten and get all keys
    # allResourceTypes = list( set( [ res for breakdown in allBreakdowns for resGroup in breakdown.values() for res in resGroup.keys() ] ) )

    organizedResources = {}
    for breakdown in allBreakdowns :
      for group, resources in breakdown.items() :
        if group not in organizedResources :
          organizedResources[ group ] = {}
        for resource, amount in resources.items() :
          if resource not in organizedResources[ group ] :
            organizedResources[ group ][ resource ] = []
          # Accumulate all resources' amounts into lists
          organizedResources[ group ][ resource ].append( amount )

    finalBreakdown = {}
    for group, resources in organizedResources.items() :
      finalBreakdown[ group ] = {}
      for resource, amounts in resources.items() : 
        try :
          finalBreakdown[ group ][ resource ] = sum( [ int(amount) for amount in heapq.nlargest( maxN, amounts ) ] )
        except ValueError :
          resMem = SubmitOptions.resourceMemSizeDict( amounts[0], submitType )
          if resMem is not None :
            amountsAsDicts = [ SubmitOptions.resourceMemSizeDict( amount, submitType ) for amount in amounts ]
            baseAmount = sum( [ SubmitOptions.resourceMemSizeBase( memDict ) for memDict in
                                heapq.nlargest(
                                                maxN,
                                                amountsAsDicts,
                                                key=lambda amount : SubmitOptions.resourceMemSizeBase( amount )
                                                )
                              ]
                            )
            finalBreakdown[ group ][ resource ] = SubmitOptions.resourceMemSizeFormat(
                                                    SubmitOptions.resourceMemSizeReduce(
                                                      {
                                                        "numeric" : baseAmount,
                                                        "scale"   : None,
                                                        "unit"    : resMem[ "unit" ]
                                                      }
                                                    )
                                                  )

          else :
            print( "Unable to sort resource type {0}, using {1}".format( resource, amounts[0] ) )
            finalBreakdown[ group ][ resource ] = amounts[0]

    return SubmitOptions.formatResourceBreakdown( finalBreakdown, submitType )


  @staticmethod
  def joinHPCResourcesOp( steps, op, print=print ) :
    resources = ""
    for step in steps :
      resources = SubmitOptions.joinHPCResourcesStrOp( resources, step.submitOptions_.resources_, step.submitOptions_.submitType_, op, print=print )
    return resources

  @staticmethod
  def joinHPCResourcesStrOp( res1, res2, submitType, op, print=print ) :
    finalResources = ""
    finalResourceBreakdown = OrderedDict()

    # Only join if both are not empty, else take the not empty one
    if res1 and res2 :
      finalResourceBreakdown = SubmitOptions.breakdownResources( res1, submitType )
      mergeResourceBreakdown = SubmitOptions.breakdownResources( res2, submitType )
      
      # Loop merge and add if possible
      for group, resources in mergeResourceBreakdown.items() :
        if group in finalResourceBreakdown :
          for res, amount in resources.items() :
            if res in finalResourceBreakdown[ group ] :
              # Now for the tricky part
              try :
                finalAmount = op( int( amount ), int( finalResourceBreakdown[ group ][ res ] ) )
                finalResourceBreakdown[ group ][ res ] = finalAmount
              except ValueError:
                # Not an int value, size value?
                resMem = SubmitOptions.resourceMemSizeDict( amount, submitType )
                if resMem is not None :
                  finalAmountMem = SubmitOptions.resourceMemSizeDict( finalResourceBreakdown[ group ][ res ], submitType )
                  if resMem[ "unit" ] == finalAmountMem[ "unit" ] :
                    # Can add
                    rhsAmount = SubmitOptions.resourceMemSizeBase( resMem )
                    lhsAmount = SubmitOptions.resourceMemSizeBase( finalAmountMem )

                    totalAmount = op( rhsAmount, lhsAmount )
                    finalResourceBreakdown[ group ][ res ] = SubmitOptions.resourceMemSizeFormat( 
                                                                SubmitOptions.resourceMemSizeReduce(
                                                                                                    {
                                                                                                      "numeric" : totalAmount,
                                                                                                      "scale"   : None,
                                                                                                      "unit"    : resMem["unit"]
                                                                                                    }
                                                                                                  )
                                                                                                )
                  else :
                    msg = "Error : cannot perform operation with values {0} and {1}".format( rhs["multi"], lhs["multi"] )
                    print( msg )
                    raise Exception( msg )
                else :
                  # Not sure how to add, leave as is
                  print( "Unsure how to operate on resources {0} and {1} together, defaulting to {0}".format( finalResourceBreakdown[ group ][ res ], amount ) )
            else :
              # Just add
              finalResourceBreakdown[ group ][ res ] = amount
        else :
          # Just add
          finalResourceBreakdown[ group ] = resources
      
      # Generate the final resource in our HPC format
      finalResources = SubmitOptions.formatResourceBreakdown( finalResourceBreakdown, submitType )

    else :
      finalResources = res1 if res1 else res2

    return finalResources


