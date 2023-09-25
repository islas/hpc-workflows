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
  def scope( self ) :
    return "file"

  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.tests_ = {}
    super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )


  def parseSpecificOptions( self ) :
    for test, testDict in self.options_.items() :
      if test != "submit_options" :
        self.tests_[ test ] = Test( test, testDict, self.submitOptions_, self.globalOpts_, parent=self.ancestry(), rootDir=self.rootDir_ )

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
                                                            working directory that should immediate be cd'ed to.

                                                            Likewise, if a script is submitted to an HPC run (non-LOCAL) and requests automatic
                                                            post-processing, this will always assume failure unless the <KEY PHRASE> is at the end
                                                            of the logfile. Thus, scripts running in this mode should assume the same and only output
                                                            success <KEY PHRASE> when completing successfully AT THE VERY END AS THE LAST LINE.
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
  parser.add_argument( 
                      "-g", "--global",
                      dest="globalPrefix",
                      help="Global prefix to name step submission names, added as <PREFIX>.<rest of name>",
                      type=str,
                      default=None
                      )
  parser.add_argument( 
                      "-nf", "--nofatal",
                      dest="nofatal",
                      help="Force continuation of test even if scripts' return code is error",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument( 
                      "-nw", "--nowait",
                      dest="nowait",
                      help="HPC submission - Don't wait for all jobs completion, which is done via a final .results job with dependency on all jobs",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument( 
                      "-np", "--nopost",
                      dest="nopost",
                      help="HPC submission - Don't post-process log files for results using <KEY PHRASE>",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument(
                      "-k", "--key",
                      dest="key",
                      help="Post-processing <KEY PHRASE> regex to signal a script logfile passed successfully. Assumed failed if not last line of script logfile. (default : \"%(default)s\")",
                      default="TEST ((?:\w+|[.-])+) PASS",
                      type=str
                      )

  return parser


class Options(object):
  """Empty namespace"""
  pass

def main() :
  parser  = getOptionsParser()
  options = Options()
  parser.parse_args( namespace=options )
  so.LABEL_LENGTH = options.labelLength

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
  testDir = os.path.dirname( options.testsConfig )
  root  = os.path.abspath( testDir if testDir else "."  + "/" + options.dirOffset )
  print( "Root directory is : {0}".format( root ) )

  # Construct simplified name 
  basename = os.path.splitext( os.path.basename( options.testsConfig ) )[0]

  testSuite = Suite( 
                    basename,
                    json.load( fp ),
                    opts,
                    options,
                    parent=options.globalPrefix,
                    rootDir=root
                    )

  testSuite.run( options.test )

if __name__ == '__main__' :
  main()
