#
# Copyright (c) 2011-2014 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = (
  'ValuesFile',
)

from aql.util_types import AqlException 
from aql.utils import DataFile, FileLock

from .aql_value_pickler import ValuePickler

#//===========================================================================//

class   ErrorValuesFileUnknownValue( AqlException ):
  def   __init__( self, value ):
    msg = "Unknown value: %s" % (value, )
    super(type(self), self).__init__( msg )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class ValuesFile (object):
  
  __slots__ = (
    
    'data_file',
    'file_lock',
    'key2value',
    'value2key',
    'pickler',
  )
  
  #//---------------------------------------------------------------------------//
  
  def   __getValueByKey(self, key ):
    return self.key2value.get(key, None )
  
  #//---------------------------------------------------------------------------//
  
  def   __getKeyByValueId(self, value_id ):
    return self.value2key.get( value_id, None )
  
  #//---------------------------------------------------------------------------//
  
  def   __addValueToCache(self, key, value_id, value ):
    self.value2key[ value_id ] = key
    self.key2value[ key ] = value
  
  #//---------------------------------------------------------------------------//
  
  def   __updateValueInCache(self, old_key, new_key, value_id, value ):
    self.value2key[ value_id ] = new_key
    del self.key2value[ old_key ]
    self.key2value[ new_key ] = value
  
  #//---------------------------------------------------------------------------//
  
  def   __clearCache(self ):
    self.value2key.clear()
    self.key2value.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   __init__( self, filename, force = False ):
    self.key2value = {}
    self.value2key = {}
    self.data_file = None
    self.pickler = ValuePickler()
    self.open( filename, force = force )
  
  #//---------------------------------------------------------------------------//
  
  def   __enter__(self):
    return self
  
  #//-------------------------------------------------------//

  #noinspection PyUnusedLocal
  def   __exit__(self, exc_type, exc_value, traceback):
    self.close()
  
  #//---------------------------------------------------------------------------//
  
  def   open( self, filename, force = False ):
    
    invalid_keys = []
    
    self.file_lock = FileLock( filename )
    self.file_lock.writeLock( wait = False, force = force )
    
    data_file = DataFile( filename, force = force )
    
    self.data_file = data_file
    
    loads = self.pickler.loads
    for key, data in data_file:
      try:
        value = loads( data )
      except Exception:
        invalid_keys.append( key )
      else:
        value_id = value.valueId()
        self.__addValueToCache( key, value_id, value )
      
    data_file.remove( invalid_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   close( self ):
    
    if self.data_file is not None:
      self.data_file.close()
      self.data_file = None
    
    self.file_lock.releaseLock()
    
    self.__clearCache()
  
  #//---------------------------------------------------------------------------//
  
  def   findValue( self, value ):
    key = self.__getKeyByValueId( value.valueId() )
    if key is None:
      return None
    
    return self.__getValueByKey( key )
  
  #//---------------------------------------------------------------------------//
  
  def   addValue( self, value ):
    
    reserve = not value.IS_SIZE_FIXED
    
    value_id = value.valueId()
    key = self.__getKeyByValueId( value_id )
    
    if key is None:
      data = self.pickler.dumps( value )
      key = self.data_file.append( data, reserve )
      
      self.__addValueToCache( key, value_id, value )
    
    else:
      val = self.__getValueByKey( key )
      
      if value != val:
        data = self.pickler.dumps( value )
        new_key = self.data_file.replace( key, data, reserve )
        
        self.__updateValueInCache(key, new_key, value_id, value )
        
        return new_key
    
    return key
  
  #//---------------------------------------------------------------------------//
  
  def   replaceValue(self, key, value ):
    reserve = not value.IS_SIZE_FIXED
    
    data = self.pickler.dumps( value )
    new_key = self.data_file.replace( key, data, reserve )
    
    self.__updateValueInCache(key, new_key, value.valueId(), value )
  
  #//---------------------------------------------------------------------------//
  
  def   findValues(self, values ):
    return tuple( map( self.findValue, values ) )
  
  #//---------------------------------------------------------------------------//
  
  def   addValues( self, values ):
    return tuple( map( self.addValue, values ) )
  
  #//---------------------------------------------------------------------------//
  
  def   removeValues( self, values ):
    remove_keys = []
    
    for value in values:
      
      key = self.__getKeyByValueId( value.valueId() )
      
      if key is not None:
        remove_keys.append( key )
    
    self.data_file.remove( remove_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   getKeys( self, values ):
    keys = []
    
    for value in values:
      key = self.__getKeyByValueId( value.valueId() )
      
      if key is None:
        raise ErrorValuesFileUnknownValue( value )
      
      keys.append( key )
    
    return keys
  
  #//---------------------------------------------------------------------------//
  
  def   getValues( self, keys ):
    values = []
    
    for key in keys:
      value = self.__getValueByKey( key )
      
      if value is None:
        return None
      
      values.append( value )
    
    return values
  
  #//---------------------------------------------------------------------------//
  
  def   clear(self):
    if self.data_file is not None:
      self.data_file.clear()
    
    self.__clearCache()
  
  #//---------------------------------------------------------------------------//
  
  def   selfTest(self):
    if self.data_file is not None:
      self.data_file.selfTest()
    
    for key, value in self.key2value.items():
      value_id = value.valueId()  
      
      if value_id not in self.value2key:
        raise AssertionError("value (%s) not in self.value2key" % (value_id,))
        
      if key != self.value2key[ value_id ]:
        raise AssertionError("key(%s) != self.value2key[ value_id(%) ](%s) % (key, value_id, self.value2key[ value_id ])" )
    
    size = len(self.key2value)
    
    if size != len(self.value2key):
      raise AssertionError( "size(%s) != len(self.value2key)(%s)" % (size, len(self.value2key)) )
    
    data_file_size = len(self.data_file)
    if data_file_size != size:
      raise AssertionError("data_file_size(%s) != size(%s)" % (data_file_size, size))
