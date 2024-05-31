#!/usr/bin/env python3

import sys
import json

nbFile = sys.argv[1]
nbInput = open( nbFile, "r" )
nbData = json.load( nbInput )
nbInput.close()


for cell in nbData["cells"] :
  if cell["cell_type"] == "code" and "outputs" in cell and len( cell["outputs"] ) > 1 and cell["outputs"][0]["output_type"] == "stream" :
    # these are all dict entries
    cell["outputs"][0]["text"] = [ badout["text"][0] for badout in cell["outputs"] ]
    
    cell["outputs"] = cell["outputs"][0:1]


nbOutput = open( nbFile, "w" )
nbData = json.dump( nbData, nbOutput, indent=2 )
nbOutput.close()
