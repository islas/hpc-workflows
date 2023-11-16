#!/usr/bin/env python3

import json
import sys
import os
import inspect

def dumpFile( filename, bannerMsg="", banner="!" * 80 ) :
  print( "\nOpening logfile {0}".format( filename ) )
  print( "{msg}\n{banner}".format( msg=bannerMsg, banner=banner ) )
  with open( filename, 'r') as f:
    print( f.read() )
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


masterLog = sys.argv[1]
fp = open( masterLog )
logs = json.load( fp )

metadata = logs.pop( "metadata", None )
metadata["rel_exec"]="<location to hpc-workflows/.ci/runner.py>"
if len(sys.argv) == 3 :
  metadata["rel_exec"] = sys.argv[2]

print( "Finding tests that failed..." )
for test, testlog in logs.items() :
  if not testlog["success"] :
    print( "\n".join([( "#" * 80 )]*3 ) )
    print( "Test {test} failed, printing stdout".format( test=test ) )
    dumpFile( testlog["stdout"], bannerMsg="STDOUT FOR TEST {test}".format( test=test ), banner="\n".join([( "!#!#" * 20 )]*2) )

    print( "Finding logs for steps that failed..." )
    for step, steplog in testlog["steps"].items() :
      if not steplog["success"] :
        print( "Step {step} failed, printing stdout".format( step=step ) )
        dumpFile( steplog["logfile"], bannerMsg="STDOUT FOR STEP {step}".format( step=step ) )

    print( "\n".join([( "#" * 80 )]*3 ) )

print( "\n", flush=True, end="" )

hereThereBeLogs = "^^ !!! ALL LOG FILES ARE PRINTED TO SCREEN ABOVE FOR REFERENCE !!! ^^"
refLogs  = getLogsPrintedStr( logs, os.path.abspath( masterLog ) )
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