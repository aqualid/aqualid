
from aql_node import Node
from aql_builder import Builder
from aql_value import Value, NoContent
from aql_file_value import FileValue
from aql_utils import toSequence, isSequence

def   valueType( value ):
  for type_func in tool_type_functions:
    t = type_func(value )
    if t is not None:
      return t
  
  return None

# 1. Env( tools = ['c++'] )
# 2. Tool 'c++': ToolGcc, ToolMSVS, ToolIntelC, ToolClang, ...
# 3. opt = ToolGcc.options( env )
# 4. opt.update( ARGUMENTS )
# 5. Setup ToolGcc: 'c++', 'gcc', 'g++' -> setupTool(..)
# 6. __init__( tool )
# 7. Register factories

@tool('gcc', 'g++', 'c++')
class ToolGcc (Tool):
  
  def   __init__( self, env ):
    raise NotImplemented
  
  @staticmethod
  def   options( env ):
    #~ return False
    return True
  
  @factory( 'obj', [['c++', 'c']] )
  def   StaticObject( self, env, type_getter, sources, options ):
    pass
  
  @factory( 'lib', ['obj', ['c++', 'c']] )
  def   StaticLibrary( self, env, type_getter, sources, options ):
    pass
  
  @factory( ['exe'], [['obj', 'lib'], ['c++','c']] )
  def   Program( self, env, type_getter, *sources, **options ):
    pass
  
  def   getValueType( self, value ):
    return getCppType( value )


src_files = env.FindFiles( "*.*" )

env.StaticObject( src_files, typers = typerCToCpp, optimization = 'size' )

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

prog = env.ProgramCpp( obj_files )
prog = env.ProgramC( obj_files )
prog = env.ProgramAsm( obj_files )

obj_files = env.CompileCpp( cpp_files )       # c++ -> obj
obj_files = env.CompileAsm( asm_files )       # c++ -> obj
obj_files = env.CompileC( c_files )           # c++ -> obj

prog = env.ProgramCpp( obj_files )
prog = env.ProgramC( obj_files )
prog = env.ProgramAsm( obj_files )
