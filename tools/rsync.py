import os
import re
import sys
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

#//===========================================================================//

def   rsyncOptions():
  
  options = Options()
  
  options.rsync = PathOptionType( description = "File path to rsync program." )
  options.rsync_cygwin = BoolOptionType( description = "Is rsync from Cygwin." )
  
  options.rsync_host = StrOptionType( description = "Rsync remote host." )
  options.rsync_login = StrOptionType( description = "Rsync user's SSH login on the remote host." )
  options.rsync_key_file = PathOptionType( description = "Rsync user's SSH key file for the remote host." )
  
  options.rsync = 'rsync'
  options.If().rsync.has('cygwin').rsync_cygwin = True

#//===========================================================================//

"""
env.RsyncGet( '/work/cp/kh', local_path = src_dir )

prog = env.LinkProgram( target = 'test', obj_files )

env.RsyncPut( prog, remote_path = '/work/cp/bin/' )

"""

class SyncLocalBuilder (Builder):
  # rsync -avzub --exclude-from=files.flt --delete-excluded -e "ssh -i dev.key" c4dev@dev:/work/cp/bp2_int/components .
  
  __slots__ = ( 'rsync', )
  
  def   __init__(self, host, login, key_file, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    rsync_prog = options.rsync.value()
    
    host = RemoteHost( host, login, key_file )
    
    self.rsync = Rsync( rsync_prog, host, cygwin_paths = options.rsync_cygwin.value(), options.env.value() )
    
    self.name = self.name + '.' + host.address
    self.signature = bytearray()
  
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
