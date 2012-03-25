
from aql_utils import toSequence

class   UniqueList (object):
  
  __slots__ = (
    '__values_list',
    '__values_set',
  )
  
  #//-------------------------------------------------------//
  
  def     __new__(cls, values = None ):
    
    self = super(UniqueList, cls).__new__(cls)
    self.__values_list = []
    self.__values_set = set()
    
    self.__addValues( values )
    
    return self
  
  #//-------------------------------------------------------//
  
  def   __addValueFront( self, value ):
    
    values_set = self.__values_set
    values_list = self.__values_list
    
    if value in values_set:
      values_list.remove( value )
    else:
      values_set.add( value )
    
    values_list.insert( 0, value )
  
  #//-------------------------------------------------------//
  
  def   __addValue( self, value ):
    
    values_set = self.__values_set
    values_list = self.__values_list
    
    if value not in values_set:
      values_set.add( value )
      values_list.append( value )
  
  #//-------------------------------------------------------//
  
  def   __addValues( self, values ):
    
    values_set_add = self.__values_set.add
    values_list_append = self.__values_list.append
    values_set_size = self.__values_set.__len__
    values_list_size = self.__values_list.__len__
    
    for value in toSequence( values ):
      values_set_add( value )
      if values_set_size() > values_list_size():
        values_list_append( value )
  
  #//-------------------------------------------------------//
  
  def   __addValuesFront( self, values ):
    
    values_set = self.__values_set
    values_list = self.__values_list
    
    values_set_add = values_set.add
    values_list_append = values_list.append
    values_set_size = values_set.__len__
    values_list_size = values_list.__len__
    values_list_index = values_list.index
    
    pos = 0
    
    for value in toSequence( values ):
      values_set_add( value )
      if values_set_size() == values_list_size():
        i = values_list_index( value )
        if i < pos:
          continue
        
        del values_list[ i ]
      
      values_list.insert( pos, value )
      
      pos += 1
  
  #//-------------------------------------------------------//
  
  def   __removeValue( self, value ):
    
    try:
      self.__values_set.remove( value )
      self.__values_list.remove( value )
    except (KeyError, ValueError):
      pass
  
  #//-------------------------------------------------------//
  
  def   __removeValues( self, values ):
    
    values_set_remove = self.__values_set.remove
    values_list_remove = self.__values_list.remove
    
    for value in toSequence( values ):
      try:
        values_set_remove( value )
        values_list_remove( value )
      except (KeyError, ValueError):
        pass
    
  #//-------------------------------------------------------//
  
  def   __contains__( self, value ):
    return value in self.__values_set
  
  #//-------------------------------------------------------//
  
  def   __len__( self ):
    return len(self.__values_list)
  
  #//-------------------------------------------------------//
  
  def   __iter__( self ):
    return iter(self.__values_list)
  
  #//-------------------------------------------------------//
  
  def   __reversed__( self ):
    return reversed(self.__values_list)
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):        return str(self.__values_list)
  
  def   __eq__( self, other ):  return self.__values_set == set( toSequence( other ) )
  def   __ne__( self, other ):  return self.__values_set != set( toSequence( other ) )
  def   __lt__( self, other ):  return self.__values_set <  set( toSequence( other ) )
  def   __le__( self, other ):  return self.__values_set <= set( toSequence( other ) )
  def   __gt__( self, other ):  return self.__values_set >  set( toSequence( other ) )
  def   __ge__( self, other ):  return self.__values_set >= set( toSequence( other ) )
  
  #//-------------------------------------------------------//
  
  def   __getitem__(self, index ):
    return self.__values_list[ index ]
  
  #//-------------------------------------------------------//
  
  def   __iadd__(self, values ):
    self.__addValues( values )
    return self
  
  #//-------------------------------------------------------//
  
  def   __isub__(self, values ):
    self.__removeValues( values )
    return self
  
  #//-------------------------------------------------------//
  
  def   append( self, value ):
    self.__addValue( value )
  
  #//-------------------------------------------------------//
  
  def   extend( self, values ):
    self.__addValues( values )
  
  #//-------------------------------------------------------//
  
  def   append_front( self, value ):
    self.__addValueFront( value )
  
  #//-------------------------------------------------------//
  
  def   extend_front( self, values ):
    self.__addValuesFront( values )
  
  #//-------------------------------------------------------//
  
  def   remove( self, value ):
    self.__removeValue( value )
  
  #//-------------------------------------------------------//
  
  def   pop( self ):
    value = self.__values_list.pop()
    self.__values_set.remove( value )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   pop_front( self ):
    value = self.__values_list.pop(0)
    self.__values_set.remove( value )
    
    return value
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    size = len(self)
    if size != len(self.__values_list):
      raise AssertionError("size(%s) != len(self.__values_list)(%s)" % (size, len(self.__values_list)) )
    
    if size != len(self.__values_set):
      raise AssertionError("size(%s) != len(self.__values_set)(%s)" % (size, len(self.__values_set)) )
    
    if self.__values_set != set(self.__values_list):
      raise AssertionError( "self.__values_set != self.__values_list" )
