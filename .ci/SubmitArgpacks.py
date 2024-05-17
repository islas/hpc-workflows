import re
from collections import OrderedDict

import SubmitCommon as sc

class SubmitArgpacks( ) :
  
  ARGUMENTS_ORIGIN_KEY = "arguments_origin"
  REGEX_DELIMETER      = "::"

  def __init__( self, arguments, origin=None ) :
    self.arguments_        = arguments

    # Should be set via the SubmitOptions
    self.name_             = None

    self.parse( origin=origin )

  def parse( self, origin=None ):
    if origin is not None :
      self.arguments_[ SubmitArgpacks.ARGUMENTS_ORIGIN_KEY ] = { argKey : origin for argKey in self.arguments_.keys() }

  # Updates and overrides current with values from rhs if they exist
  def update( self, rhs, print=print ) :
    # Should be set via the step
    if rhs.name_                is not None : self.name_             = rhs.name_

    # This keeps things consistent but should not affect anything
    sc.recursiveUpdate( self.arguments_, rhs.arguments_ )
    self.parse( )
    self.validate( print=print )

  def validate( self, print=print ) :
    allArgpacks =  {}
    for argpack in self.arguments_.keys() :
      argpackName = argpack

      if SubmitArgpacks.REGEX_DELIMETER in argpack :
        argpackName = argpack.split( SubmitArgpacks.REGEX_DELIMETER )[1]

        if argpackName in allArgpacks :
          err = "Regex argument pack at {conflict} '{repack}' name conflict with '{argpack}', declared at {origin}".format(
                  repack=argpack,
                  argpack=allArgpacks[argpackName],
                  conflict=self.arguments_[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY][argpack],
                  origin=self.arguments_[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY][allArgpacks[argpackName]]
                  )
          print( err )
          raise Exception( err )

      # add to the known argpacks
      allArgpacks[argpackName] = argpack

  def selectAncestrySpecificSubmitArgpacks( self, sortArgpacks=True ) :
    # Find all argument packs that match our ancestry
    argpacksToUse = OrderedDict()

    for argpack in self.arguments_.keys() :
      if argpack != SubmitArgpacks.ARGUMENTS_ORIGIN_KEY :
        if SubmitArgpacks.REGEX_DELIMETER in argpack :
          # print( "Checking scope-specific argument pack {0}".format( argpack ) )
          # Take everything before :: and treat it as a regex to match ancestry
          scopeRegex = argpack.split( SubmitArgpacks.REGEX_DELIMETER )[0]
          if re.match( scopeRegex, self.name_ ) is not None :
            argpacksToUse[argpack] = self.arguments_[argpack]
        else :
          # Generic pack, send it off!
          argpacksToUse[argpack] = self.arguments_[argpack]

    argpacksToUse[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY] = { 
                                                            key : self.arguments_[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY][key]
                                                            for key in argpacksToUse.keys()
                                                          }
    finalArgpacksToUse = argpacksToUse
    if sortArgpacks : 
      finalArgpacksToUse = OrderedDict( 
                                  sorted(
                                          argpacksToUse.items(),
                                          key=lambda pack : pack[0] if SubmitArgpacks.REGEX_DELIMETER not in pack[0] else pack[0].split( SubmitArgpacks.REGEX_DELIMETER )[1]
                                          )
                                  )

      finalArgpacksToUse[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY] = argpacksToUse[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY]
    
    finalArgpacks = SubmitArgpacks( finalArgpacksToUse )
    
    return finalArgpacks

  def format( self, print=print ) :

    # Format them and pass them out in alphabetical order based on name, NOT REGEX
    longestPack   = len( max( [ key for key in self.arguments_.keys() if key != SubmitArgpacks.ARGUMENTS_ORIGIN_KEY ], key=len ) )
    longestOrigin = len( max( self.arguments_[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY].keys(), key=len ) )
    additionalArgs = []

    for key, value in self.arguments_.items() :
      if key != SubmitArgpacks.ARGUMENTS_ORIGIN_KEY :
        print( 
              "From {origin:<{length}} adding arguments pack {key:<{packlength}} : {val}".format(
                                                                                      origin=self.arguments_[SubmitArgpacks.ARGUMENTS_ORIGIN_KEY][key],
                                                                                      length=longestOrigin,
                                                                                      packlength=longestPack + 2,
                                                                                      key="'{0}'".format( key ),
                                                                                      val=self.arguments_[key]
                                                                                      )
              )
        additionalArgs.extend( self.arguments_[key] )
    
    return additionalArgs
  
