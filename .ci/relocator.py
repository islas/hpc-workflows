#!/usr/bin/env python3

import json
import sys
import os
import shutil
import inspect

def replaceReferences( filename, refs ) :
  with open( filename, "r" ) as fp :
    contents = fp.read()
  
  for ref, rep in refs.items() : 
    contents = contents.replace( ref, rep )

  with open( filename, "w" ) as fp :
    fp.write( contents )


masterLog  = os.path.abspath( sys.argv[1] )
relocation = os.path.abspath( sys.argv[2] )

fp = open( masterLog )
logs = json.load( fp )
fp.close()

metadata = logs.pop( "metadata", None )

print( "Copying {0} and all associated logs to {1}...".format( masterLog, relocation ) )
if not os.path.exists( relocation ):
  os.makedirs( relocation )

# logs are always placed together, so we only need one name
oldlocation, mastername  = os.path.split( masterLog )

replacements = { masterLog.replace( oldlocation, relocation ) : masterLog }
files = [ masterLog ]
for test in logs.values() :
  replacements = { test["logfile"].replace( oldlocation, relocation ) : test["logfile"] }
  replacements = { test["stdout"].replace( oldlocation, relocation ) : test["stdout"] }

  files.append( test["logfile"] )
  files.append( test["stdout"] )
  # step files are user stdout so  they should not have any changes
  for step in test["steps"].values() :
    replacements = { step["logfile"].replace( oldlocation, relocation ) : step["logfile"]  }
    files.append( step["logfile"] )


for logfile in files :
  # change refs in new location, using copy for safety
  newlocation = shutil.copy( logfile, relocation )
  replaceReferences( newlocation, replacements )
  
  
 



