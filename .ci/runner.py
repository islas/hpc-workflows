#!/usr/bin/env python3
import sys
import json
from Test          import Test
from SubmitOptions import SubmitOptions

class Suite() :
  def __init__( self, filename ) :
    fp    = open( filename, 'r' )
    self.suite_ = json.load( fp )
    self.tests_ = {}
    self.submitOptions_ = SubmitOptions( )
    self.submitOptions_.account_    = "testing-account"
    self.submitOptions_.submitType_ = SubmitOptions.SubmissionType.PBS
    self.submitOptions_.debug_      = True

    for test, testDict in self.suite_.items() :
      self.tests_[ test ] = Test( test, testDict, self.submitOptions_ )
  
  def run( self, test ) :
    if test not in self.tests_.keys() :
      print( "Error: no test named '{0}'".format( test ) )
      exit( 1 )
    else:
      self.tests_[ test ].run()

def main() :
  testsConfig = sys.argv[1]
  test        = sys.argv[2]
  
  testSuite = Suite( testsConfig )
  
  testSuite.run( test )

if __name__ == '__main__' :
  main()
