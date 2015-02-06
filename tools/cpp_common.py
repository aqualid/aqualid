import os
import itertools

from aql import findFileInPaths,\
  StrOptionType, BoolOptionType, VersionOptionType, ListOptionType,\
  AbsPathOptionType, EnumOptionType, SimpleOperation, Options, \
  Builder, FileBuilder, BatchNode, Node, Tool 

#//===========================================================================//

class   ErrorBatchBuildCustomExt( Exception ):
  def   __init__( self, node, ext ):
    msg = "Custom extension '%s' is not supported for batch building of node: %s" % (ext, node.getBuildStr( brief = False ))
    super(ErrorBatchBuildCustomExt, self).__init__(msg)

#//===========================================================================//

class   ErrorBatchBuildWithPrefix( Exception ):
  def   __init__( self, node, prefix ):
    msg = "Filename prefix '%s' is not supported for batch building of node: %s" % (prefix, node.getBuildStr( brief = False ))
    super(ErrorBatchBuildWithPrefix, self).__init__(msg)

#//===========================================================================//

class   ErrorBatchBuildCustomSuffix( Exception ):
  def   __init__( self, node, suffix ):
    msg = "Filename suffix '%s' is not supported for batch building of node: %s" % (suffix, node.getBuildStr( brief = False ))
    super(ErrorBatchBuildCustomSuffix, self).__init__(msg)


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

def   _preprocessorOptions( options ):
  
  options.cppdefines = ListOptionType( unique = True, description = "C/C++ preprocessor defines", separators = None )
  options.defines = options.cppdefines
  options.cppdefines_prefix = StrOptionType( description = "Flag for C/C++ preprocessor defines.", is_hidden = True )
  options.cppdefines_flags = ListOptionType( separators = None )
  options.cppdefines_flags += SimpleOperation( _addPrefix, options.cppdefines_prefix, options.cppdefines )
  
  options.cpppath_flags = ListOptionType( separators = None )
  options.cpppath_prefix  = StrOptionType( description = "Flag for C/C++ preprocessor paths.", is_hidden = True )
  
  options.cpppath = ListOptionType( value_type = AbsPathOptionType(), unique = True, description = "C/C++ preprocessor paths to headers", separators = None )
  options.include = options.cpppath
  options.cpppath_flags = SimpleOperation( _addPrefix, options.cpppath_prefix, options.cpppath )
  
  options.api_cpppath = ListOptionType( value_type = AbsPathOptionType(), unique = True, description = "C/C++ preprocessor paths to API headers", separators = None )
  options.cpppath_flags += SimpleOperation( _addPrefix, options.cpppath_prefix, options.api_cpppath )
  
  options.ext_cpppath   = ListOptionType( value_type = AbsPathOptionType(), unique = True, description = "C/C++ preprocessor path to external headers", separators = None )
  options.ext_include   = options.ext_cpppath
  options.cpppath_flags += SimpleOperation( _addPrefix, options.cpppath_prefix, options.ext_cpppath )
  
  options.sys_cpppath = ListOptionType( value_type = AbsPathOptionType(), description = "C/C++ preprocessor path to standard headers", separators = None )

#//===========================================================================//

def   _compilerOptions( options ):
  
  options.language = EnumOptionType( values = [('c++', 'cpp'), 'c'], default = 'c++',
                                         description = 'Current language', is_hidden = True )
  
  options.pic = BoolOptionType( description = "Generate position-independent code.", default = True )
  
  options.objsuffix = StrOptionType( description = "Object file suffix.", is_hidden = True )
  
  options.cxxflags = ListOptionType( description = "C++ compiler flags", separators = None )
  options.cflags = ListOptionType( description = "C++ compiler flags", separators = None )
  options.ccflags = ListOptionType( description = "Common C/C++ compiler flags", separators = None )
  options.occflags = ListOptionType( description = "Common C/C++ compiler optimization flags", separators = None )
  
  options.cc      = AbsPathOptionType( description = "C/C++ compiler program" )
  options.cc_name = StrOptionType( is_tool_key = True, ignore_case = True, description = "C/C++ compiler name" )
  options.cc_ver  = VersionOptionType( is_tool_key = True, description = "C/C++ compiler version" )
  options.cc_cmd  = ListOptionType( separators = None, description = "C/C++ compiler full command", is_hidden = True)
  
  options.cc_cmd = options.cc
  options.If().language.eq('c++').cc_cmd += options.cxxflags
  options.If().language.eq('c').cc_cmd += options.cflags
  options.cc_cmd += options.ccflags + options.occflags + options.cppdefines_flags + options.cpppath_flags
  
  options.cxxstd = EnumOptionType( values = ['default', ('c++98', 'c++03'), ('c++11', 'c++0x'), ('c++14','c++1y') ],
                                   default = 'default', description = 'C++ language standard.' )
  
#//===========================================================================//

def   _resourceCompilerOptions( options ):
  options.rc = AbsPathOptionType( description = "C/C++ resource compiler program" )
  options.ressuffix = StrOptionType( description = "Compiled resource file suffix.", is_hidden = True )
  
  options.rcflags = ListOptionType( description = "C/C++ resource compiler flags", separators = None )
  options.rc_cmd = ListOptionType( separators = None, description = "C/C++ resource resource compiler full command", is_hidden = True) 
  
  options.rc_cmd = [ options.rc ] + options.rcflags + options.cppdefines_flags + options.cpppath_flags

#//===========================================================================//

def   _linkerOptions( options ):
  
  options.libprefix = StrOptionType( description = "Static library archiver prefix.", is_hidden = True )
  options.libsuffix = StrOptionType( description = "Static library archiver suffix.", is_hidden = True )
  options.libflags  = ListOptionType( description = "Static library archiver flags", separators = None )
  options.olibflags = ListOptionType( description = "Static library archiver optimization flags", separators = None )
  options.lib       = AbsPathOptionType( description = "Static library archiver program" )
  options.lib_cmd   = ListOptionType( separators = None, description = "Static library archiver full command", is_hidden = True )
  options.lib_cmd   = [ options.lib ] + options.libflags + options.olibflags
  
  options.shlibprefix = StrOptionType( description = "Shared library prefix.", is_hidden = True )
  options.shlibsuffix = StrOptionType( description = "Shared library suffix.", is_hidden = True )
  
  options.libpath = ListOptionType( value_type = AbsPathOptionType(), unique = True,
                                        description = "Paths to external libraries", separators = None )
  options.libpath_prefix  = StrOptionType( description = "Flag for library paths.", is_hidden = True )
  options.libpath_flags = ListOptionType( separators = None )
  options.libpath_flags = SimpleOperation( _addPrefix, options.libpath_prefix, options.libpath )
  
  options.libs  = ListOptionType( value_type = StrOptionType(), unique = True,
                                      description = "Linking external libraries", separators = None )
  options.libs_prefix  = StrOptionType( description = "Prefix flag for libraries.", is_hidden = True )
  options.libs_suffix  = StrOptionType( description = "Suffix flag for libraries.", is_hidden = True )
  options.libs_flags = ListOptionType( separators = None )
  options.libs_flags = SimpleOperation( _addIxes, options.libs_prefix, options.libs_suffix, options.libs )
  
  options.progsuffix = StrOptionType( description = "Program suffix.", is_hidden = True )
  options.linkflags  = ListOptionType( description = "Linker flags", separators = None )
  options.olinkflags = ListOptionType( description = "Linker optimization flags", separators = None )
  options.link       = AbsPathOptionType( description = "Linker program" )
  options.link_cmd   = ListOptionType( separators = None, description = "Linker full command", is_hidden = True )
  options.link_cmd   = [ options.link ] + options.linkflags + options.olinkflags + options.libpath_flags + options.libs_flags

#//===========================================================================//

def   _getCppOptions():
  options = Options()
  _preprocessorOptions( options )
  _compilerOptions( options )
  _resourceCompilerOptions( options )
  _linkerOptions( options )
  
  return options

#//===========================================================================//

def   _getResOptions():
  options = Options()
  _preprocessorOptions( options )
  _resourceCompilerOptions( options )
  
  return options

#//===========================================================================//

class HeaderChecker (Builder):

  SIGNATURE_ATTRS = ('cpppath', )
  
  def   __init__(self, options ):
    
    cpppath = list(options.cpppath.get())
    cpppath += options.ext_cpppath.get()
    cpppath += options.sys_cpppath.get()
    
    self.cpppath = cpppath
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    has_headers = True
    
    cpppath = self.cpppath
    
    for header in node.getSources():
      found = findFileInPaths( cpppath, header )
      if not found:
        has_headers = False
        break
    
    node.addTargets( has_headers )
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonCppCompiler (FileBuilder):
  
  NAME_ATTRS = ( 'prefix', 'suffix', 'ext' )
  SIGNATURE_ATTRS = ('cmd', )
  
  #//-------------------------------------------------------//
  
  #noinspection PyUnusedLocal
  def   __init__(self, options ):
    
    self.prefix = options.prefix.get()
    self.suffix = options.suffix.get()
    self.ext = options.objsuffix.get()
    
    ext_cpppath = list( options.ext_cpppath.get() )
    ext_cpppath += options.sys_cpppath.get()
    
    self.ext_cpppath = tuple( set( os.path.normcase( os.path.abspath( folder ) ) + os.path.sep for folder in ext_cpppath ) )
    
    self.cmd = list( options.cc_cmd.get() )
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_values ):
    return self.getObjPath( source_values[0].get() )
  
  #//-------------------------------------------------------//
  
  def   getObjPath( self, file_path ):
    return self.getTargetFromSourceFilePath( file_path, ext = self.ext, prefix = self.prefix, suffix = self.suffix )
  
  #//-------------------------------------------------------//
  
  def   getDefaultObjExt(self):
    """
    Returns a default extension of output object files.
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   checkBatchSplit( self, node ):
    
    default_ext = self.getDefaultObjExt()
    
    if self.ext != default_ext:
      raise ErrorBatchBuildCustomExt( node, self.ext )
    
    if self.prefix:
      raise ErrorBatchBuildWithPrefix( node, self.prefix )
    
    if self.suffix:
      raise ErrorBatchBuildCustomSuffix( node, self.suffix )

  #//-------------------------------------------------------//
  
  def   split( self, node ):
    if node.isBatch():
      self.checkBatchSplit( node )
      split_nodes = self.splitBatchByBuildDir( node )
    
    else:
      split_nodes = self.splitSingle( node )
    
    return split_nodes
  
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
class CommonResCompiler (FileBuilder):
  
  NAME_ATTRS = ( 'prefix', 'suffix', 'ext' )
  SIGNATURE_ATTRS = ('cmd', )
  
  #//-------------------------------------------------------//
  
  #noinspection PyUnusedLocal
  def   __init__(self, options ):
    
    self.prefix = options.prefix.get()
    self.suffix = options.suffix.get()
    self.ext = options.ressuffix.get()
    
    self.cmd = options.rc_cmd.get()
  
  #//-------------------------------------------------------//
  
  def   split( self, node ):
    return self.splitSingle( node )
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_values ):
    return self.getObjPath( source_values[0].get() )
  
  #//-------------------------------------------------------//
  
  def   getObjPath( self, file_path ):
    return self.getTargetFromSourceFilePath( file_path, ext = self.ext, prefix = self.prefix, suffix = self.suffix )
  
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
class CommonCppLinkerBase( FileBuilder ):
  
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
    
    options = node.options
    compiler = self.makeCompiler( options )
    
    self.addSourceBuilders( builders, self.getCppExts(), compiler )
    
    rc_compiler = self.makeResCompiler( options )
    self.addSourceBuilders( builders, self.getResExts(), rc_compiler )
    
    return builders
  
  #//-------------------------------------------------------//
  
  def   replace( self, node ):
    
    def _addSources():
      if current_builder is None:
        new_sources.extend( current_sources )
        return
        
      if current_builder.isBatch():
        src_node = BatchNode( current_builder, current_sources, cwd )
      else:
        src_node = Node( current_builder, current_sources, cwd )
        
      new_sources.append( src_node )
    
    new_sources = []
    
    builders = self.getSourceBuilders( node )
    
    current_builder = None
    current_sources = []
    
    cwd = node.cwd
    
    for src_file in node.getSourceEntities():
      
      ext = os.path.splitext( src_file.get() )[1]
      builder = builders.get( ext, None )
      
      if current_builder is builder:
        current_sources.append( src_file )
      else:
        if current_sources:
          _addSources()
          
        current_builder = builder
        current_sources = [ src_file ]

    if current_sources:
      _addSources()
    
    return new_sources
  
  #//-------------------------------------------------------//
  
  def   getTargetEntities( self, source_values ):
    return self.target
  
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
  
  def   __init__( self, options, target ):
    
    prefix = options.libprefix.get()
    ext = options.libsuffix.get()
    
    self.target = self.getTargetFilePath( target, ext = ext, prefix = prefix )
    self.cmd = options.lib_cmd.get()
    self.shared = False
    
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CommonCppLinker( CommonCppLinkerBase ):
  
  def   __init__( self, options, target, shared ):
    if shared:
      prefix = options.shlibprefix.get()
      ext = options.shlibsuffix.get()
    else:
      prefix = options.prefix.get()
      ext = options.progsuffix.get()
    
    self.target = self.getTargetFilePath( target, prefix = prefix, ext = ext )
    self.cmd = options.link_cmd.get()
    self.shared = shared
  
  #//-------------------------------------------------------//
  
  def   getWeight( self, node ):
    return 2 * len(node.getSourceEntities())


#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

class ToolCommonCpp( Tool ):
  
  def   __init__( self, options ):
    options.If().cc_name.isTrue().build_dir_name  += '_' + options.cc_name + '_' + options.cc_ver
    self.LinkLibrary = self.LinkStaticLibrary
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = _getCppOptions()
    options.setGroup( "C/C++ compiler" )
    
    return options
  
  def   CheckHeaders(self, options ):
    return HeaderChecker( options )
  
  def   Compile( self, options ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   CompileResource( self, options ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   LinkStaticLibrary( self, options, target ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   LinkSharedLibrary( self, options, target, def_file = None ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   LinkProgram( self, options, target ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )

#//===========================================================================//

class ToolCommonRes( Tool ):
  
  @classmethod
  def   options( cls ):
    options = _getResOptions()
    options.setGroup( "C/C++ resource compiler" )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   Compile( self, options ):
    """
    It should return a builder of C/C++ resource compiler
    """
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )

