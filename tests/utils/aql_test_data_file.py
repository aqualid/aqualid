import os
import sys
import random
import timeit

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_event_manager import event_manager
from aql_event_handler import EventHandler
from aql_temp_file import Tempfile
from aql_data_file import DataFile

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

@testcase
def test_data_file(self):
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as tmp:
    tmp.remove()
    
    data_list = generateDataList( 50, 50, 7, 57 )
    data_hash = {}
    
    df = DataFile( tmp.name ); df.selfTest()
    
    for data in data_list:
      key = df.append( data ); df.selfTest()
      data_hash[ key ] = data
    
    self.assertEqual( data_hash, dict( df ) )
    
    df.close(); df.selfTest()
    
    df = DataFile( tmp.name ); df.selfTest()
    
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

#//===========================================================================//

@testcase
def   test_data_file_update(self):
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as tmp:
    
    data_list = generateDataList( 10, 10, 7, 57 )
    data_hash = {}
    
    df = DataFile( tmp.name ); df.selfTest()
    
    for data in data_list:
      key = df.append( data ); df.selfTest()
      data_hash[ key ] = data
    
    self.assertEqual( data_hash, dict( df ) )
    
    self.assertEqual( tuple(map(list, df.update() )), ([],[]) )
    
    df2 = DataFile( tmp.name ); df2.selfTest()
    
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
    
    added, deleted = df.update()
    df.selfTest()
    
    self.assertEqual( sorted(added), sorted( added_keys ) )
    self.assertEqual( sorted(deleted), sorted( deleted_keys ) )
    
    df2.selfTest()
    
    added_keys = []
    deleted_keys = []
    df3 = DataFile( tmp.name ); df3.selfTest()
    for key in list(data_hash)[2:4]:
      del df3[key]
      del data_hash[key]
      df3.selfTest()
      deleted_keys.append( key )
    
    added, deleted = df.update()
    df.selfTest()
    
    self.assertEqual( sorted(added), sorted( added_keys ) )
    self.assertEqual( sorted(deleted), sorted( deleted_keys ) )
    
    added, deleted = df2.update()
    df2.selfTest()
    
    self.assertEqual( sorted(added), sorted( added_keys ) )
    self.assertEqual( sorted(deleted), sorted( deleted_keys ) )

#//===========================================================================//

@skip
@testcase
def   test_data_file_speed(self):
  event_manager.addHandler( EventHandler() )
  
  with Tempfile() as tmp:
    
    data_list = generateDataList( 100000, 100000, 128, 1024 )
    data_hash = {}
    
    df = DataFile( tmp.name )
    
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

#//===========================================================================//

if __name__ == "__main__":
  runTests()
