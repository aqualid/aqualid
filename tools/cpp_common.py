import os
import itertools

import aql

#//===========================================================================//
#// BUILDERS IMPLEMENTATION
#//===========================================================================//

def   _isCCppSourceFile( source_file ):
  ext = os.path.splitext( str(source_file) )[1]
  return ext in ( ".cc", ".cp", ".cxx", ".cpp", ".CPP", ".c++", ".C", ".c" )

#//===========================================================================//

def   _addPrefix( prefix, values ):
  if prefix[-1] == ' ':
    prefix = prefix.strip()
    return tuple( itertools.chain( *itertools.product( (prefix,), values ) ) )
  return tuple( "%s%s" % (prefix, value ) for value in values ) 

#//===========================================================================//

def   _absFilePaths( file_paths ):
  return tuple( os.path.normcase( os.path.abspath( path ) ) for path in file_paths )

#//===========================================================================//

def   _commonCCppCompilerOptions( options ):
  
  options.objsuffix = aql.StrOptionType( description = "Object file suffix." )
  options.shobjsuffix = aql.StrOptionType( description = "Shared object file suffix." )
  
  options.cc_name = aql.StrOptionType( ignore_case = True, is_tool_key = True, description = "C/C++ compiler name" )
  options.cc_ver = aql.VersionOptionType( is_tool_key = True, description = "C/C++ compiler version" )
  
  options.ccflags = aql.ListOptionType( description = "Common C/C++ compiler flags", separators = None )
  options.occflags = aql.ListOptionType( description = "Common C/C++ compiler optimization flags", separators = None )
  
  options.cppdefines = aql.ListOptionType( unique = True, description = "C/C++ preprocessor defines", separators = None )
  options.defines = options.cppdefines
  options.cppdefines_flag = aql.StrOptionType( description = "Flag for C/C++ preprocessor defines." )
  options.cppdefines_flags = aql.ListOptionType( separators = None )
  options.cppdefines_flags += aql.SimpleOperation( _addPrefix, options.cpppath_flag, options.ext_cpppath )
  
  options.cpppath = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor paths to headers", separators = None )
  options.include = options.cpppath
  options.cpppath_flag  = aql.StrOptionType( description = "Flag for C/C++ preprocessor paths." )
  options.cpppath_flags = aql.ListOptionType( separators = None )
  options.cpppath_flags = aql.SimpleOperation( _addPrefix, options.cpppath_flag, aql.SimpleOperation( _absFilePaths, options.cpppath ) )
  
  options.ext_cpppath = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor path to external headers", separators = None )
  options.ext_include = options.ext_cpppath
  options.cpppath_flags += aql.SimpleOperation( _addPrefix, options.cpppath_flag, aql.SimpleOperation( _absFilePaths, options.ext_cpppath ) )
  
#//===========================================================================//

def   _cxxCompilerOptions( options ):
  
  options.cxx = aql.PathOptionType( description = "C++ compiler program" )
  options.cxx_cmd = aql.ListOptionType( description = "C++ compiler full command", separators = None )
  options.cxxflags = aql.ListOptionType( description = "C++ compiler flags", separators = None )
  options.ocxxflags = aql.ListOptionType( description = "C++ compiler optimization flags", separators = None )
  
  options.cxxflags += options.ccflags
  options.cxxflags += options.occflags
  options.cxxflags += options.ocxxflags
  options.cxxflags += options.cppdefines_flags
  options.cxxflags += options.cpppath_flags
  
  options.cxx_cmd = options.cxx + options.cxxflags + options.ocxxflags + \
                    options.ccflags + options.ocflags + \
                    options.cppdefines_flags + options.cpppath_flags
  
#//===========================================================================//

def   _cCompilerOptions( options ):
  
  options.cc = aql.PathOptionType( description = "C compiler program" )
  options.cflags = aql.ListOptionType( description = "C compiler flags", separators = None )
  options.ocflags = aql.ListOptionType( description = "C compiler optimization flags", separators = None )
  options.cc_cmd = aql.ListOptionType( description = "C compiler full command", separators = None )
  
  options.cc_cmd  = options.cc + options.cflags + options.ocflags + \
                    options.ccflags + options.ocflags + \
                    options.cppdefines_flags + options.cpppath_flags
  
#//===========================================================================//

def   _linkerOptions( options ):
  
  options.libprefix = aql.StrOptionType( description = "Static library prefix." )
  options.libsuffix = aql.StrOptionType( description = "Static library suffix." )
  options.shlibprefix = aql.StrOptionType( description = "Shared library prefix." )
  options.shlibsuffix = aql.StrOptionType( description = "Shared library suffix." )
  options.progsuffix = aql.StrOptionType( description = "Program suffix." )
  
  options.link  = aql.PathOptionType( description = "Program or dynamic library linker" )
  options.lib   = aql.PathOptionType( description = "Static library archiver program" )
  
  options.linkflags   = aql.ListOptionType( description = "Program linker flags", separators = None )
  options.libflags    = aql.ListOptionType( description = "Static library flags", separators = None )
  options.shlinkflags = aql.ListOptionType( description = "Shared library flags", separators = None )
  
  options.olinkflags    = aql.ListOptionType( description = "Program linker optimization flags", separators = None )
  options.olibflags     = aql.ListOptionType( description = "Static library optimization flags", separators = None )
  options.oshlinkflags  = aql.ListOptionType( description = "Shared library optimization flags", separators = None )
  
  options.linkflags   += options.olinkflags
  options.libflags    += options.olibflags
  options.shlibflags  += options.oshlibflags
  
  options.libpath = aql.ListOptionType( value_type = aql.PathOptionType, unique = True,
                                        description = "Paths to external libraries", separators = None )
  
  options.libs  = aql.ListOptionType( value_type = aql.PathOptionType, unique = True,
                                      description = "Linking external libraries", separators = None )
  
  options.shobjsuffix = options.objsuffix

#//===========================================================================//

def   _optionsCCpp():
  options = aql.Options()
  _commonCCppCompilerOptions( options )
  _cxxCompilerOptions( options )
  _cCompilerOptions( options )
  _linkerOptions( options )

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CppCommonCompiler (aql.FileBuilder):
  
  NAME_ATTRS = ( 'prefix', 'suffix' )
  SIGNATURE_ATTRS = ('cmd', )
  
  #//-------------------------------------------------------//
  
  #noinspection PyUnusedLocal
  def   __init__(self, options, language, shared, env_cpppaths = tuple() ):
    
    self.prefix = options.prefix.get()
    self.suffix = options.shobjsuffix.get() if shared else options.objsuffix.get()
    
    ext_cpppath = list( options.ext_cpppath.get() )
    for env_cpppath in env_cpppaths:
      ext_cpppath += options.env[ env_cpppath ].get()
    
    self.ext_cpppath = tuple( set( os.path.normcase( os.path.abspath( folder ) ) + os.path.sep for folder in ext_cpppath ) )
    
    if language == 'c++':
      self.cmd = list( options.cxx_cmd.get() )
    else:
      self.cmd = list( options.cc_cmd.get() )
  
  #//-------------------------------------------------------//
  
  def   getTargets( self, sources ):
    return tuple( self.getBuildPath( src ).change( prefix = self.prefix ) + self.suffix for src in sources ) 
  
  #//-------------------------------------------------------//
  
  def   getObj( self, node ):
    source = node.getSources()[0]
    obj_file = self.getBuildPath( source )
    obj_file = obj_file.change( prefix = self.prefix ) + self.suffix
    
    return obj_file, source

  #//-------------------------------------------------------//
  
  def   build( self, node ):
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
class CppCommonLinkerBase(aql.FileBuilder):
  
  NAME_ATTRS = ('target', )
  SIGNATURE_ATTRS = ('cmd', )
  
  def   __init__( self, options, target, language, shared ):
    
    self.target = target
    self.language = language
    self.shared = shared
    
    self.setCmd( options, language, shared )
    
  def   setCmd( self, options, language, shared ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  def   makeCompiler( self, options ):
    """
    It should return a builder of compiler of C/C++ files
    """
    return None
  
  #//-------------------------------------------------------//
  
  def   prebuild( self, node ):
    obj_files = []
    src_nodes = []
    
    compiler = self.makeCompiler( node.options )
    if compiler:
      for src_file in node.getSourceValues():
        if _isCCppSourceFile( src_file.name ):
          src_node = aql.Node( compiler, src_file, node.cwd )
          src_nodes.append( src_node )
        else:
          obj_files.append( src_file )
    
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
    return tuple( src.get() for src in node.builder_data )
  
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
class CppCommonArchiver(CppCommonLinkerBase):
  
  def   __init__( self, options, target, language ):
    
    prefix = options.libprefix.get() + options.prefix.get()
    suffix = options.libsuffix.get()
    
    target = self.getBuildPath( target ).change( prefix = prefix ) + suffix
    super(CppCommonArchiver, self).__init__( options, target, language, shared = False )
    
  #//-------------------------------------------------------//
  
  def   setCmd( self, options, language, shared ):
    self.cmd = [ options.lib.get() ]
    self.cmd += options.libflags.get()
  
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CppCommonLinker( CppCommonLinkerBase ):
  
  def   __init__( self, options, target, language, shared ):
    if shared:
      prefix = options.shlibprefix.get() + options.prefix.get()
      suffix = options.shlibsuffix.get()
    else:
      prefix = options.prefix.get()
      suffix = options.progsuffix.get()
    
    target = self.getBuildPath( target ).change( prefix = prefix, ext = suffix )
    
    super(CppCommonLinker, self).__init__( options, target, language, shared )
  
  #//-------------------------------------------------------//

#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

class ToolCppCommon( aql.Tool ):
  
  def   __init__( self, options ):
    super( ToolCppCommon, self).__init__( options )
    options.If().cc_name.isTrue().build_dir_name  += '_' + options.cc_name + '_' + options.cc_ver
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   options():
    options = _optionsCCpp()
    options.setGroup( "C/C++ compiler" )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options, shared ):
    #~ return GccCompiler( options, self.language, shared = shared )
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   makeArchiver( self, options, target ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
    #~ return GccArchiver( options, target, self.language )
  
  def   makeLinker( self, options, target, shared ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
    #~ return GccLinker( options, target, self.language, shared = shared )
  
  #//-------------------------------------------------------//
  
  def   Compile( self, options, shared = False, batch = False ):
    builder = self.makeCompiler( options, shared = shared )
    if batch:
      return aql.BuildBatch( builder )
    return aql.BuildSingle( builder )
  
  def   LinkLibrary( self, options, target ):
    return self.makeArchiver( options, target )
  
  def   LinkSharedLibrary( self, options, target ):
    return self.makeLinker( options, target, shared = True )
  
  def   LinkProgram( self, options, target ):
    return self.makeLinker( options, target, shared = False )
