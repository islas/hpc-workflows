import re
from collections import OrderedDict

import SubmitCommon as sc

class SubmitArgpacks( ) :
  
  ARGUMENTS_ORIGIN_KEY = "arguments_origin"
  REGEX_DELIMETER      = "::"

  def __init__( self, arguments, origin=None ) :
    self.arguments_        = arguments
    self.origins_          = {}

    # Should be set via the SubmitOptions
    self.name_             = None

    # Internal control for forcing uniqueness
    self.unique_           = False

    self.parse( origin=origin )

  def parse( self, origin=None ):
    if origin is not None :
      self.origins_ = { argKey : origin for argKey in self.arguments_.keys() }

    # Now call child parse
    self.parseSpecificOptions( origin )


  def parseSpecificOptions( self, origin=None ) :
    # Children should override this for their respective parse()
    pass
  
  def setName( self, name ) :
    self.name_ = name

  # Updates and overrides current with values from rhs if they exist
  def update( self, rhs, print=print ) :
    # Should be set via the step
    if rhs.name_                is not None : self.name_             = rhs.name_

    # This keeps things consistent but should not affect anything
    sc.recursiveUpdate( self.arguments_, rhs.arguments_ )
    sc.recursiveUpdate( self.origins_,   rhs.origins_   )

    self.validate( print=print )

  def keyExists( self, rawkey ) :
    # dictionaries already handle key exist checks, this is for matching regex
    key = rawkey.split( SubmitArgpacks.REGEX_DELIMETER )[-1]
    
    exists = False
    occurrences = OrderedDict()

    for argpack in self.arguments_.keys() :
      argpackName = argpack.split( SubmitArgpacks.REGEX_DELIMETER )[-1]

      if key == argpackName :
        exists = True
        if self.origins_ :
          occurrences[argpack] = self.origins_[argpack]
        else :
          occurrences[argpack] = "unknown"
    
    return exists, occurrences

  def validate( self, print=print ) :
    if not self.unique_ :
      return

    for argpack in self.arguments_.keys() :
      # of course our key exists, but HOW much
      _, occurrences = self.keyExists( argpack )

      if len( occurrences ) > 1 :
        argpackName = argpack.split( SubmitArgpacks.REGEX_DELIMETER )[-1]
        err = "Argument pack {root} at {conflict} '{offender}' name conflict with '{argpack}', declared at {origin}".format(
                root=argpackName,
                offender=list(occurrences.keys())[1],
                argpack=list(occurrences.keys())[0],
                conflict=list(occurrences.values())[1],
                origin=list(occurrences.values())[0]
                )
        print( err )
        raise Exception( err )


  def selectAncestrySpecificSubmitArgpacks( self, sortArgpacks=True, print=print ) :
    # Find all argument packs that match our ancestry
    argpacksToUse = OrderedDict()

    for argpack in self.arguments_.keys() :
      if SubmitArgpacks.REGEX_DELIMETER in argpack :
        # print( "Checking scope-specific argument pack {0}".format( argpack ) )
        # Take everything before :: and treat it as a regex to match ancestry
        scopeRegex = argpack.split( SubmitArgpacks.REGEX_DELIMETER )[0]
        if re.match( scopeRegex, self.name_ ) is not None :
          argpacksToUse[argpack] = self.arguments_[argpack]
      else :
        # Generic pack, send it off!
        argpacksToUse[argpack] = self.arguments_[argpack]

    finalArgpacksToUse = argpacksToUse
    if sortArgpacks : 
      finalArgpacksToUse = OrderedDict( 
                                  sorted(
                                          argpacksToUse.items(),
                                          key=lambda pack : pack[0].split( SubmitArgpacks.REGEX_DELIMETER )[-1]
                                          )
                                  )
    
    finalArgpacks = SubmitArgpacks( finalArgpacksToUse )
    finalArgpacks.origins_ = { 
                                key : self.origins_[key]
                                for key in argpacksToUse.keys()
                              }
    
    return finalArgpacks

  def format( self, print=print ) :
    longestPack   = None
    longestOrigin = None
    if self.arguments_ :
      longestPack   = len( max( self.origins_.keys(),   key=len ) )
      longestOrigin = len( max( self.origins_.values(), key=len ) )

    additionalArgs = []

    for key, value in self.arguments_.items() :
      if key != SubmitArgpacks.ARGUMENTS_ORIGIN_KEY :
        print( 
              "  From {origin:<{length}} adding arguments pack {key:<{packlength}} : {val}".format(
                                                                                      origin=self.origins_[key],
                                                                                      length=longestOrigin,
                                                                                      packlength=longestPack + 2,
                                                                                      key="'{0}'".format( key ),
                                                                                      val=self.arguments_[key]
                                                                                      )
              )
        additionalArgs.extend( self.arguments_[key] )
    
    return additionalArgs
  
