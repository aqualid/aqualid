import io
try:
  import cPickle as pickle
except ImportError:
  import pickle

#//===========================================================================//

_known_types = {}

#//===========================================================================//

class   ValuePickler (object):
  
  __slots__ = ( 'pickler', 'unpickler', 'buffer' )
  
  def   __init__( self ):
    
    buffer = io.BytesIO()
    
    pickler = pickle.Pickler( buffer, protocol = pickle.HIGHEST_PROTOCOL )
    pickler.fast = True
    
    unpickler = pickle.Unpickler( buffer )
    
    pickler.persistent_id = self.persistent_id
    unpickler.persistent_load = self.persistent_load
    
    self.pickler = pickler
    self.unpickler = unpickler
    self.buffer = buffer
  
  #//-------------------------------------------------------//
  @staticmethod
  def persistent_id( value, known_types = _known_types ):
    
    value_type = type(value)
    type_name = value_type.__name__
    if type_name in known_types:
      return (type_name, value.__getnewargs__())
    else:
      return None
  
  #//-------------------------------------------------------//
  @staticmethod
  def persistent_load( pid, known_types = _known_types ):
    
    type_name, new_args = pid
    
    try:
      value_type = known_types[ type_name ]
      return value_type.__new__(value_type, *new_args )
    
    except KeyError:
      raise pickle.UnpicklingError("Unsupported persistent object")
  
  #//-------------------------------------------------------//
  
  def   dumps( self, value ):
    buffer = self.buffer
    buffer.seek(0)
    buffer.truncate(0)
    self.pickler.dump( value )
    
    return buffer.getvalue()
 
  #//-------------------------------------------------------//
  
  def   loads( self, bytes_object ):
    buffer = self.buffer
    buffer.seek(0)
    buffer.truncate(0)
    buffer.write( bytes_object )
    buffer.seek(0)
    
    return self.unpickler.load()

#//===========================================================================//

def  pickleable( value_class, known_types = _known_types ):
  if type(value_class) is type:
    known_types[ value_class.__name__ ] = value_class
  
  return value_class

