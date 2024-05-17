# https://stackoverflow.com/a/3233356
import collections.abc

LABEL_LENGTH = 12

# Update mapping dest with source
def recursiveUpdate( dest, source ):
  for k, v in source.items():
    if isinstance( v, collections.abc.Mapping ):
      dest[k] = recursiveUpdate( dest.get( k, {} ), v )
    else:
      dest[k] = v
  return dest

