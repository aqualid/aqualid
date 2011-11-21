import random
import time

from aql_tests import testcase, skip
from aql_map import AvlMap
from aql_temp_file import Tempfile

#//===========================================================================//

class Item (object):
  
  __slots__ = ('name', 'value')
  
  def  __init__(self, name, value ):
    self.name = name
    self.value = value
  
  def __hash__(self):
    return hash(self.name)
  
  def __lt__(self, other):
    return (self.name < other.name) or ( (not (other.name < self.name)) and (self.value < other.value) )
  
  def __eq__(self, other):
    return (self.name == other.name) and (self.value == other.value)
  
  def __ne__(self, other):
    return not self.__eq__(self, other)
  
  def __str__(self):
    return str(self.name) + ":" + str(self.value)

#//===========================================================================//

@skip
@testcase
def test_map(self):
  with Tempfile() as temp_file:
    
    file_size = 200 * 1024 * 1024
    
    start = time.clock()
    
    buffer = bytearray( file_size )
    #~ for i in range(0, file_size ):
      #~ buffer.append( random.randrange( 0, 255 ) )
    
    print ("gen random content time: %s" % (time.clock() - start) )
    
    start = time.clock()
    temp_file.write( buffer )
    
    print ("write random content time: %s" % (time.clock() - start) )
    
    start = time.clock()
    temp_file.seek( 1000000 )
    temp_file.write( buffer[20000:20200] )
    temp_file.seek( 2000000 )
    temp_file.write( buffer[10000:10200] )
    temp_file.seek( 1500000 )
    temp_file.write( buffer[300000:300200] )
    
    temp_file.seek( 0 )
    temp_file.write( buffer[300000:300200] )
    
    temp_file.seek( 1000 )
    temp_file.write( buffer[300000:300200] )
    temp_file.flush()
    
    print ("write part of random content time: %s" % (time.clock() - start) )
    
    start = time.clock()
    temp_file.seek( 0 )
    temp_file.write( buffer )
    temp_file.flush()
    
    print ("rewrite random content time: %s" % (time.clock() - start) )


  
  
#//===========================================================================//
