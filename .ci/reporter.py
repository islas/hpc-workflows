#!/usr/bin/env python3

import json
import sys
import os
import inspect
import argparse
from enum import Enum

class OutputType( Enum ):
  STANDARD   = "STANDARD"
  GITHUB     = "GITHUB"

  def __str__( self ) :
    return self.value


def dumpFile( filename, errorLabel, success=False, bannerMsg="", banner="!" * 80 ) :
  print( "\nOpening logfile {0}".format( filename ) )
  print( "{msg}\n{banner}".format( msg=bannerMsg, banner=banner ) )
  with open( filename, 'r') as f:
    current = next( f, None )
    last    = None
    for line in f.readlines() :
      print( current, end="" )
      current = line
    # last line
    if current is not None and not success :
      print( errorLabel.format( title=filename, message=current )  )
    else :
      print( current )
      
  print( banner )
  print( "\nClosing logfile {0}".format( filename ) )

def getLogsPrintedStr( masterDict, masterLog ) :
  indent = "  "
  outputFormat = "{desc:=<32}=> {file}\n"

  output = outputFormat.format( desc="master log [developers only]", file=masterLog )
  for test, testlog in masterDict.items() :
    if not testlog["success"] :
      output += outputFormat.format( desc=indent * 1 + "{0} stdout ".format( test ), file=testlog["stdout"] )
      for step, steplog in testlog["steps"].items() :
        if not steplog["success"] :
          output += outputFormat.format( desc=indent * 2 + "{0} stdout ".format( step ), file=steplog["logfile"] )

  return output

def getSummaryPrintedStr( masterDict, metadata ) :
  indent = "  "
  outputFormat = "{name:<24} {reason:<40}\n"
  cmdFormat    = "{runner} {file} -t {test} -d {offset} -s LOCAL"
  output = "SUMMARY OF TEST FAILURES\n" + outputFormat.format( name="NAME", reason="REASON" )
  for test, testlog in masterDict.items() :
    if not testlog["success"] :
      testCmd = cmdFormat.format(
                                  runner=metadata["rel_exec"],
                                  file=metadata["rel_file"],
                                  test=test,
                                  offset=metadata["rel_offset"]
                                  )
      output += outputFormat.format( name=test, reason=testlog[ "line" ] ) + "[TO REPRODUCE LOCALLY] : " + testCmd + "\n"
      for step, steplog in testlog["steps"].items() :
        if not steplog["success"] :
          output += outputFormat.format( name=indent * 1 + step, reason=steplog[ "line" ] )

  return output



def getOptionsParser():
  parser = argparse.ArgumentParser( 
                                    description="Outputs summary and logs for failed tests",
                                  )

  parser.add_argument( 
                      "masterLog",
                      help="Master logfile output from runner.py",
                      type=str,
                      default=""
                      )
  # parser.add_argument( 
  #                     "-t", "--tests",
  #                     help="Test names matching respective JSON test name to run",
  #                     dest="tests",
  #                     type=str,
  #                     nargs="+",
  #                     default=[]
  #                     )
  parser.add_argument( 
                      "-o", "--outputType",
                      dest="outputType",
                      help="Set the output type style for enhanced readability",
                      type=OutputType,
                      choices=list( OutputType ),
                      default=OutputType.STANDARD
                      )
  parser.add_argument( 
                      "-e", "--exec",
                      dest="exec",
                      help="Exec to use when outputting instructions on reproduction",
                      type=str,
                      default="<location to hpc-workflows/.ci/runner.py>"
                      )
  parser.add_argument( 
                      "-f", "--failedStepsOnly",
                      dest="failedStepsOnly",
                      help="Only output the failed steps instead of the whole test",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument( 
                      "-s", "--summaryOnly",
                      dest="summaryOnly",
                      help="Only output the summary and no logs",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  return parser

class Options(object):
  """Empty namespace"""
  pass

def main() :
  parser  = getOptionsParser()
  options = Options()
  parser.parse_args( namespace=options )

  fp = open( options.masterLog )
  logs = json.load( fp )

  metadata = logs.pop( "metadata", None )
  metadata["rel_exec"] = options.exec 

  startGroup  = None
  stopGroup   = None
  noticeLabel = None
  errorLabel  = None

  if options.outputType == OutputType.STANDARD :
    startGroup  = ""
    stopGroup   = ""
    noticeLabel = ""
    errorLabel  = "{message}"
  elif options.outputType == OutputType.GITHUB :
    startGroup  = "::group::{title}"
    stopGroup   = "::endgroup"
    noticeLabel = "::notice title={title}::{message}"
    errorLabel  = "::error title={title}::{message}"
  

  if not options.summaryOnly :
    print( "Finding tests that failed..." )
    for test, testlog in logs.items() :
      if not testlog["success"] :
        testTitle = "STDOUT FOR TEST {test}".format( test=test )
        print( startGroup.format( title=testTitle ) )
        print( "\n".join([( "#" * 80 )]*3 ) )
        print( "Test {test} failed, printing stdout".format( test=test ) )
        dumpFile( testlog["stdout"], errorLabel, bannerMsg=testTitle, banner="\n".join([( "!#!#" * 20 )]*2 ) )

        print( "Finding logs for steps that failed..." )
        for step, steplog in testlog["steps"].items() :
          stepTitle = "STDOUT FOR STEP {step}".format( step=step )
          if not options.failedStepsOnly or not steplog["success"] :
            print( noticeLabel.format( title=steplog["logfile"], message=stepTitle ) )
            if not steplog["success"] :
              print( "Step {step} failed, printing stdout".format( step=step ) )
            dumpFile( steplog["logfile"], errorLabel, steplog["success"], bannerMsg=stepTitle )

        print( "\n".join([( "#" * 80 )]*3 ) )
        print( stopGroup )

    print( "\n", flush=True, end="" )
  
    hereThereBeLogs = "^^ !!! ALL LOG FILES ARE PRINTED TO SCREEN ABOVE FOR REFERENCE !!! ^^"
    refLogs  = getLogsPrintedStr( logs, os.path.abspath( options.masterLog ) )
    howToUse = inspect.cleandoc(
                hereThereBeLogs +
              """
                    To find when a logfile is printed search for (remove single quotes) :
                    'Opening logfile <logfile>'
                    OR
                    'Closing logfile <logfile>'
                    Replacing <logfile> with the logfile you wish to see
              """ )
    print( "~ How to use brief ~\n{help}\n\nOr refer to log files : \n{reflogs}\n{addendum}\n".format(
                                                                                                    help=howToUse,
                                                                                                    reflogs=refLogs,
                                                                                                    addendum=hereThereBeLogs
                                                                                                    ),
      flush=True )

  # Now do executive summary
  print( getSummaryPrintedStr( logs, metadata ) )

  note = inspect.cleandoc(
                          """
                              Note: HPC users should use '-s LOCAL' in reproduce command with caution
                                    as it will run directly where you are, consider using an interactive node
                          """
                          )
  print( note )
  # Force wait for stdout to be finished
  try:
    os.fsync( sys.stdout.fileno() )
  except:
    pass

  print( "FAILURE!" )
  # Exit with bad status so people know where to look since that might be 
  # an issue as this will look "successful"
  exit( 1 )

if __name__ == '__main__' :
  main()
