#!/usr/bin/env python3

import json
import sys

def dumpFile( filename, bannerMsg="", banner="!" * 80 ) :
  print( "\n{msg}\n{banner}".format( msg=bannerMsg, banner=banner ) )
  with open( filename, 'r') as f:
    print( f.read() )
  print( banner )

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
raise Exception( "Test did not pass, refer to the above logs" )