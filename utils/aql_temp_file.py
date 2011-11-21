
import os
import tempfile

class Tempfile (object):
    
  __slots__ = ('__handle','name')

  def   __init__(self):
    self.__handle = tempfile.NamedTemporaryFile( mode = 'w+b', delete = False )
    self.name = self.__handle.name

  def   __enter__(self):
    return self

  def   __exit__(self, exc_type, exc_value, traceback):
    self.remove()

  def write( self, buffer ):
    self.__handle.write( buffer )

  def read( self, buffer ):
    self.__handle.read( buffer )

  def seek( self, offset, whence = os.SEEK_SET ):
    self.__handle.seek( offset )

  def tell( self ):
    return self.__handle.tell()

  def flush( self ):
    self.__handle.flush()

  def close( self ):
    self.__handle.close()

  def remove( self ):
    self.__handle.close()
    try:
      os.remove( self.name )
    except OSError:
      pass
    
    return self

