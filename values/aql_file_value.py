
import os
import hashlib
import datetime

from aql_value import Value, NoContent
from aql_value_pickler import pickleable

#//===========================================================================//

@pickleable
class   FileContentChecksum (object):
  
  __slots__ = ( 'size', 'checksum' )
  
  def   __new__( cls, path = None, size = None, checksum = None ):
    
    if (size is not None) and (checksum is not None):
      self = super(FileContentChecksum,cls).__new__(cls)
      self.size     = size
      self.checksum = checksum
      return self
    
    if path is None:
      return NoContent()
    
    if isinstance( path, FileContentChecksum ):
      return path
    
    try:
      checksum = hashlib.md5()
      size = 0
      
      with open( path, mode = 'rb' ) as f:
        read = f.read
        checksum_update = checksum.update
        while True:
          chunk = read( 262144 )
          if not chunk:
            break
          size += len(chunk)
          checksum_update( chunk )
      
      self = super(FileContentChecksum,cls).__new__(cls)
      
      self.size     = size
      self.checksum = checksum.digest()
      
      return self
    
    except (OSError, IOError):
      return NoContent()
  
  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):
    return (type(self) == type(other)) and \
           (self.size == other.size) and \
           (self.checksum == other.checksum)
  
  def   __ne__( self, other ):        return not self.__eq__( other )
  def   __getnewargs__(self):         return ( None, self.size, self.checksum )
  def   __getstate__(self):           return {}
  def   __setstate__(self,state):     pass
  def   __str__( self ):              return str(self.checksum)

#//===========================================================================//

@pickleable
class   FileContentTimeStamp (object):
  
  __slots__ = ( 'size', 'modify_time' )
  
  def   __new__( cls, path = None, size = None, modify_time = None ):
    
    if (size is not None) and (modify_time is not None):
      self = super(FileContentTimeStamp,cls).__new__(cls)
      self.size = size
      self.modify_time = modify_time
      return self
    
    if path is None:
      return NoContent()
    
    if isinstance( path, FileContentTimeStamp ):
      return path
    
    try:
      stat = os.stat( path )
      
      self = super(FileContentTimeStamp,cls).__new__(cls)
      
      self.size = stat.st_size
      self.modify_time = stat.st_mtime
      
      return self
    
    except OSError:
        return NoContent()

  #//-------------------------------------------------------//
  
  def   __eq__( self, other ):        return type(self) == type(other) and (self.size == other.size) and (self.modify_time == other.modify_time)
  def   __ne__( self, other ):        return not self.__eq__( other )
  
  def   __getnewargs__(self):         return ( None, self.size, self.modify_time )
  def   __getstate__(self):           return {}
  def   __setstate__(self,state):     pass
  def   __str__( self ):              return str( datetime.datetime.fromtimestamp( self.modify_time ) )
  

#//===========================================================================//

@pickleable
class   FileName (str):
  def     __new__(cls, path = None, full_path = None ):
    if isinstance( path, FileName ):
      return path
    
    if full_path is None:
      if path is None:
        return super(FileName,cls).__new__(cls)
    
      full_path = os.path.normcase( os.path.normpath( os.path.abspath( str(path) ) ) )
    
    return super(FileName,cls).__new__(cls, full_path)
  
  #//-------------------------------------------------------//
  
  def     __getnewargs__(self):
    return (None, super(FileName,self).__getnewargs__()[0] )

#//===========================================================================//

@pickleable
class   FileValue (Value):
  
  def   __new__( cls, name, content = NotImplemented ):
    
    if isinstance( name, FileValue ):
      other = name
      name = other.name
    
      if content is NotImplemented:
        content = type(other.content)( name )
    else:
      name = FileName( name )
    
    if content is NotImplemented:
      content = FileContentChecksum( name )
    elif type(content) is type:
      content = content( name )
    
    return super(FileValue, cls).__new__( cls, name, content )
  
  #//-------------------------------------------------------//
  
  def   actual( self ):
    content = self.content
    return content == type(content)( self.name )


#//===========================================================================//
