#!/usr/bin/env python3

import json
import sys
import inspect

def dumpFile( filename, bannerMsg="", banner="!" * 80 ) :
  print( "\nOpening logfile {0}".format( filename ) )
  print( "{msg}\n{banner}".format( msg=bannerMsg, banner=banner ) )
  with open( filename, 'r') as f:
    print( f.read() )
  print( banner )

def getLogsPrintedStr( masterDict, masterLog ) :
  indent = "  "
  outputFormat = "{desc:=<32}=> {file}\n"

  output = outputFormat.format( desc="master log ", file=masterLog )
  for test, testlog in masterDict.items() :
    if not testlog["success"] :
      output += outputFormat.format( desc=indent * 1 + "{0} stdout ".format( test ), file=testlog["message"] )
      for step, steplog in testlog["steps"].items() :
        if not steplog["success"] :
          output += outputFormat.format( desc=indent * 2 + "{0} stdout ".format( step ), file=steplog["logfile"] )
  
  return output


masterLog = sys.argv[1]
fp = open( masterLog )
logs = json.load( fp )
print( "Finding tests that failed..." )
for test, testlog in logs.items() :
  if not testlog["success"] :
    print( "\n".join([( "#" * 80 )]*3 ) )
    print( "Test {test} failed, printing stdout".format( test=test ) )
    dumpFile( testlog["message"], bannerMsg="STDOUT FOR TEST {test}".format( test=test ), banner="\n".join([( "!#!#" * 20 )]*2) )

    print( "Finding logs for steps that failed..." )
    for step, steplog in testlog["steps"].items() :
      if not steplog["success"] :
        print( "Step {step} failed, printing stdout".format( step=step ) )
        dumpFile( steplog["logfile"], bannerMsg="STDOUT FOR STEP {step}".format( step=step ) )

    print( "\n".join([( "#" * 80 )]*3 ) )

# Exit with bad status so people know where to look since that might be 
# an issue as this will look "successful"
refLogs  = getLogsPrintedStr( logs, masterLog )
howToUse = inspect.cleandoc(
           """~ How to use brief ~
                Search for (remove single quotes): 
                  * '!!!!!!!!!!!' (up to 80) to find beginning and end of a step
                  * '###########' (up to 80) to find beginning of a test
                  * '!!!!!!!!!! ERROR ERROR ERROR !!!!!!!!!!' to find test infrastructure reason for failure
           """ )

raise Exception( "Test did not pass, refer to the printed logs above using :\n{help}\n\nOr refer to log files : \n{reflogs}".format( help=howToUse, reflogs=refLogs ) )