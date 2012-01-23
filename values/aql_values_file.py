import threading

from aql_logging import logWarning
from aql_values_xash import ValuesXash
from aql_lock_file import FileLock
from aql_data_file import DataFile
from aql_value import NoContent
from aql_depends_value import DependsValue, DependsKeyContent
from aql_value_pickler import ValuePickler

#//===========================================================================//

def _sortDepends( dep_sort_data ):
  
  all_keys = set( dep_sort_data )
  
  for key, value_keys in dep_sort_data.items():
    value_keys[1] &= all_keys
  
  sorted_deps = []
  
  added_keys = set()
  
  while True:
    for key, value_keys in list(dep_sort_data.items()):
      value, dep_keys = value_keys
      if not dep_keys:
        del dep_sort_data[ key ]
        added_keys.add( key )
        sorted_deps.append( (key, value ) )
    
    if not added_keys:
      break
    
    for key, value_keys in dep_sort_data.items():
      value_keys[1] -= added_keys
    
    added_keys.clear()
  
  for key, value_keys in dep_sort_data.items():
    value = value_keys[0]
    value = DependsValue( value.name, None )
    sorted_deps.append( (key, value) )
    logWarning("Cyclic dependency value: %s" % value )
  
  return sorted_deps

#//===========================================================================//

class DependsKeys (object):
  
  __slots__ = ('values', 'deps')
  
  #//-------------------------------------------------------//
  
  def   __init__(self):
    self.values = {}
    self.deps = {}
  
  #//-------------------------------------------------------//
  
  def   __setitem__(self, dep_key, value_keys ):
    if not value_keys:
      raise AssertionError("value_keys is empty")
    
    self.deps[ dep_key ] = value_keys
    values_setdefault = self.values.setdefault
    for value_key in value_keys:
      values_setdefault( value_key , set() ).add( dep_key )
  
  #//-------------------------------------------------------//
  
  def   __getitem__(self, dep_key ):
    return self.deps[ dep_key ]
  
  #//-------------------------------------------------------//
  
  def   __iter__(self):
    return iter(self.deps)
  
  #//-------------------------------------------------------//
  
  def   items(self):
    return self.deps.items()
  
  #//-------------------------------------------------------//
  
  def   __contains__(self, key):
    return key in self.deps
  
  #//-------------------------------------------------------//
  
  def   clear(self):
    self.deps.clear()
    self.values.clear()
  
  #//-------------------------------------------------------//
  
  def   remove( self, key ):
    removed_deps = set()
    removing_keys = set([key])
    
    values = self.values
    values_pop = values.pop
    deps_pop = self.deps.pop
    
    while removing_keys:
      key = removing_keys.pop()
      
      try:
        value_keys = deps_pop( key )
        
        for value_key in value_keys:
          try:
            value_deps = values[value_key]
            value_deps.remove( key )
            if not value_deps:
              del values[value_key]
          except KeyError:
            pass
        
      except KeyError:
        pass
      
      try:
        value_deps = values_pop( key )
        removing_keys |= value_deps
        removed_deps.update( value_deps )
      except KeyError:
        pass
    return removed_deps
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    all_keys = set()
    all_value_keys = set()
    
    for key, value_keys in self.deps.items():
      for value_key in value_keys:
        dep_keys = self.values[ value_key ]
        if key not in dep_keys:
          raise AssertionError("dep (%s) is not in value_keys[%s]" % (key, value_key))
        
        all_keys |= dep_keys
      
      all_value_keys |= value_keys
    
    if len(all_keys) != len(self.deps):
      raise AssertionError("len(all_keys) (%s) != len(self.deps) (%s)" % (len(all_keys), len(self.deps)))
    
    if len(all_value_keys) != len(self.values):
      raise AssertionError("len(all_value_keys) (%s) != len(self.values) (%s)" % (len(all_value_keys), len(self.values)))
    
  
#//===========================================================================//

class ValuesFile (object):
  
  __slots__ = (
    'data_file',
    'xash',
    'pickler',
    'lock' ,
    'file_lock',
    'deps',
    'loads',
    'dumps')
  
  #//---------------------------------------------------------------------------//
  
  def   __getKeysOfValues( self, values ):
  
    value_keys = DependsKeyContent()
    value_keys_append = value_keys.add
    
    findValue = self.xash.find
    try:
      for value in values:
        key = findValue( value )[0]
        if key is None:
          logWarning("Value: %s has been not found" % str(value.name))
          return None
        
        value_keys_append( key )
    
    except TypeError:
      return None
    
    return value_keys
  
  #//---------------------------------------------------------------------------//
  
  def   __getValuesByKeys( self, keys ):
    values = []
    values_append = values.append
    
    getValue = self.xash.__getitem__
    
    try:
      for key in keys:
        values_append( getValue( key ) )
    except KeyError:
      return None
    except TypeError:
      return None
    
    return values
  
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
  
  def __restoreDepends( self, dep_values ):
    
    sorted_deps = _sortDepends( dep_values )
    
    xash = self.xash
    
    for key, dep_keys_value in sorted_deps:
      value_keys = dep_keys_value.content
      values = self.__getValuesByKeys( value_keys )
      dep_value = DependsValue( dep_keys_value.name, values )
      
      xash[ key ] = dep_value
      if values:
        self.deps[ key ] = value_keys
  
  #//---------------------------------------------------------------------------//
  
  def   __removedDepends( self, removed_keys ):
    if removed_keys:
      xash = self.xash
      replace = self.data_file.replace
      dumps = self.dumps
      
      for removed_key in removed_keys:
        dep_value = xash.pop( removed_key )
        dep_value = DependsValue( dep_value.name, None )
        new_key = replace( removed_key, dumps( dep_value ) )
        xash[ new_key ] = dep_value
  
  #//---------------------------------------------------------------------------//
  
  def   __init__( self, filename ):
    self.xash = ValuesXash()
    self.deps = DependsKeys()
    self.data_file = None
    self.pickler = ValuePickler()
    self.loads = self.pickler.loads
    self.dumps = self.pickler.dumps
    self.lock = threading.Lock()
    self.open( filename )
  
  #//---------------------------------------------------------------------------//
  
  def   __loadValue( self, key, data, dep_values ):
    
    value = self.loads( data )
    
    if isinstance( value, DependsValue ):
      try:
        dep_values[ key ] = [value, set(value.content)]
      except TypeError:
        self.xash[ key ] = value
    else:
      self.xash[ key ] = value
  
  #//---------------------------------------------------------------------------//
  
  def   open( self, filename ):
    
    with self.lock:
      self.file_lock = FileLock( filename )
      
      with self.file_lock.readLock():
        self.data_file = DataFile( filename )
        
        dep_values = {}
        for key, data in self.data_file:
          self.__loadValue( key, data, dep_values )
        
        self.__restoreDepends( dep_values )
  
  #//---------------------------------------------------------------------------//
  
  def   __update( self ):
    
    xash = self.xash
    data_file = self.data_file
    loads = self.pickler.loads
    
    added_keys, deleted_keys = data_file.update()
    
    #//-------------------------------------------------------//
    
    removed_keys = set()
    deps_remove = self.deps.remove
    for del_key in deleted_keys:
      del xash[ del_key ]
      removed_keys |= deps_remove( del_key )
    
    removed_keys -= deleted_keys
    
    if removed_keys:
      logWarning("DataFile is unsynchronized")
      self.__removedDepends( removed_keys )
    
    #//-------------------------------------------------------//
    
    dep_values = {}
    
    for key in added_keys:
      self.__loadValue( key, data_file[key], dep_values )
    
    self.__restoreDepends( dep_values )
  
  #//---------------------------------------------------------------------------//
  
  def   close( self ):
    if self.data_file is not None:
      self.data_file.close()
      self.data_file = None
    
    self.xash.clear()
    self.deps.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   actual( self, values ):
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
      
      find = self.xash.find
      for value in values:
        val = find( value )[1]
        if val is None:
          return False
        
        if val != value:
          return False
      
      return True
  
  #//---------------------------------------------------------------------------//
  
  def   findValues( self, values ):
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
      
      out_values = []
      
      xash = self.xash
      for value in values:
        val = xash.find( value )[1]
        if val is None:
          val = type(value)( value.name, None )
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
        new_key = self.data_file.replace( key, self.dumps( value ) )
        xash[ new_key ] = value.copy()
        
        removed_keys = self.deps.remove( key )
        self.__removedDepends( removed_keys )
    else:
      key = self.data_file.append( self.dumps( value ) )
      xash[key] = value.copy()
  
  #//---------------------------------------------------------------------------//
  
  def   __addDepValue( self, value ):
    
    xash = self.xash
    deps = self.deps
    
    content_keys = self.__getKeysOfValues( value.content )
    if content_keys is None:
      value = DependsValue( value.name, None )
      dep_value = value
    else:
      dep_value = DependsValue( value.name, content_keys )
      value = value.copy()
    
    key, val = xash.find( value )
    if val is not None:
      
      try:
        old_content_keys = deps[ key ]
      except KeyError:
        old_content_keys = None
      
      if old_content_keys != content_keys:
        data = self.dumps( dep_value )
        
        new_key = self.data_file.replace( key, data )
        xash[ new_key ] = value
        if content_keys:
          deps[ new_key ] = content_keys
        
        removed_keys = deps.remove( key )
        self.__removedDepends( removed_keys )
    
    else:
      data = self.dumps( dep_value )
      key = self.data_file.append( data )
      xash[key] = value
      if content_keys:
        deps[ key ] = content_keys
  
  #//---------------------------------------------------------------------------//
  
  def   addValues( self, values ):
    values, dep_values = self.__sortValues( values )
    
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
        
        for value in values:
          self.__addValue( value )
        
        for id, dep_value in dep_values:
          self.__addDepValue( dep_value )
  
  #//---------------------------------------------------------------------------//
  
  def   clear(self):
    with self.lock:
      with self.file_lock.writeLock():
        if self.data_file is not None:
          self.data_file.clear()
      
      self.xash.clear()
      self.deps.clear()
  
  #//---------------------------------------------------------------------------//
  
  def   selfTest(self):
    with self.lock:
      with self.file_lock.writeLock():
        self.__update()
      
        self.deps.selfTest()
        
        if self.data_file is not None:
          self.data_file.selfTest()
        
        self.xash.selfTest()
        
        #//-------------------------------------------------------//
        
        for dep_key in self.deps:
          dep_value = self.xash[dep_key]
          if not isinstance( dep_value, DependsValue ):
            raise AssertionError("dep_value(%s) is not DependsValue" % (dep_value.name,) )
          
          if len(self.deps[dep_key]) != len(dep_value.content):
            raise AssertionError("len(self.deps[%s])(%s) != len(dep_value.content)(%s)" % (dep_key, len(self.deps[dep_key]), len(dep_value.content)) )
          
          value_keys = self.__getKeysOfValues( dep_value.content )
          
          if self.deps[dep_key] != value_keys:
            raise AssertionError("self.deps[%s])(%s) != value_keys(%s)" % (dep_key, self.deps[dep_key], value_keys) )
        
        #//-------------------------------------------------------//
        
        for key in self.xash:
          value = self.xash[key]
          if isinstance(value, DependsValue):
            if isinstance(value.content, NoContent):
              if key in self.deps:
                raise AssertionError("empty dep value(%s) is in deps" % (value.name,) )
            else:
              if value.content:
                if key not in self.deps:
                  raise AssertionError("dep value(%s) is not in deps" % (value.name,) )
          else:
            if key in self.deps:
              raise AssertionError("value(%s) is in deps" % (value.name,) )

