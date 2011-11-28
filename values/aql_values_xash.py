class ValuesXash (object):
  
  __slots__ = ('pairs', 'keys')
  
  def   __init__(self):
    
    self.pairs = {}
    self.keys = {}
  
  #//-------------------------------------------------------//
  
  def   getRef( self, value ):
    pairs = self.pairs.setdefault( hash(value.name), [] )
    
    index = 0
    for key, val in pairs:
      if val.name == value.name:
        return pairs, index
      
      index += 1
    
    return pairs, -1
    
  #//-------------------------------------------------------//
  
  def   addToRef( self, ref, key, value ):
    
    pairs, index = ref
    pair = (key, value )
    keys = self.keys
    
    try:
      old_value = keys[ key ]
      if (index == -1) or (pairs[index][1] is not old_value):
        self.removeByRef( self.getRef( old_value ) )
    except KeyError:
      pass
    
    if index != -1:
      old_key = pairs[index][0]
      del keys[ old_key ]
      pairs[ index ] = pair
    
    else:
      pairs.append( pair )
    
    keys[ key ] = value
    
  #//-------------------------------------------------------//
  
  def   removeByRef( self, ref ):
    pairs, index = ref
    if index != -1:
      key = pairs[index][0]
      del self.keys[ key ]
      del pairs[ index ]
  
  #//-------------------------------------------------------//
  
  def   __delitem__( self, key ):
    self.removeByRef( self.getRef( self.keys[ key ] ) )
  
  #//-------------------------------------------------------//
  
  def   __getitem__(self, key):
    return self.keys[ key ]
  
  #//-------------------------------------------------------//
  
  def   __setitem__(self, key, value ):
    self.addToRef( self.getRef( value ), key, value )
  
  #//-------------------------------------------------------//
  
  def   __iter__(self):
    return iter(self.keys)
  
  #//-------------------------------------------------------//
  
  def   pop(self, key):
    value = self.keys[ key ]
    self.removeByRef( self.getRef( value ) )
    return value
  
  #//-------------------------------------------------------//
  
  def   getKey( self, ref ):
    pairs, index = ref
    if index != -1:
      return pairs[index][0]
    
    return None
  
  #//-------------------------------------------------------//
  
  def   find(self, value):
    pairs, index = self.getRef( value )
    if index != -1:
      return pairs[index]
    
    return None, None
  
  #//-------------------------------------------------------//
  
  def   remove( self, value ):
    ref = self.getRef( value )
    key = self.getKey( ref )
    self.removeByRef( ref )
    
    return key
  
  #//-------------------------------------------------------//
  
  def   __contains__(self, value):
    return self.getRef( value )[1] != -1
  
  #//-------------------------------------------------------//
  
  def   clear(self):
    self.pairs.clear()
    self.keys.clear()
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return len(self.keys)
  
  #//-------------------------------------------------------//
  
  def   __bool__(self):
    return bool(self.keys)
  
  #//-------------------------------------------------------//
  
  def   selfTest( self ):
    size = 0
    for value_id, pairs in self.pairs.items():
      for key, value in pairs:
        size += 1
        
        if hash(value.name) != value_id:
          raise AssertionError("hash(value.name) != value_id")
        
        if key not in self.keys:
          raise AssertionError("key not in self.keys")
        
        if value is not self.keys[ key ]:
          raise AssertionError("value is not self.keys[ key ]")
    
    if size != len(self.keys):
      raise AssertionError("size != len(self.keys)")
