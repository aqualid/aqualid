
from aql_node import Node
from aql_builder import Builder
from aql_value import Value, NoContent
from aql_file_value import FileValue
from aql_utils import toSequence, isSequence
from aql_simple_types import FilePath

# 1. Env( tools = ['c++'] )
# 2. Tool 'c++': ToolGcc, ToolMSVS, ToolIntelC, ToolClang, ...
# 3. opt = ToolGcc.options( env )
# 4. opt.update( ARGUMENTS )
# 5. Setup ToolGcc: 'c++', 'gcc', 'g++' -> setupTool(..)
# 6. __init__( tool )
# 7. Register factories

#//===========================================================================//

class ToolCxx( Tool ):
  
  def   __init__( self, env ):
    raise NotImplemented
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   __compilerOptions( options ):
    
    _options.cflags = ListOptionType( description = "C compiler options" )
    _options.ccflags = ListOptionType( description = "Common C/C++ compiler options" )
    _options.cxxflags = ListOptionType( description = "C++ compiler options" )
    
    _options.ocflags = ListOptionType( description = "C compiler optimization options" )
    _options.occflags = ListOptionType( description = "Common C/C++ compiler optimization options" )
    _options.ocxxflags = ListOptionType( description = "C++ compiler optimization options" )
    
    _options.cflags += _options.ocflags
    _options.ccflags += _options.occflags
    _options.cxxflags += _options.ocxxflags
    
    _options.cc_name = StrOptionType( ignore_case = True, help = "C/C++ compiler name" )
    _options.cc = _options.cc_name
    
    _options.cc_ver = VersionOptionType( description = "C/C++ compiler version" )
    
    _options.cppdefines = ListOptionType( unique = True, description = "C/C++ preprocessor defines" )
    _options.defines = _options.cppdefines
    
    _options.cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor paths to headers" )
    _options.include = _options.cpppath
    
    _options.cpppath_const = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor path to extenal headers" )
    _options.cpppath_lib = _options.cpppath_const
  
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
  def   options( _options = Options() ):
    
    if not _options:
      ToolCxxCompiler.__compilerOptions( _options )
      ToolCxxCompiler.__linkerOptions( _options )
      
      cpp_group = "C/C++ compiler"
      
      for name in _options:
        _options[ name ].option_type.group = cpp_group
    
    return _options
  
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
  def   options( _options = Options() ):
    
    options.gcc_path = StrOptionType()
    options.gcc_target = _StrOption()
    options.gcc_prefix = _StrOption( help = "GCC C/C++ compiler prefix", group = "C/C++ compiler" )
    options.gcc_suffix = _StrOption( help = "GCC C/C++ compiler suffix", group = "C/C++ compiler" )
    
    
    return True
  
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
