#
# Copyright (c) 2014 The developers of Aqualid project
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
  'findFiles', 'findFileInPaths', 'absFilePath', 'changePath',
  'whereProgram', 'ErrorProgramNotFound', 'findOptionalProgram', 'findOptionalPrograms',
  'relativeJoin', 'relativeJoinList', 'excludeFilesFromDirs', 'splitDrive', 'groupPathsByDir',
  'Chdir',
)

import os
import sys
import re
import fnmatch
import operator

from aql.util_types import isString, toSequence, AqlException

from .aql_utils import ItemsGroups

#//===========================================================================//

#noinspection PyUnusedLocal
class   ErrorProgramNotFound( AqlException ):
  def   __init__( self, program ):
    msg = "Program '%s' has not been found" % (program,)
    super(type(self), self).__init__( msg )

#//===========================================================================//

class   ErrorProgramName( AqlException ):
  def   __init__( self, prog ):
    msg = "Invalid program name: %s(%s)" % (prog,type(prog))
    super(type(self), self).__init__( msg )

#//===========================================================================//

def   absFilePath( file_path ):
  if not file_path:
    file_path = '.'

  if file_path[-1] in (os.path.sep, os.path.altsep):
    last_sep = os.path.sep
  else:
    last_sep = ''

  return os.path.normcase( os.path.abspath( file_path ) ) + last_sep

#//===========================================================================//

def   excludeFilesFromDirs( files, dirs ):
  result = []
  folders = tuple( os.path.normcase( os.path.abspath( folder ) ) + os.path.sep for folder in toSequence( dirs ) )
  
  for file in toSequence( files ):
    file = os.path.normcase( os.path.abspath( file ) )
    if not file.startswith( folders ):
      result.append( file )
  
  return result

#//===========================================================================//

def   _masksToMatch( masks, _null_match = lambda name: False ):
  if not masks:
    return _null_match
  
  if isString( masks ):
    masks = masks.split('|')
  
  re_list = []
  for mask in toSequence( masks ):
    re_list.append( "(%s)" % fnmatch.translate( os.path.normcase( mask ).strip() ) )
  
  re_str = '|'.join(re_list)
  
  return re.compile(re_str).match

#//===========================================================================//

def  findFiles( paths = ".", mask = ("*", ), exclude_mask = tuple(), exclude_subdir_mask = ('__*', '.*') ):
  
  found_files = []
  
  paths = toSequence(paths)
  
  match_mask = _masksToMatch( mask )
  match_exclude_mask = _masksToMatch( exclude_mask )
  match_exclude_subdir_mask = _masksToMatch( exclude_subdir_mask )
  
  for path in paths:
    for root, folders, files in os.walk( os.path.abspath( path ) ):
      for file_name in files:
        file_name_nocase = os.path.normcase( file_name )
        if (not match_exclude_mask(file_name_nocase)) and match_mask( file_name_nocase ):
          found_files.append( os.path.join(root, file_name) )
      
      folders[:] = ( folder for folder in folders if not match_exclude_subdir_mask( folder ) )
  
  found_files.sort()
  return found_files

#//===========================================================================//

def   findFileInPaths( paths, filename ):
  
  for path in paths:
    file_path = os.path.join( path, filename )
    if os.access( file_path, os.R_OK ):
      return os.path.normpath( file_path )
  
  return None

#//===========================================================================//

def   _getEnvPath( env = None ):
  
  if env is None:
    env = os.environ
  
  paths = env.get('PATH', '')
  if isString( paths ):
    paths = paths.split( os.pathsep )
  
  return paths

#//===========================================================================//

def   _getEnvPathExt( env = None, IS_WINDOWS = os.name == 'nt' ):
  
  if env is None:
    path_exts = os.environ.get('PATHEXT', '')
  else:
    path_exts = env.get('PATHEXT', None )
    if path_exts is None:
      path_exts = os.environ.get('PATHEXT', '')
      
  if not path_exts and IS_WINDOWS:
    return ('.exe','.cmd','.bat','.com')
  
  if isString( path_exts ):
    path_sep = os.pathsep if sys.platform != 'cygwin' else ';'
    path_exts = path_exts.split( path_sep )
  
  if not IS_WINDOWS:
    if '' not in path_exts:
      path_exts.insert(0,'')
  
  return path_exts

#//===========================================================================//

def   _findProgram( prog, paths, path_exts = None ):
  
  prog_ext = os.path.splitext(prog)[1]
  
  if not path_exts or (prog_ext and prog_ext in path_exts):
    path_exts = ('',)
  
  for path in paths:
    prog_path = os.path.expanduser( os.path.join( path, prog ) )
    for ext in path_exts:
      p = prog_path + ext
      if os.access( p, os.X_OK ):
        return os.path.normcase( p )
  
  return None

#//===========================================================================//

def   whereProgram( prog, env = None ):
  
  paths = _getEnvPath( env )
  path_exts = _getEnvPathExt( env )
  
  prog_path = _findProgram( prog, paths, path_exts )
  if prog_path is None:
    raise ErrorProgramNotFound( prog )
  
  return prog_path

#//===========================================================================//

class ProgramFinder( object ):
  __slots__ = (
    'prog',
    'paths',
    'exts',
    'result',
  )
  
  def   __init__(self, prog, paths, exts ):
    if not isString(prog):
      raise ErrorProgramName( prog )
    
    self.prog   = prog
    self.paths  = paths
    self.exts   = exts
    self.result = None
  
  def   __nonzero__(self):
    return bool(self.get())
  
  def   __bool__(self):
    return bool(self.get())
  
  def   __call__(self):
    return self.get()
  
  def   __str__(self):
    return self.get()
  
  def   get(self):
    progpath = self.result
    if progpath:
      return progpath
    
    prog_full_path = _findProgram( self.prog, self.paths, self.exts )
    if prog_full_path is None:
      prog_full_path = self.prog
    
    self.result = prog_full_path
    return prog_full_path
  
#//=======================================================//

def   findOptionalProgram( prog, env = None ):
  paths = _getEnvPath( env )
  path_exts = _getEnvPathExt( env )
  return ProgramFinder( prog, paths, path_exts )

#//===========================================================================//

def   findOptionalPrograms( progs, env = None ):
  paths = _getEnvPath( env )
  path_exts = _getEnvPathExt( env )
  return tuple( ProgramFinder( prog, paths, path_exts ) for prog in progs )

#//===========================================================================//

def  _normLocalPath( path ):

  if not path:
    return '.'

  path_sep = os.path.sep

  if path[-1] in (path_sep, os.path.altsep):
    last_sep = path_sep
  else:
    last_sep = ''

  path = os.path.normcase( os.path.normpath( path ) )

  return path + last_sep

#//===========================================================================//

try:
  _splitunc = os.path.splitunc
except AttributeError:
  def _splitunc( path ):
    return str(), path

def   splitDrive( path ):
  drive, path = os.path.splitdrive( path )
  if not drive:
    drive, path = _splitunc( path )
  
  return drive, path

#//===========================================================================//

def _splitPath( path ):
  drive, path = splitDrive( path )
  
  path = path.split( os.path.sep )
  path.insert( 0, drive )
  
  return path

#//===========================================================================//

def   _commonPrefixSize( *paths ):
  min_path = min( paths )
  max_path = max( paths )
  
  i = 0
  for i, path in enumerate( min_path[:-1] ):
    if path != max_path[i]:
      return i
  return i + 1

#//===========================================================================//

def   _relativeJoin( base_path, base_path_seq, path, sep = os.path.sep ):
  
  path = _splitPath( _normLocalPath( path ) )
  
  prefix_index = _commonPrefixSize( base_path_seq, path )
  if prefix_index == 0:
    drive = path[0]
    if drive:
      drive = drive.replace(':','').split( sep )
      del path[0]
      path[0:0] = drive
  else:
    path = path[prefix_index:]
  
  path.insert( 0, base_path )
  path = filter( None, path )
  
  return sep.join( path )

#//===========================================================================//

def   relativeJoinList( base_path, paths ):
  base_path = _normLocalPath( base_path )
  base_path_seq = _splitPath( base_path )
  return [ _relativeJoin( base_path, base_path_seq, path ) for path in toSequence( paths ) ]

#//===========================================================================//

def   relativeJoin( base_path, path ):
  base_path = _normLocalPath( base_path )
  base_path_seq = _splitPath( base_path )
  return _relativeJoin( base_path, base_path_seq, path )

#//===========================================================================//

def   changePath( path, dirname = None, name = None, ext = None, prefix = None ):
  
  path_dirname, path_filename = os.path.split( path )
  path_name, path_ext = os.path.splitext( path_filename )
  
  if dirname is None: dirname = path_dirname
  if name is None: name = path_name
  if ext is None: ext = path_ext
  if prefix: name = prefix + name
  
  path = dirname
  if path:
    path += os.path.sep
  
  return path + name + ext

#//===========================================================================//

def   groupPathsByDir( file_paths, wish_groups = 1, max_group_size = -1, pathGetter = None ):
  
  groups = ItemsGroups( len(file_paths), wish_groups, max_group_size )
  
  if pathGetter is None:
    pathGetter = lambda path: path
  
  files = []
  for file_path in file_paths:
    path = pathGetter( file_path )
    
    dir_path, file_name = os.path.split( path )
    dir_path = os.path.normcase( dir_path )
    
    files.append( (dir_path, file_path) )
  
  files.sort( key = operator.itemgetter(0) )
  
  last_dir = None
  
  for dir_path, file_path in files:
    
    if last_dir != dir_path:
      last_dir = dir_path
      groups.addGroup()
    
    groups.add( file_path )
  
  return groups.get()

#//===========================================================================//

class   Chdir (object):
  __slots__ = ('previous_path', )
  
  def   __init__(self, path = None ):
    self.previous_path = os.getcwd()
    
    if path:
      os.chdir( path )
  
  def   __enter__(self):
    return self
  
  def   __exit__(self, exc_type, exc_val, exc_tb):
    os.chdir( self.previous_path )
    return False
