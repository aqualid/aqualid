import os
import itertools

import aql

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _addPrefix( prefix, values ):
  prefix = prefix.lstrip()
  
  if not prefix:
    return values
  
  if prefix[-1] == ' ':
    prefix = prefix.rstrip()
    return tuple( itertools.chain( *itertools.product( (prefix,), values ) ) )
  
  return tuple( "%s%s" % (prefix, value ) for value in values ) 

#//===========================================================================//

def   _addIxes( prefix, suffix, values ):
  prefix = prefix.lstrip()
  suffix = suffix.strip()
  
  sep_prefix = prefix and (prefix[-1] == ' ')
  result = []
  
  for value in values:
    value = "%s%s" % (value, suffix)
    if prefix:
      if sep_prefix:
        result += [ prefix, value ]
      else:
        result.append( "%s%s" % (prefix, value) )
    else:
      result.append( value )
    
  return result 

#//===========================================================================//

def   _absFilePaths( file_paths ):
  return tuple( os.path.normcase( os.path.abspath( path ) ) for path in file_paths )

#//===========================================================================//

def   _preprocessorOptions( options ):
  
  options.cppdefines = aql.ListOptionType( unique = True, description = "C/C++ preprocessor defines", separators = None )
  options.defines = options.cppdefines
  options.cppdefines_prefix = aql.StrOptionType( description = "Flag for C/C++ preprocessor defines." )
  options.cppdefines_flags = aql.ListOptionType( separators = None )
  options.cppdefines_flags += aql.SimpleOperation( _addPrefix, options.cppdefines_prefix, options.cppdefines )
  
  options.cpppath = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor paths to headers", separators = None )
  options.include = options.cpppath
  options.cpppath_prefix  = aql.StrOptionType( description = "Flag for C/C++ preprocessor paths." )
  options.cpppath_flags = aql.ListOptionType( separators = None )
  options.cpppath_flags = aql.SimpleOperation( _addPrefix, options.cpppath_prefix, aql.SimpleOperation( _absFilePaths, options.cpppath ) )
  
  options.ext_cpppath   = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor path to external headers", separators = None )
  options.ext_include   = options.ext_cpppath
  options.cpppath_flags += aql.SimpleOperation( _addPrefix, options.cpppath_prefix, aql.SimpleOperation( _absFilePaths, options.ext_cpppath ) )
  options.ext_cpppath   = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor path to external headers", separators = None )
  options.sys_cpppath   = aql.ListOptionType( value_type = aql.PathOptionType(), description = "C/C++ preprocessor path to standard headers", separators = None )

#//===========================================================================//

def   _compilerOptions( options ):
  
  options.language = aql.EnumOptionType( values = [('c++', 'cpp'), 'c'], default = 'c++', description = 'Current language' )
  options.lang = options.language
  
  options.objsuffix = aql.StrOptionType( description = "Object file suffix." )
  options.shobjsuffix = aql.StrOptionType( description = "Shared object file suffix." )
  
  options.shobjsuffix = options.objsuffix
  
  options.cxxflags = aql.ListOptionType( description = "C++ compiler flags", separators = None )
  options.cflags = aql.ListOptionType( description = "C++ compiler flags", separators = None )
  options.ccflags = aql.ListOptionType( description = "Common C/C++ compiler flags", separators = None )
  options.occflags = aql.ListOptionType( description = "Common C/C++ compiler optimization flags", separators = None )
  
  options.cc      = aql.PathOptionType( description = "C/C++ compiler program" )
  options.cc_name = aql.StrOptionType( is_tool_key = True, ignore_case = True, description = "C/C++ compiler name" )
  options.cc_ver  = aql.VersionOptionType( is_tool_key = True, description = "C/C++ compiler version" )
  options.cc_cmd  = aql.ListOptionType( description = "C/C++ compiler full command", separators = None )
  
  options.cc_cmd = options.cc
  options.If().language.eq('c++').cc_cmd += options.cxxflags
  options.If().language.eq('c').cc_cmd += options.cflags
  options.cc_cmd += options.ccflags + options.occflags + options.cppdefines_flags + options.cpppath_flags
  
  options.cxxstd = aql.EnumOptionType( values = ['default', ('c++98', 'c++03'), ('c++11', 'c++0x'), ('c++14','c++1y') ], default = 'default',
                                       description = 'C++ language standard.' )
  
#//===========================================================================//

def   _resourceCompilerOptions( options ):
  options.rc = aql.PathOptionType( description = "C/C++ resource compiler program" )
  options.ressuffix = aql.StrOptionType( description = "Compiled resource file suffix." )
  
  options.rcflags = aql.ListOptionType( description = "C/C++ resource compiler flags", separators = None )
  options.rc_cmd = aql.ListOptionType( description = "C/C++ resource resource compiler full command", separators = None )
  
  options.rc_cmd = [ options.rc ] + options.rcflags + options.cppdefines_flags + options.cpppath_flags

#//===========================================================================//

def   _linkerOptions( options ):
  
  options.libprefix = aql.StrOptionType( description = "Static library archiver prefix." )
  options.libsuffix = aql.StrOptionType( description = "Static library archiver suffix." )
  options.libflags  = aql.ListOptionType( description = "Static library archiver flags", separators = None )
  options.olibflags = aql.ListOptionType( description = "Static library archiver optimization flags", separators = None )
  options.lib       = aql.PathOptionType( description = "Static library archiver program" )
  options.lib_cmd   = aql.ListOptionType( description = "Static library archiver full command", separators = None )
  options.lib_cmd   = [ options.lib ] + options.libflags + options.olibflags
  
  options.shlibprefix = aql.StrOptionType( description = "Shared library prefix." )
  options.shlibsuffix = aql.StrOptionType( description = "Shared library suffix." )
  
  options.libpath = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True,
                                        description = "Paths to external libraries", separators = None )
  options.libpath_prefix  = aql.StrOptionType( description = "Flag for library paths." )
  options.libpath_flags = aql.ListOptionType( separators = None )
  options.libpath_flags = aql.SimpleOperation( _addPrefix, options.libpath_prefix, aql.SimpleOperation( _absFilePaths, options.libpath ) )
  
  options.libs  = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True,
                                      description = "Linking external libraries", separators = None )
  options.libs_prefix  = aql.StrOptionType( description = "Prefix flag for libraries." )
  options.libs_suffix  = aql.StrOptionType( description = "Suffix flag for libraries." )
  options.libs_flags = aql.ListOptionType( separators = None )
  options.libs_flags = aql.SimpleOperation( _addIxes, options.libs_prefix, options.libs_suffix, options.libs )
  
  options.progsuffix = aql.StrOptionType( description = "Program suffix." )
  options.linkflags  = aql.ListOptionType( description = "Linker flags", separators = None )
  options.olinkflags = aql.ListOptionType( description = "Linker optimization flags", separators = None )
  options.link       = aql.PathOptionType( description = "Linker program" )
  options.link_cmd   = aql.ListOptionType( description = "Linker full command", separators = None )
  options.link_cmd   = [ options.link ] + options.linkflags + options.olinkflags + options.libpath_flags + options.libs_flags

#//===========================================================================//

def   _getCppOptions():
  options = aql.Options()
  _preprocessorOptions( options )
  _compilerOptions( options )
  _resourceCompilerOptions( options )
  _linkerOptions( options )
  
  return options

#//===========================================================================//

def   _getResOptions():
  options = aql.Options()
  _preprocessorOptions( options )
  _resourceCompilerOptions( options )
  
  return options

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonCppCompiler (aql.FileBuilder):
  
  NAME_ATTRS = ( 'prefix', 'suffix' )
  SIGNATURE_ATTRS = ('cmd', )
  
  #//-------------------------------------------------------//
  
  #noinspection PyUnusedLocal
  def   __init__(self, options, shared ):
    
    self.prefix = options.prefix.get()
    self.suffix = options.shobjsuffix.get() if shared else options.objsuffix.get()
    self.shared = shared
    
    ext_cpppath = list( options.ext_cpppath.get() )
    ext_cpppath += options.sys_cpppath.get()
    
    self.ext_cpppath = tuple( set( os.path.normcase( os.path.abspath( folder ) ) + os.path.sep for folder in ext_cpppath ) )
    
    self.cmd = list( options.cc_cmd.get() )
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, node ):
    
    if node.builder_data:
      return None
    
    src_groups = self.groupSourcesByBuildDir( node )
    if len(src_groups) < 2:
      return None
    
    node.updateDepValues()
    pre_nodes = []
    for src_group in src_groups:
      pre_node = node.copy( src_group )
      pre_node.builder_data = True
      
      pre_nodes.append( pre_node )
    
    return pre_nodes

  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, node, pre_nodes ):
    
    targets = []
    for pre_node in pre_nodes:
      targets += pre_node.getTargetValues()
    
    node.targets = targets
    
    return True
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   buildBatch( self, node ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   getTraceName( self, brief ):
    if brief:
      name = self.cmd[0]
      name = os.path.splitext( os.path.basename( name ) )[0]
    else:
      name = ' '.join( self.cmd )
    
    return name

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonResCompiler (aql.FileBuilder):
  
  NAME_ATTRS = ( 'prefix', 'suffix' )
  SIGNATURE_ATTRS = ('cmd', )
  
  #//-------------------------------------------------------//
  
  #noinspection PyUnusedLocal
  def   __init__(self, options ):
    
    self.prefix = options.prefix.get()
    self.suffix = options.ressuffix.get()
    
    # ext_cpppath = list( options.ext_cpppath.get() )
    # ext_cpppath += options.sys_cpppath.get()
    # 
    # self.ext_cpppath = tuple( set( os.path.normcase( os.path.abspath( folder ) ) + os.path.sep for folder in ext_cpppath ) )
    
    self.cmd = options.rc_cmd.get()
  
  #//-------------------------------------------------------//
  
  def   getTraceName( self, brief ):
    if brief:
      name = self.cmd[0]
      name = os.path.splitext( os.path.basename( name ) )[0]
    else:
      name = ' '.join( self.cmd )
    
    return name

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonCppLinkerBase( aql.FileBuilder ):
  
  NAME_ATTRS = ('target', )
  SIGNATURE_ATTRS = ('cmd', )
  
  def   getCppExts( self, _cpp_ext = (".cc", ".cp", ".cxx", ".cpp", ".CPP", ".c++", ".C", ".c") ):
    return _cpp_ext
  
  #//-------------------------------------------------------//
  
  def   getResExts( self ):
    return ('.rc',)
  
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options ):
    """
    It should return a builder of C/C++ compiler
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   makeResCompiler( self, options ):
    """
    It should return a builder of C/C++ resource compiler
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   addSourceBuilders( self, builders, exts, builder ):
    if builder:
      for ext in exts:
        builders[ ext ] = builder
  
  #//-------------------------------------------------------//
  
  def   getSourceBuilders( self, node ):
    builders = {}
    
    compiler = self.makeCompiler( node.options )
    if self.batch:
      compiler = aql.BuildBatch( compiler )
    
    self.addSourceBuilders( builders, self.getCppExts(), compiler )
    
    rc_compiler = self.makeResCompiler( node.options )
    self.addSourceBuilders( builders, self.getResExts(), rc_compiler )
    
    return builders
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, node ):
    obj_files = []
    src_nodes = []
    
    builders = self.getSourceBuilders( node )
    
    batch_sources = {}
    
    cwd = node.cwd
    
    for src_file in node.getSourceValues():
      ext = os.path.splitext( src_file.get() )[1]
      builder = builders.get( ext, None )
      if builder:
        if isinstance( builder, aql.BuildBatch ):
          batch_sources.setdefault( builder, [] ).append( src_file )
        else:
          src_node = aql.Node( builder, src_file, cwd )
          src_nodes.append( src_node )
      else:
        obj_files.append( src_file )
    
    for builder, sources in batch_sources.items():
      src_nodes.append( aql.BatchNode( builder, sources, cwd ) )
    
    node.builder_data = obj_files
    
    return src_nodes
  
  #//-------------------------------------------------------//
  
  def   prebuildFinished( self, node, pre_nodes ):
    
    obj_files = node.builder_data
    for pre_node in pre_nodes:
      obj_files += pre_node.getTargetValues()
    
    return False
  
  #//-------------------------------------------------------//
  
  def   getSources( self, node ):
    return list( src.get() for src in node.builder_data )
  
  #//-------------------------------------------------------//
  
  def   getTargetValues( self, node ):
    value_type = self.fileValueType()
    target = value_type( name = self.target, signature = None )
    return target
  
  #//-------------------------------------------------------//
  
  def   getTraceSources( self, node, brief ):
    return node.builder_data
  
  #//-------------------------------------------------------//
  
  def   getTraceName( self, brief ):
    if brief:
      name = self.cmd[0]
      name = os.path.splitext( os.path.basename( name ) )[0]
    else:
      name = ' '.join( self.cmd )
    
    return name

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonCppArchiver( CommonCppLinkerBase ):
  
  def   __init__( self, options, target, batch ):
    
    prefix = options.libprefix.get() + options.prefix.get()
    suffix = options.libsuffix.get()
    
    self.target = self.getFileBuildPath( target, prefix = prefix, ext = suffix )
    self.cmd = options.lib_cmd.get()
    self.shared = False
    self.batch = batch
    
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonCppLinker( CommonCppLinkerBase ):
  
  def   __init__( self, options, target, shared, def_file, batch ):
    if shared:
      prefix = options.shlibprefix.get() + options.prefix.get()
      suffix = options.shlibsuffix.get()
    else:
      prefix = options.prefix.get()
      suffix = options.progsuffix.get()
    
    self.target = self.getFileBuildPath( target, prefix = prefix, ext = suffix )
    self.cmd = options.link_cmd.get()
    self.shared = shared
    self.def_file = def_file
    self.batch = batch


#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

class ToolCommonCpp( aql.Tool ):
  
  def   __init__( self, options ):
    super( ToolCommonCpp, self).__init__( options )
    
    options.If().cc_name.isTrue().build_dir_name  += '_' + options.cc_name + '_' + options.cc_ver
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = _getCppOptions()
    options.setGroup( "C/C++ compiler" )
    
    return options
  
  def   makeCompiler( self, options, shared, batch ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   makeResCompiler( self, options ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   makeArchiver( self, options, target, batch ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   makeLinker( self, options, target, shared, def_file, batch ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   Compile( self, options, shared = False, batch = False ):
    builder = self.makeCompiler( options, shared = shared )
    if batch:
      return aql.BuildBatch( builder )
    return aql.BuildSingle( builder )
  
  def   CompileResource( self, options ):
    builder = self.makeResCompiler( options )
    return aql.BuildSingle( builder )
  
  def   LinkStaticLibrary( self, options, target, batch = False ):
    return self.makeArchiver( options, target, batch = batch )
  
  LinkLibrary = LinkStaticLibrary
  
  def   LinkSharedLibrary( self, options, target, def_file = None, batch = False ):
    return self.makeLinker( options, target, shared = True, def_file = def_file, batch = batch )
  
  def   LinkProgram( self, options, target, batch = False ):
    return self.makeLinker( options, target, shared = False, def_file = None, batch = batch )

#//===========================================================================//

class ToolCommonRes( aql.Tool ):
  
  @classmethod
  def   options( cls ):
    options = _getResOptions()
    options.setGroup( "C/C++ resource compiler" )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   makeResCompiler( self, options ):
    """
    It should return a builder of C/C++ resource compiler
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   Compile( self, options ):
    builder = self.makeResCompiler( options )
    return aql.BuildSingle( builder )
