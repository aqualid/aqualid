#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = ( 'FileLock', 'ErrorFileLocked' )

import os
import time
import errno

from aql.util_types import AqlException

class   ErrorFileLocked( AqlException ):
  def   __init__( self, filename ):
    msg = 'File "%s" is locked.' % (filename,)
    super(ErrorFileLocked, self).__init__( msg )

#//===========================================================================//
#   General implementation
#//===========================================================================//
class GeneralFileLock (object):
  
  __slots__ = ('lockfilename', 'filename', 'retries', 'interval')
  
  def   __init__( self, filename, interval = 0.25, timeout = 5 * 60 ):
    filename = os.path.normcase( os.path.abspath( filename ) )
    self.filename = filename
    self.lockfilename = filename + '.lock'
    self.interval = interval
    self.retries = int(timeout / interval)
  
  def   __enter__(self):
    return self

  #noinspection PyUnusedLocal
  def   __exit__(self, exc_type, exc_value, traceback):
    self.releaseLock()
  
  def   readLock( self, wait = True, force = False ):
    return self.writeLock( wait = wait, force = force )
  
  def   writeLock( self, wait = True, force = False ):
    if wait:
      index = self.retries
    else:
      index = 0
    
    while True:
      try:
        self.__lock( force = force )
        break
      except ErrorFileLocked:
        if index <= 0:
          raise
        
      index -= 1
      time.sleep( self.interval )
    
    return self
  
  def   __lock( self, force = False ):
    try:
      os.mkdir( self.lockfilename )
    except OSError as ex:
      if ex.errno == errno.EEXIST:
        if force:
          return
        raise ErrorFileLocked( self.filename )
      
      raise
  
  def   releaseLock( self ):
    try:
      os.rmdir( self.lockfilename )
    except OSError as ex:
      if ex.errno != errno.ENOENT:
        raise

try:
  #//===========================================================================//
  #   Unix implementation
  #//===========================================================================//
  #noinspection PyUnresolvedReferences
  import fcntl
  
  class UnixFileLock (object):
    
    __slots__ = ('fd','filename')
  
    def   __init__( self, filename ):
      filename = os.path.normcase( os.path.abspath( filename ) )
      self.filename = filename
      self.fd = os.open( filename, os.O_RDWR | os.O_CREAT )
    
    def   __enter__(self):
      return self

    #noinspection PyUnusedLocal
    def   __exit__(self, exc_type, exc_value, traceback):
      self.releaseLock()
    
    def   readLock( self, wait = True, force = False ):
      self.__lock( write = False, wait = wait )
      return self
    
    def   writeLock( self, wait = True, force = False ):
      self.__lock( write = True, wait = wait )
      return self
    
    def   __lock( self, write, wait ):
      
      if write:
        flags = fcntl.LOCK_EX
      else:
        flags = fcntl.LOCK_SH
      
      if not wait:
        flags |= fcntl.LOCK_NB
      
      try:
        fcntl.lockf( self.fd, flags )
      except IOError as ex:
        if ex.errno in ( errno.EACCES, errno.EAGAIN ):
          raise ErrorFileLocked( self.filename )
        raise
    
    def   releaseLock( self ):
      fcntl.lockf( self.fd, fcntl.LOCK_UN )
  
  FileLock = UnixFileLock
  
except ImportError:

  try:
    #//===========================================================================//
    #   Widows implementation
    #//===========================================================================//
    #noinspection PyUnresolvedReferences
    import win32con
    #noinspection PyUnresolvedReferences
    import win32file
    #noinspection PyUnresolvedReferences
    import pywintypes
    
    class WindowsFileLock (object):
      
      __slots__ = ('hfile', 'filename' )
      _overlapped = pywintypes.OVERLAPPED()
    
      def   __init__( self, filename ):
        
        filename = os.path.normcase( os.path.abspath( filename ) )
        
        self.filename = filename
        lockfilename = filename  + ".lock"
        
        self.hfile = win32file.CreateFile( lockfilename,
                                           win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                           win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
                                           None,
                                           win32file.OPEN_ALWAYS,
                                           0,
                                           None )
      
      def   __enter__(self):
        return self

      #noinspection PyUnusedLocal
      def   __exit__(self, exc_type, exc_value, traceback):
        self.releaseLock()
      
      def   readLock( self, wait = True, force = False ):
        self.__lock( write = False, wait = wait )
        return self
      
      def   writeLock( self, wait = True, force = False ):
        self.__lock( write = True, wait = wait )
        return self
      
      def   __lock( self, write, wait ):
        
        if write:
          flags = win32con.LOCKFILE_EXCLUSIVE_LOCK
        else:
          flags = 0
        
        if not wait:
          flags |= win32con.LOCKFILE_FAIL_IMMEDIATELY
        
        overlapped = pywintypes.OVERLAPPED()
        
        result = win32file.LockFileEx( self.hfile, flags, 0, 4096, overlapped )
        if not result:
          raise ErrorFileLocked( self.filename )
      
      def   releaseLock( self ):
        overlapped = pywintypes.OVERLAPPED()
        win32file.UnlockFileEx( self.hfile, 0, 4096, overlapped )
    
    FileLock = WindowsFileLock
    
  except ImportError:
    
    FileLock = GeneralFileLock
