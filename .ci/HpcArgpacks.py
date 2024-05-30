import re
import copy
import math
from collections import OrderedDict

import SubmitCommon as sc
from SubmitArgpacks import SubmitArgpacks

# http://docs.adaptivecomputing.com/torque/4-1-3/Content/topics/2-jobs/requestingRes.htm
PBS_RESOURCE_SIZE_REGEX_STR = r"(?P<numeric>\d+)(?P<multi>(?P<scale>k|m|g|t)?(?P<unit>b|w))"
PBS_RESOURCE_SIZE_REGEX     = re.compile( PBS_RESOURCE_SIZE_REGEX_STR, re.I )

class HpcArgpacks( SubmitArgpacks ) :

  HPC_JOIN_NAME = "join"

  def __init__( self, arguments, origin=None ) :
    self.nestedArguments_ = OrderedDict()
    super().__init__( arguments, origin )

  def parseSpecificOptions( self, origin=None ) :
    for key, value in self.arguments_.items() :
      self.nestedArguments_[key] = SubmitArgpacks( value[next( iter( value ) )], origin )
      self.nestedArguments_[key].unique_ = True
  
  def setName( self, name ) :
    super().setName( name )
    for key, nestedArg in self.nestedArguments_.items() :
      nestedArg.setName( name )

  # Updates and overrides current with values from rhs if they exist
  def update( self, rhs, print=print ) :
    for key, rhsNestedArg in rhs.nestedArguments_.items() :
      if key in self.nestedArguments_ :
        self.nestedArguments_[key].update( rhs.nestedArguments_[key], print )
      else :
        self.nestedArguments_[key] = rhs.nestedArguments_[key]
      
    super().update( rhs, print )

  def validate( self, print=print ) :
    super().validate( print )

    for key, value in self.arguments_.items() : 
      if len( value ) != 1 :
        err = "HPC argument packs must only have one option declared per pack"
        print( err )
        raise Exception( err )
    for option, argpacks in self.nestedArguments_.items() :
      argpacks.validate( print )
    

  def selectAncestrySpecificSubmitArgpacks( self, sortArgpacks=False, print=print ) :
    keysToUse = super().selectAncestrySpecificSubmitArgpacks( sortArgpacks, print ).arguments_.keys()
    hpcArgpacksToUse = OrderedDict()

    for argpack in keysToUse :
      # We've downselected which hpc argpacks to use, now further select which resources if present
      hpcArgpacksToUse[argpack] = OrderedDict()
      hpcArgpacksToUse[argpack][next( iter( self.arguments_[argpack] ) )] = self.nestedArguments_[argpack].selectAncestrySpecificSubmitArgpacks( sortArgpacks, print ).arguments_
    
    finalHpcArgpacks = HpcArgpacks( hpcArgpacksToUse )
    finalHpcArgpacks.origins_ = self.origins_
    for argpack in finalHpcArgpacks.nestedArguments_.keys() :
      finalHpcArgpacks.nestedArguments_[argpack].origins_ = self.nestedArguments_[argpack].origins_

    # final selection does not allow for duplicates
    finalHpcArgpacks.unique_ = True
    finalHpcArgpacks.validate( print=print )

    return finalHpcArgpacks

  def getPrintInfo( self, argpack ) :
    origins       = [ self.origins_[argpack] ]
    longestPack   = len( max( self.origins_.keys(), key=len ) )
    longestNestedPack   = None
    longestNestedOrigin = None


    if self.nestedArguments_[argpack].arguments_ :
      origins = set( self.nestedArguments_[argpack].origins_.values() )
      longestNestedPack   = len( max( self.nestedArguments_[argpack].origins_.keys(),   key=len ) )
      longestNestedOrigin = len( max( self.nestedArguments_[argpack].origins_.values(), key=len ) )
  
    return origins, longestPack, longestNestedPack, longestNestedOrigin


  def format( self, submitType, print=print ) :
    additionalArgs = []
    kvGlue  = None
    argGlue = None

    if submitType == sc.SubmissionType.PBS :
      kvGlue  = "="
      argGlue = ":"
    elif submitType == sc.SubmissionType.SLURM :
      kvGlue  = ":"
      argGlue = ","


    for argpack, nestedArgs in self.arguments_.items() :
      origins, _, longestNestedPack, longestNestedOrigin = self.getPrintInfo( argpack )
      
      argpackOption = next( iter( nestedArgs ) )

      print( "  From [{0}] adding HPC argument pack '{1}' :".format( ", ".join( origins ), argpack ) )
      print( "    Adding option '{0}'".format( argpackOption ) )

      for key, value in self.nestedArguments_[argpack].arguments_.items() :

        print( 
              "      From {origin:<{length}} adding resource {key:<{packlength}}{val}".format(
                                                                                                      origin=self.nestedArguments_[argpack].origins_[key],
                                                                                                      length=longestNestedOrigin,
                                                                                                      packlength=longestNestedPack + 2,
                                                                                                      key="'{0}'".format( key ),
                                                                                                      val="" if not value else " : {0}".format( value )
                                                                                                      )
              )
      
      argpackOption += argGlue.join( [ res + ( "" if amount == "" else kvGlue + str( amount ) ) for res, amount in self.nestedArguments_[argpack].arguments_.items() ] )
      print( "  Final argpack output for {0} : '{1}'".format( argpack, argpackOption ) )
      additionalArgs.append( argpackOption )
    
    return " ".join( additionalArgs )

  def join( self, rhs, submitType, op, print=print ) :
    # Because we are joining all origins and regex don't matter anymore so don't 
    # try to track them anymore - join on the underlying name of the argpacks
    # not the flags or resources as this would provide the greatest flexibility
    # to users in partitioning out resources. Only throw error on conflict in option
    # flag if it doesn't match
    for key, value in rhs.arguments_.items() : 
      # print( "Checking if {key} exists in {name}".format( key=key, name=self.name_ ) )
      exists, occurrences = self.keyExists( key )
      if exists :

        # Join with the first occurrence ONLY!!
        argpack = next(iter(occurrences))

        # check if flags match
        rhsOption = next(iter(value))
        lhsOption = next(iter(self.arguments_[argpack]))
        if rhsOption != lhsOption :
          msg = "Options {0} from {1} and {2} from {3} do not match".format(
                                                                            lhsOption,
                                                                            argpack,
                                                                            rhsOption,
                                                                            key
                                                                            )
          print( msg )
          raise Exception( msg )

        origins, argpackLen, longestPack, longestOrigin = rhs.getPrintInfo( key )
        print( "  Joining argpack {key:<{arglen}} from [{rhs}] into {name}".format( 
                                                                                    key="'{0}'".format( key ),
                                                                                    arglen=argpackLen + 2,
                                                                                    rhs=", ".join(
                                                                                                  set( rhs.nestedArguments_[key].origins_.values() )
                                                                                                  ),
                                                                                    name=self.name_
                                                                                    )
                                                                                  )

        for res, amount in rhs.nestedArguments_[key].arguments_.items() :
          resExists, resOccurrences = self.nestedArguments_[argpack].keyExists( res )
          if resExists and amount != "" :
            resName = next(iter(resOccurrences))
            try :
              self.nestedArguments_[argpack].arguments_[resName] = op( 
                                                                      int( self.nestedArguments_[argpack].arguments_[resName] ),
                                                                      int( amount )
                                                                      )
            except ValueError:
              # Not an int value, size value / maybe this is a memory resource
              lhsMem = HpcArgpacks.resourceMemSizeDict( self.nestedArguments_[argpack].arguments_[resName], submitType )
              if lhsMem is not None :
                rhsMem = SubmitOptions.resourceMemSizeDict( amount, submitType )
                if lhsMem[ "unit" ] == rhsMem[ "unit" ] :
                  # Can add
                  rhsAmount = HpcArgpacks.resourceMemSizeBase( rhsMem )
                  lhsAmount = HpcArgpacks.resourceMemSizeBase( lhsMem )

                  totalAmount = op( rhsAmount, lhsAmount )
                  self.nestedArguments_[argpack].arguments_[resName] = HpcArgpacks.resourceMemSizeFormat( 
                                                                        HpcArgpacks.resourceMemSizeReduce(
                                                                                                            {
                                                                                                              "numeric" : totalAmount,
                                                                                                              "scale"   : None,
                                                                                                              "unit"    : resMem["unit"]
                                                                                                            }
                                                                                                          )
                                                                                                        )
                else :
                  msg = "Error : cannot perform operation with values {0} and {1}".format( lhsMem["multi"], rhsMem["multi"] )
                  print( msg )
                  raise Exception( msg )
              else :
                # No idea how to join this arg
                print( "Unsure how to operate on resources {0} and {1} together, defaulting to {0}".format( self.nestedArguments_[argpack].arguments_[resName], amount ) )
          
          else :
            # assign new resource - remove all regex to signify generalization
            self.nestedArguments_[argpack].arguments_[res.split( SubmitArgpacks.REGEX_DELIMETER )[-1]] = amount
            self.nestedArguments_[argpack].origins_  [res.split( SubmitArgpacks.REGEX_DELIMETER )[-1]] = HpcArgpacks.HPC_JOIN_NAME

      else :
        # Just add
        # print( "No {key} in {name}, adding to list".format( key=key, name=self.name_ ) )
        genArgpack = key.split( SubmitArgpacks.REGEX_DELIMETER )[-1]
        self.arguments_[genArgpack]       = copy.deepcopy(value)
        self.origins_  [genArgpack]       = HpcArgpacks.HPC_JOIN_NAME
        self.nestedArguments_[genArgpack] = SubmitArgpacks( OrderedDict() )
        self.nestedArguments_[genArgpack].unique_ = True

        for res, amount in rhs.nestedArguments_[key].arguments_.items() :
          self.nestedArguments_[genArgpack].arguments_[res.split( SubmitArgpacks.REGEX_DELIMETER )[-1]] = amount
          self.nestedArguments_[genArgpack].origins_  [res.split( SubmitArgpacks.REGEX_DELIMETER )[-1]] = HpcArgpacks.HPC_JOIN_NAME 
  


  @staticmethod
  def joinAll( hpcArgpacks, submitType, op, print=print ) :
    finalHpcArgpacks = HpcArgpacks( OrderedDict() )
    finalHpcArgpacks.setName( HpcArgpacks.HPC_JOIN_NAME + "all" )
    if len( hpcArgpacks ) == 0 :
      return finalHpcArgpacks
    
    for argpack in hpcArgpacks :
      finalHpcArgpacks.join( argpack, submitType, op, print=print )
    
    return finalHpcArgpacks


  @staticmethod
  def resourceMemSizeDict( amountStr, submitType ) :
    memMatch = None 
    if submitType == sc.SubmissionType.PBS :
      memMatch = PBS_RESOURCE_SIZE_REGEX.match( amountStr )
    elif submitType == sc.SubmissionType.SLURM :
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

