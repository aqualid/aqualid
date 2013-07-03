import os
import re
import shutil
import hashlib
import itertools

import aql

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _readDeps( dep_file, _space_splitter_re = re.compile(r'(?<!\\)\s+') ):
  
  deps = aql.readTextFile( dep_file )
  
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

class GccCompilerImpl (aql.Builder):
  
  __slots__ = ( 'cmd', 'language', 'shared')
  
  def   __init__(self, options, language, shared ):
    self.language = language
    self.shared = shared
    
  #//-------------------------------------------------------//
  
  def   getCmd( self ):
    
    language = self.language
    options = self.options
    
    if language == 'c++':
      cmd = [ options.cxx.value() ]
    else:
      cmd = [ options.cc.value() ]
    
    cmd += ['-c', '-pipe', '-MMD', '-x', language ]
    if language == 'c++':
      cmd += options.cxxflags.value()
    else:
      cmd += options.cflags.value()
    
    if self.shared:
      cmd += ['-fPIC']
    
    cmd += options.ccflags.value()
    cmd += itertools.chain( *itertools.product( ['-D'], options.cppdefines.value() ) )
    cmd += itertools.chain( *itertools.product( ['-I'], options.cpppath.value() ) )
    cmd += itertools.chain( *itertools.product( ['-I'], options.ext_cpppath.value() ) )
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   getSignature( self ):
    return hashlib.md5( ''.join( self.cmd ).encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      options = self.options
      prefix = options.prefix.value()
      suffix = options.shobjsuffix.value() if self.shared else options.objsuffix.value()
      
      self.name = name = '.'.join( [ self.getName(), prefix, suffix ] )
      return name
    
    elif attr == 'signature':
      self.signature = signature = self.getSignature()
      return signature
    
    elif attr == 'cmd':
      self.cmd = cmd = self.getCmd()
      return cmd
    
    return super( GccCompilerImpl, self).__getattr__( attr )
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    return False
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    options = self.options
    
    prefix = options.prefix.value()
    suffix = options.shobjsuffix.value() if self.shared else options.objsuffix.value()
    
    source = node.sources()[0]
    obj_file = self.buildPath( source )
    
    cwd = obj_file.dir
    obj_file = obj_file.change( prefix = prefix ) + suffix
    dep_file = obj_file +'.d'
    
    cmd = list(self.cmd)
    cmd += ['-o', obj_file, '-MF', dep_file, str(source) ]
    
    result = aql.execCommand( cmd, cwd, file_flag = '@' )
    if result.failed():
      raise result
    
    node.setTargets( obj_file, itargets = dep_file, ideps = _readDeps( dep_file ) )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.cmd[0] + ': ' + ' '.join( map( str, node.sources() ) )


#//===========================================================================//

class GccCompiler(aql.Builder):
  
  __slots__ = ('compiler')
  
  def   __init__(self, options, language, shared ):
    self.compiler = GccCompilerImpl( options, language, shared )
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      self.name = name = self.compiler.name
      return name
    
    elif attr == 'signature':
      self.signature = signature = self.compiler.signature
      return signature
    
    return super(GccCompiler,self).__getattr__( attr )
  
  #//-------------------------------------------------------//
  
  def   actual( self, vfile, node ):
    return True
  
  #//-------------------------------------------------------//
  
  def   _splitNodes( self, vfile, node ):
    targets = []
    
    src_nodes = []
    for src_node in node.split( self.compiler ):
      if src_node.actual( vfile ):
        targets += src_node.targets()
      else:
        src_nodes.append( src_node )
    
    node.setTargets( targets )
    
    return src_nodes
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, vfile, node ):
    targets = []
    
    src_nodes = []
    for src_node in node.split( self.compiler ):
      if src_node.actual( vfile ):
        targets += src_node.targets()
      else:
        src_nodes.append( src_node )
    
    node.setTargets( targets )
    
    return src_nodes
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, vfile, node, pre_nodes ):
    
    targets = list( node.targets() )
    for pre_node in pre_nodes:
      targets += pre_node.targets()
    
    node.setTargets( targets )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.compiler.buildStr( node )

#//===========================================================================//

class GccArchiver(aql.Builder):
  
  __slots__ = ('cmd', 'target')
  
  def   __init__( self, options, target ):
    self.target = target
    
  #//-------------------------------------------------------//
  
  def   getCmd( self ):
    return [ self.options.lib.value(), 'rcs' ]
  #//-------------------------------------------------------//
  
  def   getSignature( self ):
    return hashlib.md5( ''.join( self.cmd ).encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      
      options = self.options
      
      prefix = options.libprefix.value() + options.prefix.value()
      suffix = options.libsuffix.value()
      
      self.name = name = '.'.join( [ self.getName(), self.target, prefix, suffix ] )
      return name
    
    elif attr == 'signature':
      self.signature = signature = self.getSignature()
      return signature
    
    elif attr == 'cmd':
      self.cmd = cmd = self.getCmd()
      return cmd
    
    return super(GccCompiler,self).__getattr__( attr )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    options = self.options
    prefix = options.libprefix.value() + options.prefix.value()
    suffix = options.libsuffix.value()
    
    obj_files = node.sources()
    archive = self.buildPath( self.target ).change( prefix = prefix ) + suffix
    
    cmd = list(self.cmd)
    
    cmd += [ archive ]
    cmd += aql.FilePaths( obj_files )
    
    cwd = self.buildPath()
    
    result = aql.execCommand( cmd, cwd, file_flag = '@' )
    if result.failed():
      raise result
    
    node.setTargets( archive )
  
  #//-------------------------------------------------------//
  
  def   buildStr( self, node ):
    return self.cmd[0] + ': ' + ' '.join( map( str, node.sources() ) )

#//===========================================================================//

class GccLinker(aql.Builder):
  
  __slots__ = ('cmd', 'language', 'target', 'shared' )
  
  def   __init__( self, options, target, language, shared ):
    self.language = language
    self.target = target
    self.shared = shared
    
  #//-------------------------------------------------------//
  
  def   getCmd( self ):
    
    language = self.language
    options = self.options
    
    if language == 'c++':
      cmd = [ options.cxx.value() ]
    else:
      cmd = [ options.cc.value() ]
    
    cmd += [ '-pipe' ]
    
    if self.shared:
      cmd += [ '-shared' ]
    
    cmd += options.linkflags.value()
    cmd += itertools.chain( *itertools.product( ['-L'], options.libpath.value() ) )
    cmd += itertools.chain( *itertools.product( ['-l'], options.libs.value() ) )
    
    return cmd
  
  #//-------------------------------------------------------//
  
  def   getSignature( self ):
    return hashlib.md5( ''.join( self.cmd ).encode('utf-8') ).digest()
  
  #//-------------------------------------------------------//
  
  def   __getattr__( self, attr ):
    
    if attr == 'name':
      options = self.options
      
      if self.shared:
        prefix = options.shlibprefix.value()
        suffix = options.shlibsuffix.value()
      else:
        prefix = ''
        suffix = options.progsuffix.value()
      
      self.name = name = '.'.join( [ self.getName(), self.target, prefix, suffix ] )
      return name
    
    elif attr == 'signature':
      self.signature = signature = self.getSignature()
      return signature
    
    elif attr == 'cmd':
      self.cmd = cmd = self.getCmd()
      return cmd
    
    return super(GccCompiler,self).__getattr__( attr )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    obj_files = node.sources()
    
    if self.shared:
      prefix = self.options.shlibprefix.value()
      suffix = self.options.shlibsuffix.value()
      
      target = self.buildPath( self.target ).change( prefix = prefix, ext = suffix )
    else:
      suffix = self.options.progsuffix.value()
      
      target = self.buildPath( self.target ) + suffix
    
    print("target: %s" % (target,))
    cmd = list(self.cmd)
    
    cmd_objs = [ '-o', target ]
    cmd_objs += map( str, obj_files )
    cmd[1:1] = cmd_objs
    
    cwd = self.buildPath()
    
    result = aql.execCommand( cmd, cwd, file_flag = '@' )
    if result.failed():
      raise result
    
    node.setTargets( target )
  
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

def   _findGcc( env, gcc_prefix, gcc_suffix ):
  gcc = '%sgcc%s' % (gcc_prefix, gcc_suffix)
  gcc = aql.whereProgram( gcc, env )
  
  gxx = None
  ar = None
  
  gcc_ext = os.path.splitext( gcc )[1]
  
  gcc_prefixes = [gcc_prefix, ''] if gcc_prefix else ['']
  gcc_suffixes = [gcc_suffix + gcc_ext, gcc_ext ] if gcc_suffix else [gcc_ext]
  
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
  result = aql.execCommand( [gcc, '-v'] )
  
  target_re = re.compile( r'^\s*Target:\s+(.+)$', re.MULTILINE )
  version_re = re.compile( r'^\s*gcc version\s+(.+)$', re.MULTILINE )
  
  out = result.err
  
  match = target_re.search( out )
  target = match.group(1).strip() if match else ''
  
  match = version_re.search( out )
  version = str(aql.Version( match.group(1).strip() if match else '' ))
  
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
    'cc_name':      'gcc',
    'cc_ver':       version,
    'target_os':    target_os,
    'target_arch':  target_arch,
  }
  
  return specs

#//===========================================================================//

class ToolGccCommon( aql.Tool ):
  
  @staticmethod
  def   setup( options, env ):
    
    gcc_prefix = options.gcc_prefix.value()
    gcc_suffix = options.gcc_suffix.value()
    
    """
    cfg_keys = ( gcc_prefix, gcc_suffix )
    cfg_deps = ( str(options.env['PATH']), )
    
    specs = self.LoadValues( project, cfg_keys, cfg_deps )
    if cfg is None:
      info = _getGccInfo( env, gcc_prefix, gcc_suffix )
      self.SaveValues( project, cfg_keys, cfg_deps, specs )
    """
    
    gcc, gxx, ar = _findGcc( env, gcc_prefix, gcc_suffix )
    specs = _getGccSpecs( gcc )
    specs['cc'] = gcc
    specs['cxx'] = gxx
    specs['lib'] = ar
    
    return specs
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   options():
    
    options = aql.optionsCCpp()
    
    options.gcc_path  = aql.PathOptionType()
    options.gcc_target = aql.StrOptionType( ignore_case = True )
    options.gcc_prefix = aql.StrOptionType( description = "GCC C/C++ compiler prefix" )
    options.gcc_suffix = aql.StrOptionType( description = "GCC C/C++ compiler suffix" )
    
    if_ = options.If()
    if_windows = if_.target_os.eq('windows')
    
    options.objsuffix     = '.o'
    options.shobjsuffix   = '.os'
    options.libprefix     = 'lib'
    options.libsuffix     = '.a'
    options.shlibprefix   = 'lib'
    options.shlibsuffix   = '.so'
    if_windows.progsuffix = '.exe'
    
    if_windows.target_subsystem.eq('console').linkflags += '-Wl,--subsystem,console'
    if_windows.target_subsystem.eq('windows').linkflags += '-Wl,--subsystem,windows'
    
    if_.debug_symbols.isTrue().ccflags += '-g'
    if_.debug_symbols.isFalse().linkflags += '-Wl,--strip-all'
    
    if_.runtime_link.eq('static').linkflags += '-static-libgcc'
    if_.runtime_link.eq('shared').linkflags += '-shared-libgcc'
    
    if_.target_os.eq('windows').runtime_thread.eq('multi').ccflags += '-mthreads'
    if_.target_os.ne('windows').runtime_thread.eq('multi').ccflags += '-pthreads'
    
    if_.optimization.eq('speed').occflags += '-O3'
    if_.optimization.eq('size').occflags  += '-Os'
    if_.optimization.eq('off').occflags   += '-O0'
    
    if_.inlining.eq('off').occflags   += '-fno-inline'
    if_.inlining.eq('on').occflags    += '-finline'
    if_.inlining.eq('full').occflags  += '-finline-functions'
    
    if_.no_rtti.isTrue().cxxflags   += '-fno-rtti'
    if_.no_rtti.isFalse().cxxflags  += '-frtti'
    
    if_.no_exceptions.isTrue().cxxflags   += '-fno-exceptions'
    if_.no_exceptions.isFalse().cxxflags  += '-fexceptions'
    
    if_.warning_as_error.isTrue().ccflags += '-Werror'
    
    if_profiling_true = if_.profile.isTrue()
    if_profiling_true.ccflags += '-pg'
    if_profiling_true.linkflags += '-pg'
    if_profiling_true.linkflags -= '-Wl,--strip-all'
    
    options.setGroup( "C/C++ compiler" )
    
    return options
    
  #//-------------------------------------------------------//
  
  def   FilterLibrary( self, options, libraries ):
    pass


#//===========================================================================//

@aql.tool('c++', 'g++', 'cpp', 'cxx')
class ToolGxx( ToolGccCommon ):
  
  def   Object( self, options ):
    return GccCompiler( options, 'c++', shared = False )
  
  def   SharedObject( self, options ):
    return GccCompiler( options, 'c++', shared = True )
  
  def   Library( self, options, target ):
    return GccArchiver( options, target )
  
  def   SharedLibrary( self, options, target ):
    return GccLinker( options, target, 'c++', shared = True )
  
  def   Program( self, options, target ):
    return GccLinker( options, target, 'c++', shared = False )

#//===========================================================================//
  
@aql.tool('c', 'gcc', 'cc')
class ToolGcc( ToolGccCommon ):
  
  def   Object( self, options ):
    return GccCompiler( options, 'c', shared = False )
  
  def   SharedObject( self, options ):
    return GccCompiler( options, 'c', shared = True )
  
  def   Library( self, options, target ):
    return GccArchiver( options, target )
  
  def   SharedLibrary( self, options, target ):
    return GccLinker( options, target, 'c', shared = True )
  
  def   Program( self, options, target ):
    return GccLinker( options, target, 'c', shared = False )
