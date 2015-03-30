import os
import sys
import random
import uuid
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, DataFile, Chrono

#//===========================================================================//

def   generateData( min_size, max_size ):
  return bytearray( random.randint( 0, 255 ) for i in range( random.randint( min_size, max_size ) ) )

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
          df.write( data_id, data );  df.selfTest()
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
          tmp_data_id = df.map_keys( [key] )[0]
          self.assertEqual( tmp_data_id, data_id )
          new_key = df.write_with_key( data_id, data ); df.selfTest()
          self.assertGreater( new_key, key )
          self.assertIsNone( df.map_keys([key]) )
          self.assertSequenceEqual( df.map_keys([new_key]), [data_id] )
          
          stored_data = df.read_by_key( new_key )
          self.assertEqual( stored_data, data )
        
        
        # self.assertEqual( data_hash, dict( df ) )
        # 
        # df.selfTest(); df.close(); df.selfTest()
        # 
        # df = DataFile( tmp ); df.selfTest()
        # 
        # self.assertEqual( len(data_hash), len( df ) )
        # self.assertEqual( data_hash, dict( df ) )
        # 
        # for key in data_hash:
        #   data = bytearray( len(df[key]) )
        #   new_key = df.replace(key, data )
        #   df.selfTest()
        #   del data_hash[key]; data_hash[new_key] = data
        # 
        # self.assertEqual( data_hash, dict( df ) )
        # 
        # for key in data_hash:
        #   data = bytearray( len(df[key]) // 2 )
        #   new_key = df.replace(key, data )
        #   df.selfTest()
        #   del data_hash[key]; data_hash[new_key] = data
        # 
        # self.assertEqual( data_hash, dict( df ) )
        # 
        # for key in data_hash:
        #   data = bytearray( len(df[key]) * 8 )
        #   new_key = df.replace(key, data )
        #   df.selfTest()
        #   del data_hash[key]; data_hash[new_key] = data
        # 
        # self.assertEqual( data_hash, dict( df ) )
        # 
        # for key in tuple(data_hash):
        #   del df[key]
        #   del data_hash[key]
        #   df.selfTest()
        # 
        # self.assertEqual( data_hash, dict( df ) )
        # 
        # #//-------------------------------------------------------//
        # 
        # self.assertEqual( len( df ), 0 )
        # self.assertFalse( df )
      
      finally:
        df.close()

  #//-------------------------------------------------------//
  @skip
  def   _test_data_file_update(self):
    
    with Tempfile() as tmp:
      
      data_list = generateDataList( 10, 10, 7, 57 )
      data_hash = {}
      
      df = DataFile( tmp )
      try:
        df.selfTest()
        
        for data in data_list:
          key = df.append( data ); df.selfTest()
          data_hash[ key ] = data
        
        self.assertEqual( data_hash, dict( df ) )
        
        self.assertEqual( tuple(map(list, df.update() )), ([],[]) )
        
        df.flush()
        
        df2 = DataFile( tmp.name )
        try:
          df2.selfTest()
          added_keys = []
          deleted_keys = []
          
          for key in list(data_hash)[:2]:
            data = bytearray( len(data_hash[key]) )
            
            new_key = df2.replace( key, data )
            df2.selfTest()
            del data_hash[key]; data_hash[new_key] = data
            
            added_keys.append(new_key)
            deleted_keys.append(key)
          
          data = bytearray( 4 )
          key = df2.append( data ); df2.selfTest()
          data_hash[key] = data
          added_keys.append(key)
          
          data = bytearray( 5 )
          key = df2.append( data ); df2.selfTest()
          data_hash[key] = data
          added_keys.append(key)
          
          for key in list(data_hash)[2:4]:
            del df2[key]
            del data_hash[key]
            df2.selfTest()
            deleted_keys.append( key )
          
          df2.flush()
          added, deleted = df.update()
          df.selfTest()
          
          self.assertEqual( sorted(added), sorted( added_keys ) )
          self.assertEqual( sorted(deleted), sorted( deleted_keys ) )
          
          df2.selfTest()
          
          added_keys = []
          deleted_keys = []
          df3 = DataFile( tmp.name )
          try:
            df3.selfTest()
            for key in list(data_hash)[2:4]:
              del df3[key]
              del data_hash[key]
              df3.selfTest()
              deleted_keys.append( key )
            
            df3.flush()
            added, deleted = df.update()
            df.selfTest()
            
            self.assertEqual( sorted(added), sorted( added_keys ) )
            self.assertEqual( sorted(deleted), sorted( deleted_keys ) )
            
            added, deleted = df2.update()
            df2.selfTest()
            
            self.assertEqual( sorted(added), sorted( added_keys ) )
            self.assertEqual( sorted(deleted), sorted( deleted_keys ) )
        
          finally:
            df3.close()
        finally:
          df2.close()
      finally:
        df.close()
  
  #//-------------------------------------------------------//
  
  def test_data_file_remove(self):
    with Tempfile() as tmp:
      tmp.remove()
      
      data_list = generateDataList( 50, 50, 7, 57 )
      data_keys = []
      
      df = DataFile( tmp )
      try:
        for data in data_list:
          key = df.append( data ); df.selfTest()
          data_keys.append( key )
        
        remove_keys = []
        
        for i, key in reversed( list( enumerate( data_keys ) ) ):
          if (i % 2) == 0:
            remove_keys.append( key )
            del data_keys[i]
            del data_list[i]
        
        df.remove( remove_keys ); df.selfTest()
        
        self.assertEqual( set(data_keys) , set( dict(df).keys() ) )
        
        df.close()
        df = DataFile( tmp )
        
        for key, data in zip( data_keys, data_list ):
          self.assertEqual( data , df[key] )
          
        for key in remove_keys:
          self.assertRaises( KeyError, df.__getitem__, key )
        
        df.remove( data_keys[:1] ); df.selfTest()
        data_keys = data_keys[:1]
        data_list = data_keys[:1]
        
        df.remove( [ data_keys[-1] ] ); df.selfTest()
        data_keys.pop()
        data_list.pop()
        
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
        
      finally:
        df.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
