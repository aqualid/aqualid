import bisect
import random
import time

class Hash (object):
  
  __slots__ = ('values', 'size', 'seq_num', 'keys')
  
  def   __init__(self):
    
    self.values = {}
    self.size = 0
    self.seq_num = 0
    self.keys = {}
  
  #//-------------------------------------------------------//
  
  def   find(self, item):
    values = self.values.get( hash(item), [] )
    for value_item, key in values:
      if value_item == item:
        return value_item, key
    
    return None, -1
  
  #//-------------------------------------------------------//
  
  def   findByKey(self, key):
    try:
      return self.keys[ key ]
    except KeyError:
      return None
  
  #//-------------------------------------------------------//
  
  def   add(self, item):
    values = self.values.setdefault( hash(item), [] )
    
    for value_item, key in values:
      if value_item == item:
        return value_item, key
    
    key = self.seq_num
    self.seq_num += 1
    
    value = (item, key )
    
    values.append( value )
    self.size += 1
    
    self.keys[ key ] = item
    
    return value
  
  #//-------------------------------------------------------//
  
  def   remove(self, item):
    values = self.values.get( hash(item), [] )
    for value_item, key in values:
      if value_item == item:
        del values[ item ]
        del self.keys[ key ]
  
  #//-------------------------------------------------------//
  
  def   __contains__(self, item):
    return self.find( item )[0] is not None
  
  #//-------------------------------------------------------//
  
  def   __iter__(self):
    for key, item in self.keys.items():
      yield item
  
  #//-------------------------------------------------------//
  
  def   clear(self):
    self.values.clear()
    self.keys.clear()
    self.size = 0
  
  #//-------------------------------------------------------//
  
  def   __len__(self):
    return self.size
  
  #//-------------------------------------------------------//
  
  def   __bool__(self):
    return self.size > 0

#//===========================================================================//


class _HashItem(object):
  __slots__ = ('item', 'key')
  
  def  __init__(self, item ):
    self.item = item
    self.key = hash(item)

  def   __lt__( self, other):       return self.key <  other.key
  def   __le__( self, other):       return self.key <= other.key
  def   __eq__( self, other):       return self.key == other.key
  def   __ne__( self, other):       return self.key != other.key
  def   __gt__( self, other):       return self.key >  other.key
  def   __ge__( self, other):       return self.key >= other.key


num_of_values = 100000
values =[ random.randrange(1000000) for i in range(num_of_values) ]
item_values = map(_HashItem, values )

bi_list = []
start_time = time.clock()
for value in item_values:
  bisect.insort( bi_list, value )
elapsed_time = time.clock() - start_time

print ("bisect: %s" % elapsed_time)

sorted_list = []
start_time = time.clock()
for value in item_values:
  sorted_list.append( value )

sorted_list.sort()
elapsed_time = time.clock() - start_time

print ("list: %s" % elapsed_time)

h = Hash()
start_time = time.clock()
for value in values:
  h.add( value )

elapsed_time = time.clock() - start_time

print ("hash: %s" % elapsed_time)
