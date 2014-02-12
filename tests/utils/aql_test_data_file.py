import os
import sys
import random
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, DataFile

#//===========================================================================//

def   generateData( min_size, max_size ):
  b = bytearray()
  
  size = random.randint( min_size, max_size )
  for i in range( 0, size ):
    b.append( i % 256 )
  
  return b

#//===========================================================================//

def   generateDataList( min_list_size, max_list_size, min_data_size, max_data_size ):
  bl = []
  size = random.randint( min_list_size, max_list_size )
  for i in range( 0, size ):
    bl.append( generateData( min_data_size, max_data_size ) )
  
  return bl

#//===========================================================================//

def   printFileContent( filename ):
  with open( filename, 'rb' ) as f:
    b = f.read()
    print( "%s: %s" % ( filename, b ))

#//===========================================================================//

class TestDataFile( AqlTestCase ):
  
  def test_data_file(self):
    with Tempfile() as tmp:
      tmp.remove()
      
      data_list = generateDataList( 50, 50, 7, 57 )
      data_hash = {}
      
      df = DataFile( tmp.name )
      try:
        df.selfTest()
        
        df.clear()
        
        df.selfTest()
        
        for data in data_list:
          key = df.append( data ); df.selfTest()
          data_hash[ key ] = data
        
        self.assertEqual( data_hash, dict( df ) )
        
        df.selfTest(); df.close(); df.selfTest()
        
        df = DataFile( tmp.name ); df.selfTest()
        
        self.assertEqual( len(data_hash), len( df ) )
        self.assertEqual( data_hash, dict( df ) )
        
        for key in data_hash:
          data = bytearray( len(df[key]) )
          new_key = df.replace(key, data )
          df.selfTest()
          del data_hash[key]; data_hash[new_key] = data
        
        self.assertEqual( data_hash, dict( df ) )
        
        for key in data_hash:
          data = bytearray( len(df[key]) // 2 )
          new_key = df.replace(key, data )
          df.selfTest()
          del data_hash[key]; data_hash[new_key] = data
        
        self.assertEqual( data_hash, dict( df ) )
        
        for key in data_hash:
          data = bytearray( len(df[key]) * 8 )
          new_key = df.replace(key, data )
          df.selfTest()
          del data_hash[key]; data_hash[new_key] = data
        
        self.assertEqual( data_hash, dict( df ) )
        
        for key in tuple(data_hash):
          del df[key]
          del data_hash[key]
          df.selfTest()
        
        self.assertEqual( data_hash, dict( df ) )
        
        #//-------------------------------------------------------//
        
        self.assertEqual( len( df ), 0 )
        self.assertFalse( df )
      
      finally:
        df.close()

  #//-------------------------------------------------------//
  def   test_data_file_update(self):
    return
    
    with Tempfile() as tmp:
      
      data_list = generateDataList( 10, 10, 7, 57 )
      data_hash = {}
      
      df = DataFile( tmp.name )
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
      
      df = DataFile( tmp.name )
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
        df = DataFile( tmp.name )
        
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
    return
    
    with Tempfile() as tmp:
      
      data_list = generateDataList( 100000, 100000, 128, 1024 )
      data_hash = {}
      
      df = DataFile( tmp.name )
      try:
        
        key = None
        for data in data_list:
          key = df.append( data )
          data_hash[ key ] = data
        
        df2 = DataFile( tmp.name )
        df2.update()
        
        def update( df, df2 ):
          df.append( bytearray(10) )
          df2.update()
        
        up = lambda df = df, df2 = df2, update = update: update(df,df2)
        
        t = timeit.timeit( up, number = 10 ) / 10
        
        print("update time: %s" % t)
        
        t = timeit.timeit( lambda df = df, data = bytearray(generateData(256,256)): df.append(data), number = 1000 ) / 1000
        
        print("append time: %s" % t)
      
      finally:
        df.close()

#//===========================================================================//

if __name__ == "__main__":
  runLocalTests()
