# https://stackoverflow.com/a/3233356
import collections.abc
from enum import Enum
LABEL_LENGTH = 32

class SubmissionType( Enum ):
  PBS   = "PBS"
  SLURM = "SLURM"
  LOCAL = "LOCAL"

  def __str__( self ) :
    return self.value

# Update mapping dest with source
def recursiveUpdate( dest, source ):
  for k, v in source.items():
    if isinstance( v, collections.abc.Mapping ):
      dest[k] = recursiveUpdate( dest.get( k, {} ), v )
    else:
      dest[k] = v
  return dest

# An exception type to handle parse errors
class SubmitParseException( Exception ) :
  def __init__( self, msg ) :
    super( Exception, self ).__init__( msg )

# An exception type to handle parse errors parents
class SubmitParentParseException( Exception ) :
  def __init__( self, msg ) :
    super( Exception, self ).__init__( msg )

