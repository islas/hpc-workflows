#!/usr/bin/env python3
import sys
import json
import os
from Test          import Test
from SubmitOptions import SubmitOptions
from SubmitAction  import SubmitAction

class Suite( SubmitAction ) :
  def __init__( self, name, options, defaultSubmitOptions = SubmitOptions(), parent = "", rootDir = "./" ) :
    self.tests_ = {}
    super().__init__( name, options, defaultSubmitOptions, parent, rootDir )


  def parseSpecificOptions( self ) :
    for test, testDict in self.options_.items() :
      if test != "submit_options" :
        self.tests_[ test ] = Test( test, testDict, self.submitOptions_, parent=self.name_, rootDir=self.rootDir_ )

  def run( self, test ) :
    self.setWorkingDirectory()
    if test not in self.tests_.keys() :
      print( "Error: no test named '{0}'".format( test ) )
      exit( 1 )
    else:
      self.tests_[ test ].run()

def main() :
  testsConfig = sys.argv[1]
  test        = sys.argv[2]
  runType     = None
  account     = ""

  if len( sys.argv ) > 3 :
    runType     = SubmitOptions.SubmissionType[ sys.argv[3] ]
    if len( sys.argv ) > 4 :
      account     = sys.argv[4]
    elif runType != SubmitOptions.SubmissionType.LOCAL :
      # We don't have an account && we are not running local
      err = "Error: No account provided for non-local run."
      print( err )
      raise Exception( err )
  else:
    runType = SubmitOptions.SubmissionType.LOCAL

  opts = SubmitOptions()
  opts.account_    = account
  opts.submitType_ = runType

  fp    = open( testsConfig, 'r' )
  # Go up one to get repo root - change this if you change the location of this script
  root  = os.path.abspath( os.path.dirname( sys.argv[0] ) + "/../" )
  
  testSuite = Suite( 
                    testsConfig,
                    json.load( fp ),
                    opts,
                    rootDir=root
                    )

  testSuite.run( test )

if __name__ == '__main__' :
  main()
