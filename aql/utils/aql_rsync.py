#
# Copyright (c) 2012 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = (
  'RemoteHost', 'Rsync',
)

import sys
import os.path
import itertools
import tempfile

from aql.types import toSequence
from .aql_utils import execCommand, whereProgram

#//===========================================================================//

class RemoteHost (object):
  __slots__ = ('address', 'login', 'key_file')
  
  def   __init__( self, host, login, key_file ):
    self.address = address
    self.login = login
    self.key_file = key_file
  
  def   remotePath( self, path ):
    return "%s@%s:%s" % (self.login, self.address, path)

#//===========================================================================//

class   PathNormalizer( object ):
  __slots__ = (
    'local_path_sep',
    'remote_path_sep',
    'cygwin_paths'
  )
  
  #//-------------------------------------------------------//
  
  def   __init__(self, remote_path_sep = '/', local_path_sep = os.path.sep, cygwin_paths = False ):
    if cygwin_paths:
      local_path_sep = '/'
      remote_path_sep = '/'
    
    self.cygwin_paths = cygwin_paths
    self.local_path_sep = local_path_sep
    self.remote_path_sep = remote_path_sep
    
  #//-------------------------------------------------------//
  
  class _NormPath( str ):  pass
  
  def   __normPath( self, path, path_sep ):
    
    if isinstance( path, self._NormPath ):
      return path
    
    if not path:
      path = '.'
    
    if self.cygwin_paths:
      drive, path = os.path.splitdrive( path )
      if drive.find(':') == 1:
        drive = "/cygdrive/" + drive[0]
      path = drive + path
    
    path = path.replace('\\', '/')
    if path[-1] == '/':
      last_sep = path_sep
    else:
      last_sep = ''
    
    path = os.path.normcase( os.path.normpath( path ) )
    if path_sep != os.path.sep:
      if path_sep == '/':
        path = path.replace('\\', '/')
      else:
        path = path.replace('/', '\\')
    
    return self._NormPath( path + last_sep )
  
  #//-------------------------------------------------------//
  
  def   localPath( self, path ):
    path = self.__normPath( path, self.local_path_sep )
    return path
  
  def   remotePath( self, path ):
    path = self.__normPath( path, self.remote_path_sep )
    return path

#//===========================================================================//

class   Rsync( object ):
  
  __slots__ = (
    'cmd',
    'host',
    'path_normalizer',
    'env',
  )
  
  def   __init__( self, rsync, host, cygwin_paths = False, env = None ):
    
    if not rsync:
      rsync = whereProgram( 'rsync', env )
    
    self.cmd = (rsync, '-avzubsX')
    self.host = host if host else None
    self.path_normalizer = PathNormalizer( cygwin_paths = cygwin_paths )
    self.env = env
  
  #//-------------------------------------------------------//
  
  def   __sync( self, local_files, local_path, remote_path, sync_local, exclude ):
    
    remote_path = self.normRemotePath( remote_path )
    local_path = self.normLocalPath( local_path )
    if local_files:
      local_files = self.__normLocalFiles( local_files, local_path[0] )
    
    cmd = list( self.cmd )
    
    excludes = []
    
    for args in itertools.product( ['--exclude'], toSequence( exclude ) ):
      excludes += args
    
    if excludes:
      cmd += excludes
      cmd.append('--delete-excluded')
    
    host = self.host
    if host:
      remote_path = map( host.remotePath, remote_path )
      cmd += [ '-e', 'ssh -o StrictHostKeyChecking=no -i ' + str(self.host.key_file) ]
    
    tmp_r, tmp_w = None, None
    try:
      if sync_local:
        cmd += remote_path
        cmd += local_path
      else:
        if local_files:
          tmp_r, tmp_w = os.pipe()
          os.write( tmp_w, '\n'.join( local_files ).encode('utf-8') )
          os.close( tmp_w )
          tmp_w = None
          cmd.append( "--files-from=-" )
        
        cmd += local_path
        cmd += remote_path
      
      result = execCommand( cmd, env = self.env, stdin = tmp_r )
      if result.failed():
        raise result
    
    finally:
      if tmp_r: os.close( tmp_r )
      if tmp_w: os.close( tmp_w )
    
  #//-------------------------------------------------------//
  
  def   __normLocalFiles( self, local_files, local_path ):
    
    norm_lpath = self.path_normalizer.localPath
    
    files = []
    
    for file in toSequence( local_files ):
      file = norm_lpath( file )
      if file.startswith( local_path ):
        file = file[len(local_path):]
      
      files.append( file )
    
    return files
  
  #//-------------------------------------------------------//
  
  def   normLocalPath( self, local_path ):
    norm_path = self.path_normalizer.localPath
    return tuple( norm_path(path) for path in toSequence(local_path) )
  
  #//-------------------------------------------------------//
  
  def   normRemotePath( self, remote_path ):
    norm_path = self.path_normalizer.remotePath
    return tuple( norm_path(path) for path in toSequence( remote_path ) )
  
  #//-------------------------------------------------------//
  
  def   get( self, local_path, remote_path, exclude = None ):
    self.__sync( None, local_path, remote_path, sync_local = True, exclude = exclude )
  
  #//-------------------------------------------------------//
  
  def   put( self, local_path, remote_path, exclude = None, local_files = None ):
    self.__sync( local_files, local_path, remote_path, sync_local = False, exclude = exclude )

#//===========================================================================//
