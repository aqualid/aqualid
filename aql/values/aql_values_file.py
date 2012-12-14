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

__all__ = (
  'ValuesFile',
  'eventFileValuesCyclicDependencyValue', 'eventFileValuesDependencyValueHasUnknownValue',
)

import threading

from aql.utils import DataFile, FileLock, eventWarning, logWarning

from .aql_values_xash import ValuesXash
from .aql_value import NoContent
from .aql_depends_value import DependsValue, DependsKeyContent, DependsValueContent
from .aql_value_pickler import ValuePickler

#//===========================================================================//

@eventWarning
def   eventFileValuesCyclicDependencyValue( value ):
  logWarning("Internal error: Cyclic dependency value: %s" % value )

#//===========================================================================//

@eventWarning
def   eventFileValuesDependencyValueHasUnknownValue( dep_value, value ):
  logWarning("Internal error: Dependency value: '%s' has unknown value: '%s'" % (dep_value, value) )

#//===========================================================================//

def _sortDepends( dep_sort_data ):
  
  all_keys = set( dep_sort_data )
  
  for key, value_keys in dep_sort_data.items():
    value_keys[1] &= all_keys
  
  sorted_deps = []
  
  added_keys = set()
  
  while True:
    tmp_dep_sort_data = {}
    
    for key, value_keys in dep_sort_data.items():
      value, dep_keys = value_keys
      if dep_keys:
        tmp_dep_sort_data[ key ] = value_keys
      else:
        sorted_deps.append( value )
        added_keys.add( key )
    
    if not added_keys:
      break
    
    dep_sort_data = tmp_dep_sort_data
    
    for key, value_keys in dep_sort_data.items():
      value_keys[1] -= added_keys
    
    added_keys.clear()
  
  for key, value_keys in dep_sort_data.items():
    value = value_keys[0]
    value = DependsValue( value.name, None )
    sorted_deps.append( value )
    eventFileValuesCyclicDependencyValue( value )
  
  return sorted_deps

#//===========================================================================//

class ValuesFile (object):
  
  __slots__ = (
    'data_file',
    'xash',
    'pickler',
    'lock' ,
    'file_lock',
    'loads',
    'dumps')
  
  #//---------------------------------------------------------------------------//
  
  def   __makeDependsKey( self, dep_value ):
    
    value_keys = DependsKeyContent()
    value_keys_append = value_keys.add
    
    find_value = self.xash.find
    for value in dep_value.content:
      key = find_value( value )[0]
      if key is None:
        eventFileValuesDependencyValueHasUnknownValue( dep_value, value )
        return DependsValue( dep_value.name )
      
      value_keys_append( key )
    
    return DependsValue( dep_value.name, value_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   __makeDepends( self, kvalue, kvalue_key ):
    
    values = []
    values_append = values.append
    
    get_value = self.xash.__getitem__
    
    try:
      keys = kvalue.content
      if kvalue_key in keys: # cyslic dependency
        return DependsValue( kvalue.name )
      
      for key in keys:
        v = get_value( key )
        if isinstance( v, DependsValue ):
          v = self.__makeDepends( v, kvalue_key )
          if isinstance( v.content, NoContent ):
            return DependsValue( kvalue.name )
        
        values_append( v )
    except KeyError as e:
      return DependsValue( kvalue.name )
    
    return DependsValue( kvalue.name, values )
  
  #//---------------------------------------------------------------------------//
  
  @staticmethod
  def   __sortValues( values ):
    
    sorted_values = []
    
    dep_values = {}
    
    for value in values:
      if isinstance(value, DependsValue ):
        try:
          dep_values[ id(value) ] = [value, set(map(id, value.content))]
        except TypeError:
          sorted_values.append( value )
      else:
        sorted_values.append( value )
    
    return sorted_values, _sortDepends( dep_values )
  
  #//---------------------------------------------------------------------------//
  
  def   __init__( self, filename ):
    self.xash = ValuesXash()
    self.data_file = None
    self.pickler = ValuePickler()
    self.loads = self.pickler.loads
    self.dumps = self.pickler.dumps
    self.lock = threading.Lock()
    self.open( filename )
  
  #//---------------------------------------------------------------------------//
  
  def   open( self, filename ):
    
    invalid_keys = []
    
    with self.lock:
      self.file_lock = FileLock( filename )
      
      with self.file_lock.writeLock():
        data_file = DataFile( filename )
        self.data_file = data_file
        
        xash = self.xash
        loads = self.loads
        for key, data in data_file:
          try:
            xash[ key ] = loads( data )
          except ValueError:
            invalid_keys.append( key )
        
        data_file.remove( invalid_keys )
  
  #//---------------------------------------------------------------------------//
  
  def   __update( self ):
    
    xash = self.xash
    data_file = self.data_file
    
    added_keys, deleted_keys = data_file.update()
    
    #//-------------------------------------------------------//
    
    for del_key in deleted_keys:
      del xash[ del_key ]
    
    invalid_keys = []
    
    loads = self.loads
    for key in added_keys:
      try:
        xash[ key ] = loads( data_file[ key ] )
      except ValueError:
        invalid_keys.append( key )
    
    data_file.remove( invalid_keys )
    
  #//---------------------------------------------------------------------------//
  
  def   close( self ):
    if self.data_file is not None:
      self.data_file.close()
      self.data_file = None
    
    self.xash.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   findValues( self, values ):
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
      
      out_values = []
      
      find = self.xash.find
      for value in values:
        key, val = find( value )
        if val is None:
          val = type(value)( value.name, None )
        else:
          if isinstance( val, DependsValue ):
            val = self.__makeDepends( val, key )
          else:
            val = val.copy()
        
        out_values.append( val )
      
      return out_values
  
  #//---------------------------------------------------------------------------//
  
  def   __addValue( self, value ):
    
    xash = self.xash
    
    key, val = xash.find( value )
    if val is not None:
      if value.content != val.content:
        data = self.dumps( value )
        new_key = self.data_file.replace( key, data )
        xash[ new_key ] = value
    else:
      data = self.dumps( value )
      key = self.data_file.append( data )
      xash[ key ] = value
  
  #//---------------------------------------------------------------------------//
  
  def   addValues( self, values ):
    values, dep_values = self.__sortValues( values )
    
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
        
        for value in values:
          self.__addValue( value.copy() )
        
        for dep_value in dep_values:
          value = self.__makeDependsKey( dep_value )
          self.__addValue( value )
  
  #//---------------------------------------------------------------------------//
  
  def   clear(self):
    with self.lock:
      with self.file_lock.writeLock():
        if self.data_file is not None:
          self.data_file.clear()
      
      self.xash.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   selfTest(self):
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
      
        if self.data_file is not None:
          self.data_file.selfTest()
        
        self.xash.selfTest()