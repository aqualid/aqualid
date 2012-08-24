import sys
import time
import os.path
import multiprocessing as mp

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql_temp_file import Tempfile
from aql_lock_file import FileLock, GeneralFileLock

#//===========================================================================//

def   writeProcess( filename, event, LockType ):
  
  flock = LockType( filename )
  
  with flock.writeLock():
    event.set()
    
    time.sleep( 2 )
    
    with open( filename, 'w+b' ) as file:
      file.write( b"123" )
      file.flush()

#//===========================================================================//

def   readProcess( filename, event, LockType ):
  
  flock = LockType( filename )
  
  with flock.readLock():
    event.set()
    
    time.sleep( 2 )
    
    with open( filename, 'r+b' ) as file:
      file.read()

#//===========================================================================//
class TestFileLock( AqlTestCase ):
  
  def __test_file_lock_type(self, LockType):
    
    with Tempfile() as temp_file:
      
      flock = LockType( temp_file.name )
      flock.releaseLock()
      flock.releaseLock()
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file.name, event, LockType) )
      p.start()
      
      event.wait()
      
      start_time = time.time()
      with flock.writeLock():
        
        self.assertGreaterEqual( time.time() - start_time, 1 )
        
        with open( temp_file.name, 'w+b' ) as file:
          file.write( b'345' )
          file.flush()
      
      p.join()

  #//===========================================================================//

  def test_file_lock(self):
    
    self.__test_file_lock_type( GeneralFileLock )
    
    if FileLock is not GeneralFileLock:
      self.__test_file_lock_type( FileLock )

  #//===========================================================================//

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

  def test_file_wrlock(self):
    
    if FileLock is GeneralFileLock:
      return
    
    with Tempfile() as temp_file:
      
      flock = FileLock( temp_file.name )
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file.name, event, FileLock) )
      p.start()
      
      event.wait()
      
      start_time = time.time()
      
      with flock.readLock():
        
        self.assertGreaterEqual( time.time() - start_time, 1 )
        
        with open( temp_file.name, 'w+b' ) as file:
          file.write( b'345' )
          file.flush()
      
      p.join()
    
  #//=======================================================//

  def test_file_rwlock(self):
    
    if FileLock is GeneralFileLock:
      return
    
    with Tempfile() as temp_file:
      
      flock = FileLock( temp_file.name )
      
      event = mp.Event()
      
      p = mp.Process( target = readProcess, args = (temp_file.name, event, FileLock) )
      p.start()
      
      event.wait()
      
      start_time = time.time()
      
      with flock.writeLock():
        
        self.assertGreaterEqual( time.time() - start_time, 1 )
        
        with open( temp_file.name, 'w+b' ) as file:
          file.write( b'345' )
          file.flush()
      
      p.join()

#//=======================================================//

if __name__ == "__main__":
  runLocalTests()

