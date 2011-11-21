import sys
import time
import os.path
import multiprocessing as mp

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import testcase, skip, runTests
from aql_temp_file import Tempfile
from aql_lock_file import FileLock, GeneralFileLock

#//===========================================================================//

def   writeProcess( filename, delay, LockType ):
  
  flock = LockType( filename )
  
  with flock.writeLock():
    
    time.sleep( delay )
    
    with open( filename, 'w+b' ) as file:
      file.write( b"123" )
      file.flush()

#//===========================================================================//

def   readProcess( filename, delay, LockType ):
  
  flock = LockType( filename )
  
  with flock.readLock():
    
    time.sleep( delay )
    
    with open( filename, 'r+b' ) as file:
      file.read()

#//===========================================================================//

def test_file_lock_type(test, LockType):
  
  with Tempfile() as temp_file:
    
    flock = LockType( temp_file.name )
    flock.releaseLock()
    flock.releaseLock()
    
    delay = 3
    
    p = mp.Process( target = writeProcess, args = (temp_file.name, delay, LockType) )
    p.start()
    
    time.sleep(1)
    
    start_time = time.time()
    
    with flock.writeLock():
      
      test.assertGreaterEqual( time.time() - start_time, delay - 1 )
      
      with open( temp_file.name, 'w+b' ) as file:
        file.write( b'345' )
        file.flush()
    
    p.join()

#//===========================================================================//

@testcase
def test_file_lock(self):
  
  test_file_lock_type( self, GeneralFileLock )
  
  if FileLock is not GeneralFileLock:
    test_file_lock_type( self, FileLock )

#//===========================================================================//

@testcase
def test_general_file_lock_timeout(self):
  
  with Tempfile() as temp_file:
    
    flock1 = GeneralFileLock( temp_file.name )
    flock2 = GeneralFileLock( temp_file.name, interval = 1, timeout = 3)
    
    with flock1.writeLock():
      start_time = time.time()
      with self.assertRaises(GeneralFileLock.Timeout):
        with flock2.writeLock():
          self.assertFalse(True)
      self.assertGreaterEqual( time.time() - start_time, 3 )

#//===========================================================================//

@testcase
def test_read_file_lock(self):
  
  if FileLock is GeneralFileLock:
    return
  
  with Tempfile() as temp_file:
    
    flock1 = FileLock( temp_file.name )
    flock2 = FileLock( temp_file.name )
    
    with flock1.readLock():
        start_time = time.time()
        with flock2.readLock():
          self.assertLess( time.time() - start_time, 1 )
          
          with open( temp_file.name, 'r+b' ) as file:
            file.read()

#//===========================================================================//

@testcase
def test_file_wrlock(self):
  
  if FileLock is GeneralFileLock:
    return
  
  with Tempfile() as temp_file:
    
    flock = FileLock( temp_file.name )
    
    delay = 3
    
    p = mp.Process( target = writeProcess, args = (temp_file.name, delay, FileLock) )
    p.start()
    
    time.sleep(1)
    
    start_time = time.time()
    
    with flock.readLock():
      
      self.assertGreaterEqual( time.time() - start_time, delay - 1 )
      
      with open( temp_file.name, 'w+b' ) as file:
        file.write( b'345' )
        file.flush()
    
    p.join()
  
#//=======================================================//

@testcase
def test_file_rwlock(self):
  
  if FileLock is GeneralFileLock:
    return
  
  with Tempfile() as temp_file:
    
    flock = FileLock( temp_file.name )
    
    delay = 3
    
    p = mp.Process( target = readProcess, args = (temp_file.name, delay, FileLock) )
    p.start()
    
    time.sleep(1)
    
    start_time = time.time()
    
    with flock.writeLock():
      
      self.assertGreaterEqual( time.time() - start_time, delay - 1 )
      
      with open( temp_file.name, 'w+b' ) as file:
        file.write( b'345' )
        file.flush()
    
    p.join()

#//=======================================================//

if __name__ == "__main__":
  runTests()

