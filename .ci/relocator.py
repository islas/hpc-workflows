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

oldlocation, mastername  = os.path.split( masterLog )

files = [ masterLog ]
for test in logs.values() :
  files.append( test["logfile"] )
  files.append( test["stdout"] )
  # step files are user stdout so  they should not have any changes
  for step in test["steps"].values() :
    files.append( step["logfile"] )

common = os.path.commonpath( files )
replacements = { logfile : logfile.replace( common, relocation ) for logfile in files }

for oldloc, newloc in replacements.items() :
  # change refs in new location, using copy for safety
  os.makedirs( os.path.dirname( newloc ), exist_ok=True )
  newlocation = shutil.copy( oldloc, newloc )
  replaceReferences( newlocation, replacements )
  
  
 



