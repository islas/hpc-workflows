import re
from collections import OrderedDict

import SubmitCommon as sc
from SubmitArgpacks import SubmitArgpacks

class HpcArgpacks( SubmitArgpacks ) :

  def __init__( self, arguments, origin=None ) :
    self.nestedArguments_ = OrderedDict()
    super().__init__( arguments, origin )

  def parseSpecificOptions( self, origin=None ) :
    for key, value in self.arguments_.items() :
      self.nestedArguments_[key] = SubmitArgpacks( value[next( iter( value ) )], origin )
      self.nestedArguments_[key].unique_ = True

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
      origins       = [ self.origins_[argpack] ]
      longestPack   = None
      longestOrigin = None


      if self.nestedArguments_[argpack].arguments_ :
        origins = set( self.nestedArguments_[argpack].origins_.values() )
        longestPack   = len( max( self.nestedArguments_[argpack].origins_.keys(),   key=len ) )
        longestOrigin = len( max( self.nestedArguments_[argpack].origins_.values(), key=len ) )
      
      argpackOption = next( iter( nestedArgs ) )

      print( "  From {0} adding HPC argument pack '{1}' :".format( "[{0}]".format(", ".join( origins ) ), argpack ) )
      print( "    Adding option '{0}'".format( argpackOption ) )

      for key, value in self.nestedArguments_[argpack].arguments_.items() :

        print( 
              "      From {origin:<{length}} adding resource {key:<{packlength}}{val}".format(
                                                                                                      origin=self.nestedArguments_[argpack].origins_[key],
                                                                                                      length=longestOrigin,
                                                                                                      packlength=longestPack + 2,
                                                                                                      key="'{0}'".format( key ),
                                                                                                      val="" if not value else " : {0}".format( value )
                                                                                                      )
              )
      
      argpackOption += argGlue.join( [ res + ( "" if amount == "" else kvGlue + str( amount ) ) for res, amount in self.nestedArguments_[argpack].arguments_.items() ] )
      print( "  Final argpack output for {0} : '{1}'".format( argpack, argpackOption ) )
      additionalArgs.append( argpackOption )
    
    return " ".join( additionalArgs )
  
