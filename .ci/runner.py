#!/usr/bin/env python3
import sys
import json
import os
import argparse
import inspect
from Test          import Test
from SubmitOptions import SubmitOptions
from SubmitAction  import SubmitAction
import SubmitOptions as so

class Suite( SubmitAction ) :
  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.tests_ = {}
    super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )


  def parseSpecificOptions( self ) :
    for test, testDict in self.options_.items() :
      if test != "submit_options" :
        self.tests_[ test ] = Test( test, testDict, self.submitOptions_, self.globalOpts_, parent=self.name_, rootDir=self.rootDir_ )

  def run( self, test ) :
    self.setWorkingDirectory()
    if test not in self.tests_.keys() :
      print( "Error: no test named '{0}'".format( test ) )
      exit( 1 )
    else:
      self.tests_[ test ].run()

def getOptionsParser():
  parser = argparse.ArgumentParser( epilog=inspect.cleandoc("""
                                                            All tests & steps will be run with root dir = <abs path to json> + dirOffset
                                                            Meaning if no [dirOffset] is provided, the root dir from which all working directories
                                                            are evaluated will be from the location of the JSON test suite definition file

                                                            Test & steps will be prefixed with current context, except for
                                                            sections delineated with '***...***' as those will be raw step 
                                                            command output.

                                                            Scripts running from this framework should always take at least one 
                                                            prefix arguments ($1) before any other arguments which will be the 
                                                            working directory that should immediate be cd'ed to
                                                            """ ),
                                  formatter_class=argparse.RawTextHelpFormatter
                                  )

  parser.add_argument( 
                      "testsConfig",
                      help="JSON file defining set of tests",
                      type=str,
                      default=""
                      )
  parser.add_argument( 
                      "test",
                      help="Test name matching respective JSON test name to run",
                      type=str,
                      default=""
                      )
  parser.add_argument( 
                      "-s", "--submit",
                      dest="submitType",
                      help="Override type of submission to use for all steps submitted",
                      type=SubmitOptions.SubmissionType,
                      choices=list( SubmitOptions.SubmissionType),
                      default=None
                      )
  parser.add_argument( 
                      "-a", "--account",
                      dest="account",
                      help="Account to use when submitting to an HPC",
                      type=str,
                      default=None
                      )
  parser.add_argument( 
                      "-d", "--dirOffset",
                      dest="dirOffset",
                      help="Offset from root dir to run entire suite from",
                      type=str,
                      default=""
                      )
  parser.add_argument( 
                      "-l", "--labelLength",
                      dest="labelLength",
                      help="Length of left-justify label string [file|test|step]",
                      type=int,
                      default=12
                      )

  return parser


class Options(object):
  """Empty namespace"""
  pass

def main() :
  parser  = getOptionsParser()
  options = Options()
  parser.parse_args( namespace=options )
  sa.LABEL_LENGTH = options.labelLength

  opts = SubmitOptions()
  opts.account_    = options.account

  if options.submitType is None :
    # Set default to LOCAL, but do not force
    opts.submitType_ = SubmitOptions.SubmissionType.LOCAL
    print( "Setting default submission type to {0} for steps with unspecified type".format( opts.submitType_ ) )
  else :
    opts.submitType_         = options.submitType
    opts.lockSubmitType_     = True
    print( "Forcing submission type to {0} for all steps".format( opts.submitType_ ) )
  
  if opts.submitType_ != SubmitOptions.SubmissionType.LOCAL and opts.account_ is None:
    # We don't have an account && we are not running local
    err = "Error: No account provided for non-local run."
    print( err )
    raise Exception( err )

  fp    = open( options.testsConfig, 'r' )
  # Go up one to get repo root - change this if you change the location of this script
  root  = os.path.abspath( os.path.dirname( options.testsConfig ) + "/" + options.dirOffset )
  print( "Root directory is : {0}".format( root ) )
  
  testSuite = Suite( 
                    options.testsConfig,
                    json.load( fp ),
                    opts,
                    options,
                    rootDir=root
                    )

  testSuite.run( options.test )

if __name__ == '__main__' :
  main()
