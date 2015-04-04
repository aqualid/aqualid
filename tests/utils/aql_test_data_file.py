import os
import sys
import random
import uuid

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, DataFile, Chrono

from aql.util_types import encodeStr

#//===========================================================================//

def   generateData( min_size, max_size ):
  return encodeStr( ''.join( chr(random.randint( 32, 127 )) for i in range( random.randint( min_size, max_size ) ) ) )

#//===========================================================================//

def   generateDataMap( size, min_data_size, max_data_size ):
  data_map = {}
  for i in range( 0, size ):
    data_id = uuid.uuid4().bytes
    data_map[ data_id ] = generateData( min_data_size, max_data_size )
  
  return data_map

#//===========================================================================//

def   extendDataMap( data_map ):
  for data_id in data_map:
    data_size = len(data_map[ data_id ])
    data_map[ data_id ] = generateData( data_size + 1, data_size * 2 )

#//===========================================================================//

def   printFileContent( filename ):
  with open( filename, 'rb' ) as f:
    b = f.read()
    print( "%s: %s" % ( filename, b ))

#//===========================================================================//

class TestDataFile( AqlTestCase ):
  
  def test_data_file_add(self):
    with Tempfile() as tmp:
      tmp.remove()
      
      data_map = generateDataMap( 2100, 16, 128 )
      
      df = DataFile( tmp )
      try:
        df.selfTest()
        
        df.clear()
        
        df.selfTest()
        
        for data_id, data in data_map.items():
          df.write_with_key( data_id, data ); df.selfTest()
          stored_data = df.read( data_id )
          self.assertEqual( stored_data, data )
      
      finally:
        df.close()

  #//=======================================================//
  
  def test_data_file_update(self):
    with Tempfile() as tmp:
      tmp.remove()
      
      data_map = generateDataMap( 100, 16, 128 )
      data_keys = {}
      
      df = DataFile( tmp )
      try:
        df.selfTest()
        
        df.clear()
        
        df.selfTest()
        
        for data_id, data in data_map.items():
          df.write( data_id, data );  df.selfTest()
          stored_data = df.read( data_id )
          self.assertEqual( stored_data, data )
        
        extendDataMap( data_map )
        
        for data_id, data in data_map.items():
          df.write( data_id, data ); df.selfTest()
          stored_data = df.read( data_id )
          self.assertEqual( stored_data, data )
        
        df.close(); df.selfTest()
        
        df.open( tmp ); df.selfTest()
        
        for data_id, data in data_map.items():
          stored_data = df.read( data_id )
          self.assertEqual( stored_data, data )
        
        for data_id, data in data_map.items():
          key = df.write_with_key( data_id, data ); df.selfTest()
          data_keys[ data_id ] = key
          tmp_data_id = df.get_ids( [key] )[0]
          self.assertEqual( tmp_data_id, data_id )
          new_key = df.write_with_key( data_id, data ); df.selfTest()
          self.assertGreater( new_key, key )
          self.assertIsNone( df.get_ids([key]) )
          self.assertSequenceEqual( df.get_ids([new_key]), [data_id] )
          
          stored_data = df.read_by_key( new_key )
          self.assertEqual( stored_data, data )
        
        
        for data_id in data_map:
          df.remove( (data_id,) )
      
      finally:
        df.close()

  #//=======================================================//
  
  def test_data_file_remove(self):
    with Tempfile() as tmp:
      tmp.remove()
      
      data_map = generateDataMap( 1025, 16, 128 )
      
      df = DataFile( tmp )
      try:
        df.selfTest()
        
        df.clear()
        
        df.selfTest()
        
        for data_id, data in data_map.items():
          df.write( data_id, data )
        
        for data_id in data_map:
          df.remove( (data_id,) ); df.selfTest()
        
        df.close(); df = DataFile( tmp ); df.selfTest()
        
        for data_id, data in data_map.items():
          df.write( data_id, data )
        
        df.remove( data_map ); df.selfTest()
        
        for data_id, data in data_map.items():
          df.write( data_id, data )
        
        data_ids = list(data_map)
        random.shuffle(data_ids)
        
        df.remove( data_ids[:len(data_ids)//2] ); df.selfTest()
        
        df.close(); df = DataFile( tmp ); df.selfTest()
        
        df.remove( data_ids[len(data_ids)//2:] ); df.selfTest()
        
        for data_id, data in data_map.items():
          df.write( data_id, data )
        
        data_ids = list(data_map)
        remove_data_ids1 = [ data_ids[i*2 + 0] for i in range(len(data_ids)//2) ]
        remove_data_ids2 = [ data_ids[i*2 + 1] for i in range(len(data_ids)//2) ]
        df.remove( remove_data_ids1 ); df.selfTest()
        
        df.close(); df = DataFile( tmp ); df.selfTest()
        
        for data_id in remove_data_ids2:
          data = data_map[data_id]
          stored_data = df.read( data_id )
          self.assertEqual( stored_data, data )
        
        df.remove( remove_data_ids2 ); df.selfTest()

      finally:
        df.close()
  
  #//-------------------------------------------------------//
  
  @skip
  def   test_data_file_speed(self):
    
    with Tempfile() as tmp:
      timer = Chrono()
      
      with timer:
        data_map = generateDataMap( 20000, 123, 123 )
      
      print("generate data time: %s" % timer)
      
      df = DataFile( tmp )
      try:
        
        with timer:
          for data_id, data in data_map.items():
            df.write_with_key( data_id, data )
        
        print("add time: %s" % timer)
        
        df.close()
        
        with timer:
          df = DataFile( tmp )
        print("load time: %s" % timer)
        
        with timer:
          for data_id, data in data_map.items():
            df.write_with_key( data_id, data )
        
        print("update time: %s" % timer)
        
        with timer:
          for data_id in data_map:
            df.read( data_id )
        
        print("read time: %s" % timer)
        
        data_ids = list(data_map)
        remove_data_ids1 = [ data_ids[i*2 + 0] for i in range(len(data_ids)//2) ]
        remove_data_ids2 = [ data_ids[i*2 + 1] for i in range(len(data_ids)//2) ]
        with timer:
          df.remove( remove_data_ids1 )
          df.remove( remove_data_ids2 )
        
        print("remove time: %s" % timer)
        
      finally:
        df.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
