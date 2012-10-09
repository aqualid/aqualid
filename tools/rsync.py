import os
import re
import shutil
import hashlib
import itertools

from aql_node import Node
from aql_builder import Builder
from aql_utils import execCommand, toSequence
from aql_path_types import FilePath, FilePaths
from aql_errors import InvalidSourceValueType, BuildError
from aql_options import Options
from aql_temp_file import Tempfile, Tempdir
from aql_option_types import OptionType, BoolOptionType, EnumOptionType, RangeOptionType, ListOptionType, PathOptionType, StrOptionType, VersionOptionType

#//===========================================================================//

class RemoteHost (object):
  __slots__ = ('address', 'login', 'key_file')
  
  def   __init__( self, host, login, key_file ):
    self.address = address
    self.login = login
    self.key_file = key_file

#//===========================================================================//

class   RemotePathMapping (object):
    __slots__ = ( 'local_paths', 'remote_paths' )
    
    #//-------------------------------------------------------//
    
    @staticmethod
    def   __normRemotePath( path ):
      return os.path.normpath( path ).replace('\\', '/') + '/'
    
    @staticmethod
    def   __normLocalPath( path ):
      #~ return os.path.normpath( path ).replace('\\', '/') + '/'
      return os.path.normpath( path ) + os.path.sep
    
    #//-------------------------------------------------------//
    
    def   __init__(self, mappings = {} ):
      
      self.local_paths = []
      self.remote_paths = []
      
      try:
        mappings = mappings.items()
      except AttributeError:
        pass
      
      self.local_paths = []
      self.remote_paths = []
      
      for local_path, remote_path in mappings:
        self.add( local_path, remote_path )
    
    #//-------------------------------------------------------//
    
    def   add( self, local_path, remote_path ):
      local_path = self.__normLocalPath( local_path )
      remote_path = self.__normRemotePath( remote_path )
      
      remove_locals = []
      
      for lpaths in self.local_paths:
        if (lpaths[0] == local_path) or (lpaths[1] == remote_path):
          remove_locals.append( lpaths )
      
      for lpaths in remove_locals:
        self.local_paths.remove( lpaths )
      
      remove_remotes = []
      
      for rpaths in self.remote_paths:
        if (rpaths[1] == local_path) or (rpaths[0] == remote_path):
          remove_remotes.append( rpaths )
      
      for rpaths in remove_remotes:
        self.remote_paths.remove( rpaths )
      
      self.local_paths.append( (local_path, remote_path) )
      self.remote_paths.append( (remote_path, local_path) )
      
      self.local_paths.sort( key = lambda v: len(v[0]), reverse = True )
      self.remote_paths.sort( key = lambda v: len(v[0]), reverse = True )
    
    #//-------------------------------------------------------//
    
    def   localPath( self, remote_path ):
      remote_path = self.__normRemotePath( remote_path )
      
      for rpath, lpath in self.remote_paths:
        if remote_path.startswith( rpath ):
          return self.__normLocalPath( lpath + '/' + remote_path[len(rpath):-1] )
      
      return ''
    
    #//-------------------------------------------------------//
    
    def   remotePath( self, local_path ):
      local_path = self.__normLocalPath( local_path )
      
      for lpath, rpath in self.local_paths:
        if local_path.startswith( lpath ):
          return self.__normRemotePath( rpath + '/' + local_path[len(lpath):] )[:-1]
      
      return ''

#//===========================================================================//

class   Rsync( object ):
  
  __slots__ = (
    'cmd',
    'host',
    'path_map',
    'env',
  )
  
  def   __init__( self, rsync, host, path_map, env = None ):
    
    self.cmd = (rsync, '-avzub')
    self.host = host
    self.path_map = path_map
    self.env = env
  
  #//-------------------------------------------------------//
  
  def   __sync( self, local_path, remote_path, sync_local, exclude ):
    cmd = list( self.cmd )
    
    excludes = []
    
    for args in itertools.product( ['--exclude'], toSequence( exclude ) ):
      excludes += args
    
    if excludes:
      cmd += excludes
      cmd.append('--delete-excluded')
    
    host = self.host
    if host:
      remote_path = "%s@%s:%s" % (host.login, host.address, remote_path)
      cmd += ['-e', 'ssh -o StrictHostKeyChecking=no -i ' + str(self.host.key_file) ]
    
    if sync_local:
      cmd += [ remote_path, local_path ]
    else:
      cmd += [ local_path, remote_path ]
    
    result = execCommand( cmd, env = self.env )
    if result.failed():
      raise result
  
  #//-------------------------------------------------------//
  
  def   syncLocal( self, remote_path, exclude = None ):
    local_path = self.path_map.localPath( remote_path )
    remote_path = self.path_map.remotePath( local_path )
    self.__sync( local_path, remote_path, sync_local = True, exclude = exclude )
  
  #//-------------------------------------------------------//
  
  def   syncRemote( self, local_path, exclude = None ):
    remote_path = self.path_map.remotePath( local_path )
    local_path = self.path_map.localPath( remote_path )
    self.__sync( local_path, remote_path, sync_local = False, exclude = exclude )

#//===========================================================================//

def   rsyncOptions():
  
  options = Options()
  
  options.rsync = PathOptionType( description = "File path to rsync program." )
  options.rsync_flags = ListOptionType( description = "Rsync program options." )
  options.rsync_host = StrOptionType( description = "Rsync remote host." )
  options.rsync_login = StrOptionType( description = "Rsync user's SSH login in the remote host." )
  options.rsync_key_file = PathOptionType( description = "Rsync user's SSH key file for the remote host." )
  options.rsync_path_map = DictOptionType( value_type = PathOptionType(), description = "Rsync user's SSH key file for the remote host." )
  
  options.rsync_flags = '-avzub'
  options.rsync = 'rsync'

#//===========================================================================//

class SyncLocalBuilder (Builder):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  __slots__ = ( 'cmd', )
  
  def   __init__(self, options, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    self.cmd = self.__cmd( options )
    self.signature = self.__signature()
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __cmd( options, language ):
    
    if language == 'c++':
      cmd = [ options.cxx.value() ]
    else:
      cmd = [ options.cc.value() ]
    
    cmd += ['-c', '-pipe', '-MMD', '-x', language ]
    if language == 'c++':
      cmd += options.cxxflags.value()
    else:
      cmd += options.cflags.value()
    
    cmd += options.ccflags.value()
    cmd += itertools.product( ['-D'], options.cppdefines.value() )
    cmd += itertools.product( ['-I'], options.cpppath.value() )
    cmd += itertools.product( ['-I'], options.ext_cpppath.value() )
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    return hashlib.md5( ''.join( self.cmd ).encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   __buildOne( self, vfile, src_file_value ):
    with Tempfile( suffix = '.d' ) as dep_file:
      
      src_file = src_file_value.name
      
      cmd = list(self.cmd)
      
      cmd += [ '-MF', dep_file.name ]
      
      obj_file = self.buildPath( src_file ) + '.o'
      cmd += [ '-o', obj_file ]
      cmd += [ src_file ]
      
      cwd = self.buildPath()
      
      result = execCommand( cmd, cwd, file_flag = '@' )
      if result.failed():
        raise result
      
      return self.nodeTargets( obj_file, ideps = _readDeps( dep_file.name ) )
  
  #//===========================================================================//

  def   __buildMany( self, vfile, src_file_values, src_nodes, targets ):
    
    build_dir = self.buildPath()
    
    src_files = FilePaths( src_file_values )
    
    with Tempdir( dir = build_dir ) as tmp_dir:
      cwd = FilePath( tmp_dir )
      
      cmd = list(self.cmd)
      cmd += src_files
      
      tmp_obj_files, tmp_dep_files = src_files.change( dir = cwd, ext = ['.o','.d'] )
      
      obj_files = self.buildPaths( src_files ).add('.o')
      
      result = execCommand( cmd, cwd, file_flag = '@' )
      
      move_file = os.rename
      
      for src_node, obj_file, tmp_obj_file, tmp_dep_file in zip( src_nodes, obj_files, tmp_obj_files, tmp_dep_files ):
        
        if not os.path.isfile( tmp_obj_file ):
          continue
        
        if os.path.isfile( obj_file ):
          os.remove( obj_file )
        move_file( tmp_obj_file, obj_file )
        
        node_targets = self.nodeTargets( obj_file, ideps = _readDeps( tmp_dep_file ) )
        
        src_node.save( vfile, node_targets )
        
        targets += node_targets
      
      if result.failed():
        raise result
    
    return targets
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    src_file_values = node.sources()
    
    if len(src_file_values) == 1:
      targets = self.__buildOne( vfile, src_file_values[0] )
    else:
      targets = self.nodeTargets()
      values = []
      nodes = []
      for src_file_value in src_file_values:
        node = Node( self, src_file_value )
        if node.actual( vfile ):
          targets += node.nodeTargets()
        else:
          values.append( src_file_value )
          nodes.append( node )
      
      num = len(values)
      
      if num == 1:
        node_targets = self.__buildOne( vfile, values[0] )
        nodes[0].save( vfile, node_targets )
        targets += node_targets
      elif num > 0:
        self.__buildMany( vfile, values, nodes, targets )
    
    return targets
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.cmd[0] + ': ' + ' '.join( map( str, node.sources() ) )
