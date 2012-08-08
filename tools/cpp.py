
from aql_node import Node
from aql_builder import Builder
from aql_value import Value, NoContent
from aql_file_value import FileValue
from aql_utils import toSequence, isSequence, execCommand
from aql_simple_types import FilePath
from aql_errors import InvalidSourceValueType

# 1. Env( tools = ['c++'] )
# 2. Tool 'c++': ToolGcc, ToolMSVS, ToolIntelC, ToolClang, ...
# 3. opt = ToolGcc.options( env )
# 4. opt.update( ARGUMENTS )
# 5. Setup ToolGcc: 'c++', 'gcc', 'g++' -> setupTool(..)
# 6. __init__( tool )
# 7. Register factories

#//===========================================================================//

def   _getSourceFiles( values ):
  
  src_files = []
  
  for value in values:
    if not isinstance( value, FileValue ):
      raise InvalidSourceValueType( value )
    
    src_files.append( value.name )
  
  return src_files

#//===========================================================================//

def   _addPrefix( prefix, values ):
  return map( lambda v, prefix = prefix: prefix + v, values )

#//===========================================================================//

def   _mapToBuildDir( build_dir, source_file ):
  
  build_dir = os.path.normpath( build_dir )
  source_file = os.path.abspath( os.path.normpath( source_file ) )
  
  drive, build_dir = os.path.splitdrive( build_dir )
  
  build_dir = list( filter( None, build_dir.split( os.path.sep ) ) )
  build_dir = list( filter( None, build_dir.split( os.path.sep ) ) )
  
  for a, b in zip( )

class BuildPathMapper( object ):
  
  __slots__ = ( 'build_dir_map', 'build_dir_default' )
  
  def   __init__( self ):
    self.build_dir_map = {}
    self.build_dir_default = None
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __splitPath( path ):
    drive, path = os.path.splitdrive( os.path.normcase( path ) )
    path = list( filter( None, path.split( os.path.sep ) ) )
    path[0:1] = drive + os.path.sep
    
    return path
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def __isBasePath( base_path, path ):
    return path[0 : 0 + len(base_path)] == base_path
  
  #//-------------------------------------------------------//
  
  def   buildDir( self, build_dir, src_dir = None ):
    build_dir = FileAbsPath( build_dir )
    build_dir_seq = self.__splitPath( build_dir )
    
    if src_dir is None:
      self.build_dir_default = (build_dir, build_dir_seq)
    else:
      if self.build_dir_default is None:
        self.build_dir_default = (build_dir, build_dir_seq)
      
      src_dir = FileAbsPath( src_dir )
      src_dir_seq = self.__splitPath( src_dir )
      self.build_dir_map[ src_dir ] = ( src_dir_seq, build_dir, build_dir_seq )
  
  #//-------------------------------------------------------//
  
  def   mapPath( self, src_path ):
    src_path = FileAbsPath( src_path )
    src_path_seq = self.__splitPath( src_path )
    
    src_path_base = None
    build_path = self.build_dir_default
    
    for src_dir, build_dir in self.build_dir_map.items():
      if src_path.startswith( src_dir ):
        build_path = build_dir
        src_path_base = src_dir
        break
      
      elif src_path.startswith( build_dir ):
        build_path = build_dir  # keep looking for the specific mapping
        src_path_base = build_dir
    
    if src_path_base is None:
      
    
#//===========================================================================//

def   _buildSingleSource( cmd, build_dir, source_file ):
  with Tempfile() as dep_file:
    cmd += [ '-MF', dep_file ]
    
    obj_file = os.path.relpath( )
    
    cmd += [ '-o', dep_files[0] ]

#//===========================================================================//

class CompileCppBuilder (Builder):
  
  def   __init__(self, name, env, options ):
    
    self.name = [ name ]
    self.env = env
    self.options = options
  
  #//-------------------------------------------------------//
  
  def   build( self, build_manager, node ):
    
    options = self.options
    
    build_dir = options.build_dir().value()
    
    cmd = [options.cxx.value(), '-c', '-MMD', '-x', 'c++']
    cmd += options.cxxflags.value()
    cmd += options.ccflags.value()
    cmd += _addPrefix( '-D', options.cppdefines.value() )
    cmd += _addPrefix( '-I', options.cpppath.value() )
    cmd += _addPrefix( '-I', options.ext_cpppath.value() )
    
    with Tempfiles() as dep_files:
      src_files = _getSourceFiles( node.sources() )
      if len(src_files) == 1:
        src_file = src_files[0]
        dep_files.append( Tempfile().close().name )
        cmd += [ '-MF', dep_files[0] ]
        cmd += [ '-o', dep_files[0] ]
    
    #'../build/<target OS>_<target CPU>_<cc name><cc ver>/<build variant>/tests'
    #<build_dir_prefix>/<build_target>/<build_dir_suffix>/<prefix>
    
    CompileCpp( src_files, build_dir_suffix = 'sbe_sdk' )
    
    #// C:\work\src\sbe\build_dir
    #// C:\work\src\sbe\tests\list\test_list.cpp
    #// C:\work\src\sbe\sbe\path_finder\foo.cpp
    #// C:\work\src\sbe\sbe\path_finder\bar.cpp
    #// C:\work\src\sbe\sbe\hash\foo.cpp
    #// C:\3rdparty\foo\src\foo.cpp
    #// D:\TEMP\foo.cpp
    #// C:\TEMP\foo.cpp
    
    #// C:\work\src\sbe\build_dir\tests\list\test_list.o
    #// C:\work\src\sbe\build_dir\sbe\path_finder\foo.o
    #// C:\work\src\sbe\build_dir\sbe\path_finder\bar.o
    #// C:\work\src\sbe\build_dir\sbe\hash\foo.o
    #// C:\work\src\sbe\build_dir\3rdparty\foo\src\foo.o
    #// C:\work\src\sbe\build_dir\__D\TEMP\foo.o
    #// C:\work\src\sbe\build_dir\__C\TEMP\foo.o
    
    # > cd C:\work\src\sbe\build_dir\tmp_1234
    # > g++ -c -MMD -O3 tests\list\test_list.cpp sbe\path_finder\foo.cpp sbe\path_finder\bar.cpp
    # > mv test_list.o tests\list\test_list.o
    # > mv foo.o sbe\path_finder\foo.o
    # > mv bar.o sbe\path_finder\bar.o
    # > g++ -c -MMD -O3 tests\list\test_list.cpp sbe\path_finder\foo.cpp sbe\path_finder\bar.cpp
    
    cmd += src_files
    
    cmd = ' '.join( map(str, cmd ) )
    
    cwd = options.build_dir.value()
    
    #~ result = execCommand( cmd, cwd = cwd, env = options.os_env )
    result = execCommand( cmd, cwd = cwd, env = None )
    
    target_values = []
    
    sub_nodes = []
    
    for source_value in node.sources():
      
      n = Node( self.builder, source_value )
      if n.actual( vfile ):
        target_values += n.targets()
      else:
        sub_nodes.append( n )
    
    if sub_nodes:
      bm.addDeps( node, sub_nodes ); bm.selfTest()
      raise RebuildNode()
    
    return target_values, [], []
  
  #//-------------------------------------------------------//
  
  def   clear( self, node, target_values, itarget_values ):
    for value in target_values:
      value.remove()
  
  #//-------------------------------------------------------//
  
  def   values( self ):
    return self.builder.values()
  
  #//-------------------------------------------------------//
  
  def   __str__( self ):
    return ' '.join( self.long_name )

#//===========================================================================//

class ToolCxx( Tool ):
  
  def   __init__( self, env ):
    raise NotImplemented
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __compilerOptions( options ):
    
    options.cflags = ListOptionType( description = "C compiler options" )
    options.ccflags = ListOptionType( description = "Common C/C++ compiler options" )
    options.cxxflags = ListOptionType( description = "C++ compiler options" )
    
    options.ocflags = ListOptionType( description = "C compiler optimization options" )
    options.occflags = ListOptionType( description = "Common C/C++ compiler optimization options" )
    options.ocxxflags = ListOptionType( description = "C++ compiler optimization options" )
    
    options.cflags += options.ocflags
    options.ccflags += options.occflags
    options.cxxflags += options.ocxxflags
    
    options.cc_name = StrOptionType( ignore_case = True, help = "C/C++ compiler name" )
    options.cc_ver = VersionOptionType( description = "C/C++ compiler version" )
    
    options.cppdefines = ListOptionType( unique = True, description = "C/C++ preprocessor defines" )
    options.defines = options.cppdefines
    
    options.cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor paths to headers" )
    options.include = options.cpppath
    
    options.ext_cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor path to extenal headers" )
  
  #//-------------------------------------------------------//
  @staticmethod
  def   __linkerOptions( options ):
    options.linkflags = ListOptionType( description = "Linker options" )
    options.libflags = ListOptionType( description = "Archiver options" )
    
    options.olinkflags = ListOptionType( description = "Linker optimization options" )
    options.olibflags = ListOptionType( description = "Archiver optimization options" )
    
    options.linkflags += options.olinkflags
    options.libflags += options.olibflags
    
    options.libpath = ListOptionType( value_type = FilePath, unique = True, description = "Paths to extenal libraries" )
    options.libs = ListOptionType( value_type = FilePath, unique = True, description = "Linking extenal libraries" )
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   _options( options ):
    ToolCxxCompiler.__compilerOptions( options )
    ToolCxxCompiler.__linkerOptions( options )
  
  #//-------------------------------------------------------//
  
  @builder
  def   CompileCpp( self, env, sources, options ):
    pass
  
  @builder
  def   CompileC( self, env, sources, options ):
    pass
  
  @builder
  def   StaticLibrary( self, env, sources, options ):
    pass
  
  @builder
  def   SharedLibrary( self, env, sources, options ):
    pass
  
  @builder
  def   Program( self, env, sources, options ):
    pass


#//===========================================================================//

@tool('gcc', 'c++')
class ToolGcc( ToolCxx ):
  
  def   __init__( self, env ):
    raise NotImplemented
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   options( _options = [ None ] ):
    
    options = _options[0]
    
    if options is not None:
      return options
    
    options = Options()
    _options[0] = options
    
    super( ToolGcc, self)._options( options )
    
    options.gcc_path = PathOptionType()
    options.gcc_target = StrOptionType( ignore_case = True )
    options.gcc_prefix = StrOptionType( description = "GCC C/C++ compiler prefix" )
    options.gcc_suffix = StrOptionType( description = "GCC C/C++ compiler suffix" )
    
    options.setGroup( "C/C++ compiler" )
    
    return options
  
  #//-------------------------------------------------------//
  
  @builder
  def   CompileCpp( self, env, sources, options ):
    pass
  
  @builder
  def   CompileC( self, env, sources, options ):
    pass
  
  @builder
  def   StaticLibrary( self, env, sources, options ):
    pass
  
  @builder
  def   SharedLibrary( self, env, sources, options ):
    pass
  
  @builder
  def   Program( self, env, sources, options ):
    pass

#//===========================================================================//

"""

env = Environment( tools_path = ['.'] )

src_files = env.FindFiles( "*.*" )

objs = env.ComplieCpp( src_files, optimization = 'size' )
objs = env.ComplieC( src_files, optimization = 'size' )
lib = env.StaticLibrary( objs, debug_symbols = 'off' )
lib = env.LinkDynamicLibrary( objs, debug_symbols = 'off' )

if_ = options.If().cc_name['gcc']

if_.target_os['windows'].user_interface['console'].cc.linkflags += '-Wl,--subsystem,console'
if_.target_os['windows'].user_interface['gui'].cc.linkflags += '-Wl,--subsystem,windows'

if_.debug_symbols['true'].ccflags += '-g'
if_.debug_symbols['false'].linkflags += '-Wl,--strip-all'

options.cc.cxxflags = ""
options.cc.cflags = ""
options.cc.flags = ""

obj_files = env.Compile( src_files, ccflags )      # c++ -> obj
obj_files = env.StaticObject( src_nodes ) # c++ -> obj

prog = env.Program( src_files ) # c++ -> obj -> exe
prog = env.Program( obj_files ) # obj -> exe

prog = env.Program( env.Object( src_files ) ) # obj -> exe
prog = env.Library( env.Object( src_files ) ) # obj -> exe
prog = env.SharedLibrary( env.SharedObject( src_files ) ) # obj -> exe
prog = env.Link( env.Compile( src_files ) ) # obj -> exe


obj_files = env.CompileCpp( cpp_files )       # c++ -> obj
obj_files = env.CompileAsm( asm_files )       # c++ -> obj
obj_files = env.CompileC( c_files )           # c++ -> obj

prog = env.LinkProgram['c++']( obj_files )
prog = env.LinkProgram['fortran']( obj_files )
prog = env.ProgramC( obj_files )
prog = env.ProgramAsm( obj_files )

obj_files = env.CompileCpp( cpp_files )       # c++ -> obj
obj_files = env.CompileAsm( asm_files )       # c++ -> obj
obj_files = env.CompileC( c_files )           # c++ -> obj

prog = env.ProgramCpp( obj_files )
prog = env.ProgramC( obj_files )
prog = env.ProgramAsm( obj_files )

"""
