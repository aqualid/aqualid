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
  prefix = prefix.lstrip()
  
  if not prefix:
    return values
  
  if prefix[-1] == ' ':
    prefix = prefix.rstrip()
    return tuple( itertools.chain( *itertools.product( (prefix,), values ) ) )
  
  return tuple( "%s%s" % (prefix, value ) for value in values ) 

#//===========================================================================//

def   _absFilePaths( file_paths ):
  return tuple( os.path.normcase( os.path.abspath( path ) ) for path in file_paths )

#//===========================================================================//

def   _compilerOptions( options ):
  
  options.objsuffix = aql.StrOptionType( description = "Object file suffix." )
  options.shobjsuffix = aql.StrOptionType( description = "Shared object file suffix." )
  
  options.shobjsuffix = options.objsuffix
  
  options.ccflags = aql.ListOptionType( description = "Common C/C++ compiler flags", separators = None )
  options.occflags = aql.ListOptionType( description = "Common C/C++ compiler optimization flags", separators = None )
  
  options.cppdefines = aql.ListOptionType( unique = True, description = "C/C++ preprocessor defines", separators = None )
  options.defines = options.cppdefines
  options.cppdefines_flag = aql.StrOptionType( description = "Flag for C/C++ preprocessor defines." )
  options.cppdefines_flags = aql.ListOptionType( separators = None )
  options.cppdefines_flags += aql.SimpleOperation( _addPrefix, options.cppdefines_flag, options.cppdefines )
  
  options.cpppath = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor paths to headers", separators = None )
  options.include = options.cpppath
  options.cpppath_flag  = aql.StrOptionType( description = "Flag for C/C++ preprocessor paths." )
  options.cpppath_flags = aql.ListOptionType( separators = None )
  options.cpppath_flags = aql.SimpleOperation( _addPrefix, options.cpppath_flag, aql.SimpleOperation( _absFilePaths, options.cpppath ) )
  
  options.ext_cpppath   = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor path to external headers", separators = None )
  options.ext_include   = options.ext_cpppath
  options.cpppath_flags += aql.SimpleOperation( _addPrefix, options.cpppath_flag, aql.SimpleOperation( _absFilePaths, options.ext_cpppath ) )
  options.ext_cpppath   = aql.ListOptionType( value_type = aql.PathOptionType(), unique = True, description = "C/C++ preprocessor path to external headers", separators = None )
  options.sys_cpppath   = aql.ListOptionType( value_type = aql.PathOptionType(), description = "C/C++ preprocessor path to standard headers", separators = None )
  
  options.cc      = aql.PathOptionType( description = "C/C++ compiler program" )
  options.cc_name = aql.StrOptionType( ignore_case = True, is_tool_key = True, description = "C/C++ compiler name" )
  options.cc_ver  = aql.VersionOptionType( is_tool_key = True, description = "C/C++ compiler version" )
  options.cc_cmd  = aql.ListOptionType( description = "C/C++ compiler full command", separators = None )
  
  options.cc_cmd = [ options.cc ] + options.ccflags + options.occflags + options.cppdefines_flags + options.cpppath_flags
  
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
  
  options.libpath = aql.ListOptionType( value_type = aql.PathOptionType, unique = True,
                                        description = "Paths to external libraries", separators = None )
  options.libpath_flag  = aql.StrOptionType( description = "Flag for library paths." )
  options.libpath_flags = aql.ListOptionType( separators = None )
  options.libpath_flags = aql.SimpleOperation( _addPrefix, options.libpath_flag, aql.SimpleOperation( _absFilePaths, options.libpath ) )
  
  options.libs  = aql.ListOptionType( value_type = aql.PathOptionType, unique = True,
                                      description = "Linking external libraries", separators = None )
  options.libs_flag  = aql.StrOptionType( description = "Flag for libraries." )
  options.libs_flags = aql.ListOptionType( separators = None )
  options.libs_flags = aql.SimpleOperation( _addPrefix, options.libpath_flag, options.libs )
  
  options.progsuffix = aql.StrOptionType( description = "Program suffix." )
  options.linkflags  = aql.ListOptionType( description = "Linker flags", separators = None )
  options.olinkflags = aql.ListOptionType( description = "Linker optimization flags", separators = None )
  options.link       = aql.PathOptionType( description = "Linker program" )
  options.link_cmd   = aql.ListOptionType( description = "Linker full command", separators = None )
  options.link_cmd   = [ options.link ] + options.linkflags + options.olinkflags + options.libpath_flags + options.libs_flags

#//===========================================================================//

def   _getCppOptions():
  options = aql.Options()
  _compilerOptions( options )
  _linkerOptions( options )
  
  return options

#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CppCommonCompiler (aql.FileBuilder):
  
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
  
  def   getTargets( self, sources ):
    return tuple( self.getBuildPath( src ).change( prefix = self.prefix ) + self.suffix for src in sources ) 
  
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
  
  #//-------------------------------------------------------//
  def   makeCompiler( self, options ):
    """
    It should return a builder of C/C++ compiler
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
class CppCommonArchiver( CppCommonLinkerBase ):
  
  def   __init__( self, options, target ):
    
    prefix = options.libprefix.get() + options.prefix.get()
    suffix = options.libsuffix.get()
    
    self.target = self.getBuildPath( target ).change( prefix = prefix ) + suffix
    self.cmd = options.lib_cmd.get()
    self.shared = False
    
#//===========================================================================//

#noinspection PyAttributeOutsideInit
class CppCommonLinker( CppCommonLinkerBase ):
  
  def   __init__( self, options, target, shared ):
    if shared:
      prefix = options.shlibprefix.get() + options.prefix.get()
      suffix = options.shlibsuffix.get()
    else:
      prefix = options.prefix.get()
      suffix = options.progsuffix.get()
    
    self.target = self.getBuildPath( target ).change( prefix = prefix, ext = suffix )
    self.cmd = options.link_cmd.get()
    self.shared = shared

#//===========================================================================//
#// TOOL IMPLEMENTATION
#//===========================================================================//

class ToolCppCommon( aql.Tool ):
  
  def   __init__( self, options ):
    super( ToolCppCommon, self).__init__( options )
    options.If().cc_name.isTrue().build_dir_name  += '_' + options.cc_name + '_' + options.cc_ver
  
  #//-------------------------------------------------------//
  
  @classmethod
  def   options( cls ):
    options = _getCppOptions()
    options.setGroup( "C/C++ compiler" )
    
    return options
  
  #//-------------------------------------------------------//
  
  def   makeCompiler( self, options, shared ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   makeArchiver( self, options, target ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  def   makeLinker( self, options, target, shared ):
    raise NotImplementedError( "Abstract method. It should be implemented in a child class." )
  
  #//-------------------------------------------------------//
  
  def   Compile( self, options, shared = False, batch = False ):
    builder = self.makeCompiler( options, shared = shared )
    if batch:
      return aql.BuildBatch( builder )
    return aql.BuildSingle( builder )
  
  def   LinkLibrary( self, options, target ):
    return self.makeArchiver( options, target )
  
  def   LinkStaticLibrary( self, options, target ):
    return self.makeArchiver( options, target )
  
  def   LinkSharedLibrary( self, options, target ):
    return self.makeLinker( options, target, shared = True )
  
  def   LinkProgram( self, options, target ):
    return self.makeLinker( options, target, shared = False )
