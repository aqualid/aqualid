
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

class CompileCppBuilder (Builder):
  
  def   __init__(self, env, options ):
    
    chcksum = hashlib.md5()
    chcksum.update( name.encode() )
    
    self.name = chcksum.digest()
    self.long_name = [ name ]
    
    self.env = env
    self.builder = ChecksumBuilder( "ChecksumBuilder", offset, length )
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    target_values = []
    
    bm = self.env.build_manager
    vfile = bm.valuesFile()
    
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
    options.cc = options.cc_name
    
    options.cc_ver = VersionOptionType( description = "C/C++ compiler version" )
    
    options.cppdefines = ListOptionType( unique = True, description = "C/C++ preprocessor defines" )
    options.defines = options.cppdefines
    
    options.cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor paths to headers" )
    options.include = options.cpppath
    
    options.extcpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor path to extenal headers" )
  
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
