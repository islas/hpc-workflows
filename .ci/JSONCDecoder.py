# https://stackoverflow.com/a/72168909
import json
from typing import Any
class JSONCDecoder( json.JSONDecoder ):
  def __init__( self, **kw ) :
    super().__init__( **kw )
  
  def decode( self, s : str ) -> Any :
    # Sanitize the input string for leading // comments ONLY and replace with
    # blank line so that line numbers are preserved
    s = '\n'.join( l if not l.lstrip().startswith( "//" ) else "" for l in s.split( '\n' ) )
    return super().decode( s )
