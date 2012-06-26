#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


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

