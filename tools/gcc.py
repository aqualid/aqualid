import os
import re
import shutil
import hashlib
import itertools

from aql.nodes import Node, Builder
from aql.utils import execCommand, readTextFile, Tempfile, Tempdir
from aql.types import FilePath, FilePaths, Version
from aql.options import Options, BoolOptionType, ListOptionType, PathOptionType, StrOptionType, VersionOptionType, cppToolCommonOptions

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _readDeps( dep_file, _space_splitter_re = re.compile(r'(?<!\\)\s+') ):
  
  deps = readTextFile( dep_file )
  
  dep_files = []
  
  target_sep = ': '
  target_sep_len = len(target_sep)
  
  for line in deps.splitlines():
    pos = line.find( target_sep )
    if pos >= 0:
      line = line[ pos + target_sep_len: ]
    
    line = line.rstrip('\\ ').strip()
    
    tmp_dep_files = filter( None, _space_splitter_re.split( line ) )
    tmp_dep_files = [dep_file.replace('\\ ', ' ') for dep_file in tmp_dep_files ]
    
    dep_files += tmp_dep_files
  
  return dep_files[1:]  # skip the source file

#//===========================================================================//

def   _addPrefix( prefix, values ):
  return map( lambda v, prefix = prefix: prefix + v, values )

#//===========================================================================//

class GccCompilerImpl (Builder):
  
  __slots__ = ( 'cmd', )
  
  def   __init__(self, options, language, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.build_dir = options.build_dir.value()
    self.do_path_merge = options.do_build_path_merge.value()
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    self.cmd = self.__cmd( options, language )
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

#//===========================================================================//

class GccCompiler(Builder):
  
  __slots__ = ('compiler')
  
  def   __init__(self, options, language, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    self.compiler = GccCompilerImpl( options, language, scontent_type, tcontent_type )
    self.signature = self.compiler.signature
  
  #//-------------------------------------------------------//
  
  def   __groupSources( self, src_values, wish_groups ):
    
    src_files = FilePaths()
    src_map = {}
    
    for value in src_values:
      file = FilePath( value.name )
      src_files.append( file )
      src_map[ file ] = value
    
    src_file_groups = src_files.groupUniqueNames( wish_groups = wish_groups, max_group_size = -1 )
    
    groups = []
    
    for group in src_file_groups:
      groups.append( [ src_map[name] for name in group ] )
    
    return groups
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, build_manager, vfile, node ):
    
    src_groups = self.__groupSources( node.sources(), wish_groups = build_manager.jobs() )
    
    compiler = self.compiler
    pre_nodes = [ Node( compiler, src_values ) for src_values in src_groups ]
    
    return pre_nodes
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, build_manager, vfile, node, pre_nodes ):
    
    targets = self.nodeTargets()
    
    for pre_node in pre_nodes:
      targets += pre_node.nodeTargets()
    
    node.save( vfile, targets )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.compiler.buildStr( node )

#//===========================================================================//

class GccArchiver(Builder):
  
  __slots__ = ('cmd', 'target')
  
  def   __init__(self, target, options, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.target = target
    self.build_dir = options.build_dir.value()
    self.do_path_merge = options.do_build_path_merge.value()
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    self.cmd = [ options.ar.value(), 'rcs' ]
    self.signature = self.__signature()
    
    self.name = self.name + '.' + str(target)
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    return hashlib.md5( ''.join( self.cmd ).encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    obj_files = node.sources()
    archive = self.buildPath( self.target ).change( prefix = 'lib', ext = '.a', )
    
    cmd = list(self.cmd)
    
    cmd += [ archive ]
    cmd += FilePaths( obj_files )
    
    cwd = self.buildPath()
    
    result = execCommand( cmd, cwd, file_flag = '@' )
    if result.failed():
      raise result
    
    return self.nodeTargets( archive )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.cmd[0] + ': ' + ' '.join( map( str, node.sources() ) )

#//===========================================================================//

class GccLinker(Builder):
  
  __slots__ = ('cmd', 'target')
  
  def   __init__(self, target, options, scontent_type = NotImplemented, tcontent_type = NotImplemented ):
    
    self.target = target
    self.build_dir = options.build_dir.value()
    self.do_path_merge = options.do_build_path_merge.value()
    self.scontent_type = scontent_type
    self.tcontent_type = tcontent_type
    
    self.cmd = self.__cmd( options, language )
    self.signature = self.__signature()
    
    self.name = self.name + '.' + str(target)
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __cmd( options, language ):
    
    if language == 'c++':
      cmd = [ options.cxx.value() ]
    else:
      cmd = [ options.cc.value() ]
    
    cmd += [ '-pipe' ]
    
    cmd += options.linkflags.value()
    cmd += itertools.product( ['-L'], options.libpath.value() )
    cmd += itertools.product( ['-l'], options.libs.value() )
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   __signature( self ):
    return hashlib.md5( ''.join( self.cmd ).encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, vfile, node ):
    
    obj_files = node.sources()
    archive = self.buildPath( self.target ).change( prefix = 'lib', ext = '.a', )
    
    cmd = list(self.cmd)
    
    cmd += [ archive ]
    cmd += FilePaths( obj_files )
    
    cwd = self.buildPath()
    
    result = execCommand( cmd, cwd, file_flag = '@' )
    if result.failed():
      raise result
    
    return self.nodeTargets( archive )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.cmd[0] + ': ' + ' '.join( map( str, node.sources() ) )

#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

def   _checkProg( gcc_path, prog ):
  prog = os.path.join( gcc_path, prog )
  return prog if os.path.isfile( prog ) else None

#//===========================================================================//

def   _findGcc( env, gcc_prefix, gcc_suffix )
  gcc = '%sgcc%s' % (gcc_prefix, gcc_suffix)
  gcc = whereProgram( gcc, env.copy( value_type = str ) )
  
  gxx = None
  ar = None
  
  gcc_prefixes = [gcc_prefix, ''] if gcc_prefix else ['']
  gcc_suffixes = [gcc_suffix, ''] if gcc_suffix else ['']
  
  gcc_path = os.path.dirname( gcc )
  
  for gcc_prefix, gcc_suffix in itertools.product( gcc_prefixes, gcc_suffixes ):
    if not gxx: gxx = _checkProg( gcc_path, '%sg++%s' % (gcc_prefix, gcc_suffix) )
    if not gxx: gxx = _checkProg( gcc_path, '%sc++%s' % (gcc_prefix, gcc_suffix) )
    if not ar:  ar  = _checkProg( gcc_path, '%sar%s' % (gcc_prefix, gcc_suffix) )
  
  if not gxx or not ar:
    raise NotImplementedError()
  
  return gcc, gxx, ar

#//===========================================================================//

def   _getGccSpecs( gcc ):
  result = execCommand( [gcc, '-v'] )
  
  target_re = re.compile( r'^\s*Target:\s+(.+)$', re.MULTILINE )
  version_re = re.compile( r'^\s*gcc version\s+(.+)$', re.MULTILINE )
  
  out = result.err
  
  match = target_re.search( out )
  target = match.group(1).strip() if match else ''
  
  match = version_re.search( out )
  version = str(Version( match.group(1).strip() if match else '' ))
  
  if target == 'mingw32':
    target_arch = 'x86-32'
    target_os = 'windows'
  
  else:
    target_list = target.split('-')
    
    target_list_len = len( target_list )
    
    if target_list_len == 2:
      target_arch = target_list[0]
      target_os = target_list[1]
    elif target_list_len > 2:
      target_arch = target_list[0]
      target_os = target_list[2]
    else:
      target_arch = ''
      target_os = ''
  
  specs = {
    'version': version,
    'target_os': target_os,
    'target_arch': target_arch,
  }
  
  return specs

#//===========================================================================//

def   _getGccInfo( env, gcc_prefix, gcc_suffix ):
  gcc, gxx, ar = _findGcc( env, gcc_prefix, gcc_suffix )
  specs = _getGccSpecs( gcc )
  specs['gcc'] = gcc
  specs['gxx'] = gxx
  specs['ar'] = ar
  
  return specs

#//===========================================================================//

@aql.tool('gcc', 'g++', 'c++', 'c')
class ToolGcc( Tool ):
  
  def   __init__( self, project, options ):
    
    if not options.cc_name.setDefault( "gcc" ):   raise NotImplementedError()
    
    env = options.env.value().copy( value_type = str )
    gcc_prefix = options.gcc_prefix.value()
    gcc_suffix = options.gcc_suffix.value()
    
    """
    cfg_keys = ( gcc_prefix, gcc_suffix )
    cfg_deps = ( str(options.env['PATH']), )
    
    specs = self.LoadValues( prj, cfg_keys, cfg_deps )
    if cfg is None:
      info = _getGccInfo( env, gcc_prefix, gcc_suffix )
      self.SaveValues( prj, cfg_keys, cfg_deps, specs )
    """
    
    info = _getGccInfo( env, gcc_prefix, gcc_suffix )
    
    if not options.cc_ver.setDefault( info['version'] ):           raise NotImplementedError()
    if not options.target_os.setDefault( info['target_os'] ):      raise NotImplementedError()
    if not options.target_arch.setDefault( info['target_arch'] ):  raise NotImplementedError()
    
    options.cc = info['gcc']
    options.cxx = info['gxx']
    options.ar = info['ar']
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   options():
    options = cppToolCommonOptions()
    
    options.gcc_path = PathOptionType()
    options.gcc_target = StrOptionType( ignore_case = True )
    options.gcc_prefix = StrOptionType( description = "GCC C/C++ compiler prefix" )
    options.gcc_suffix = StrOptionType( description = "GCC C/C++ compiler suffix" )
    
    options.setGroup( "C/C++ compiler" )
    
    return options
  
  #//-------------------------------------------------------//
  
  @aql.builder
  def   CompileCpp( self, project, options, sources ):
    cpp_compiler = GccCompiler( options, 'c++' )
    return Node( cpp_compiler, sources )
  
  #//-------------------------------------------------------//
  
  @aql.builder
  def   CompileC( self, prj, options, sources ):
    c_compiler = GccCompiler( options, 'c' )
    return Node( c_compiler, sources )
  
  @aql.builder
  def   LinkCppLibrary( self, env, sources, options ):
    pass
  
  @aql.builder
  def   LinkCLibrary( self, env, sources, options ):
    pass
  
  @aql.builder
  def   LinkSharedCppLibrary( self, env, sources, options ):
    pass
  
  @aql.builder
  def   LinkSharedCLibrary( self, env, sources, options ):
    pass
  
  @aql.builder
  def   LinkCppProgram( self, env, sources, options ):
    pass

#//===========================================================================//
  

