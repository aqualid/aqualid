import sys
import time
import os.path
import multiprocessing as mp

sys.path.insert( 0, os.path.normpath(os.path.join( os.path.dirname( __file__ ), '..') ))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempfile, FileLock, ErrorFileLocked
from aql.utils.aql_lock_file import GeneralFileLock

#//===========================================================================//

def   writeProcess( filename, event, LockType, **lock_flags ):
  
  flock = LockType( filename )
  
  with flock.writeLock( **lock_flags ):
    event.set()
    
    time.sleep( 2 )
    
    with open( filename, 'w+b' ) as file:
      file.write( b"123" )
      file.flush()

#//===========================================================================//

def   readProcess( filename, event, LockType, **lock_flags ):
  
  flock = LockType( filename )
  
  with flock.readLock( **lock_flags ):
    event.set()
    
    time.sleep( 2 )
    
    with open( filename, 'r+b' ) as file:
      file.read()

#//===========================================================================//
class TestFileLock( AqlTestCase ):
  
  def __test_file_lock_type(self, LockType):
    
    with Tempfile() as temp_file:
      
      flock = LockType( temp_file )
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file, event, LockType) )
      p.start()
      
      event.wait()
      
      start_time = time.time()
      with flock.writeLock():
        
        self.assertGreaterEqual( time.time() - start_time, 1 )
        
        with open( temp_file, 'w+b' ) as file:
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
      
      flock1 = GeneralFileLock( temp_file )
      flock2 = GeneralFileLock( temp_file, interval = 1, timeout = 3)
      
      with flock1.writeLock():
        start_time = time.time()
        with self.assertRaises( ErrorFileLocked ):
          with flock2.writeLock():
            self.assertFalse(True)
        self.assertGreaterEqual( time.time() - start_time, 3 )

  #//===========================================================================//

  def test_read_file_lock(self):
    
    if FileLock is GeneralFileLock:
      return
    
    with Tempfile() as temp_file:
      
      flock1 = FileLock( temp_file )
      flock2 = FileLock( temp_file )
      
      with flock1.readLock():
          start_time = time.time()
          with flock2.readLock():
            self.assertLess( time.time() - start_time, 1 )
            
            with open( temp_file, 'r+b' ) as file:
              file.read()

  #//===========================================================================//

  def test_file_wrlock(self):
    
    if FileLock is GeneralFileLock:
      return
    
    with Tempfile() as temp_file:
      
      flock = FileLock( temp_file )
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file, event, FileLock) )
      p.start()
      
      event.wait()
      
      start_time = time.time()
      
      with flock.readLock():
        
        self.assertGreaterEqual( time.time() - start_time, 1 )
        
        with open( temp_file, 'w+b' ) as file:
          file.write( b'345' )
          file.flush()
      
      p.join()
    
  #//=======================================================//

  def test_file_rwlock(self):
    
    if FileLock is GeneralFileLock:
      return
    
    with Tempfile() as temp_file:
      
      flock = FileLock( temp_file )
      
      event = mp.Event()
      
      p = mp.Process( target = readProcess, args = (temp_file, event, FileLock) )
      p.start()
      
      event.wait()
      
      start_time = time.time()
      
      with flock.writeLock():
        
        self.assertGreaterEqual( time.time() - start_time, 1 )
        
        with open( temp_file, 'w+b' ) as file:
          file.write( b'345' )
          file.flush()
      
      p.join()

  #//===========================================================================//

  def _test_file_lock_no_wait(self, lock_type ):
    
    with Tempfile() as temp_file:
      
      flock = lock_type( temp_file )
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file, event, lock_type ) )
      p.start()
      
      event.wait()
      
      self.assertRaises( ErrorFileLocked, flock.readLock, wait = False )
      self.assertRaises( ErrorFileLocked, flock.writeLock, wait = False )
      
      p.join()
  
  #//===========================================================================//

  def test_file_lock_no_wait(self):
    self._test_file_lock_no_wait( FileLock )
  
  #//===========================================================================//

  def test_general_file_lock_no_wait(self):
    
    if FileLock is GeneralFileLock:
      return
    
    self._test_file_lock_no_wait( GeneralFileLock )
  
  #//===========================================================================//
  
  def test_file_lock_force(self):
    
    if FileLock is GeneralFileLock:
      return
    
    with Tempfile() as temp_file:
      
      flock = FileLock( temp_file )
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file, event, FileLock ) )
      p.start()
      
      event.wait()
      
      self.assertRaises( ErrorFileLocked, flock.readLock, wait = False, force = True )
      self.assertRaises( ErrorFileLocked, flock.writeLock, wait = False, force = True )
      
      p.join()
  
  #//===========================================================================//
  
  def test_general_file_lock_force(self):
    
    with Tempfile() as temp_file:
      
      flock = GeneralFileLock( temp_file )
      
      event = mp.Event()
      
      p = mp.Process( target = writeProcess, args = (temp_file, event, GeneralFileLock ) )
      p.start()
      
      event.wait()
      
      with flock.readLock( wait = False, force = True ):
        with flock.writeLock( wait = False, force = True ):
          pass
              
      p.join()


#//=======================================================//

if __name__ == "__main__":
  runLocalTests()

