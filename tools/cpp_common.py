
from aql_value import Value, NoContent
from aql_file_value import FileValue
from aql_utils import toSequence, isSequence

#//---------------------------------------------------------------------------//

def   getCppType( value, cpp_ext = ['cpp', 'cxx', 'cc', 'c++' ], c_ext = ['c'] ):
  if isinstance( value, FileValue ):
    ext = os.path.splitext( value.name )[1].lower()
    if ext in cpp_ext:
      return 'c++'
    
    if ext in c_ext:
      return 'c'
  
  return None

#//---------------------------------------------------------------------------//

def   addCppOptions( env, options = Options() ):
  
  if options:
    return options
  
  options.cflags = StrOption( is_list = 1, help = "C compiler options", group = "C/C++ compiler" )
  options.ccflags = StrOption( is_list = 1, help = "Common C/C++ compiler options", group = "C/C++ compiler" )
  options.cxxflags = StrOption( is_list = 1, help = "C++ compiler options", group = "C/C++ compiler" )
  options.linkflags = StrOption( is_list = 1, help = "Linker options", group = "C/C++ compiler" )
  options.libflags = StrOption( is_list = 1, help = "Archiver options", group = "C/C++ compiler" )
  
  options.ocflags = StrOption( is_list = 1, help = "C compiler optimization options", group = "C/C++ compiler" )
  options.occflags = StrOption( is_list = 1, help = "Common C/C++ compiler optimization options", group = "C/C++ compiler" )
  options.ocxxflags = StrOption( is_list = 1, help = "C++ compiler optimization options", group = "C/C++ compiler" )
  options.olinkflags = StrOption( is_list = 1, help = "Linker optimization options", group = "C/C++ compiler" )
  options.olibflags = StrOption( is_list = 1, help = "Archiver optimization options", group = "C/C++ compiler" )
  
  options.cflags = options.ocflags
  options.ccflags = options.occflags
  options.cxxflags = options.ocxxflags
  options.linkflags = options.olinkflags
  options.libflags = options.olibflags
  
  options.cc_name = StrOption( help = "C/C++ compiler name", group = "C/C++ compiler" )
  options.cc = options.cc_name
  
  options.cc_ver = VersionOption( help = "C/C++ compiler version", group = "C/C++ compiler" )
  
  cppdefines = StrOption( is_list = 1, help = "C/C++ preprocessor defines", group = "C/C++ compiler" )
  options.cppdefines = cppdefines
  options.defines = cppdefines
  
  cpppath = PathOption( is_list = 1, help = "C/C++ preprocessor paths to headers", is_node = 1, group = "C/C++ compiler" )
  options.cpppath = cpppath
  options.include = cpppath
  
  cpppath_lib = _PathOption( is_list = 1, help = "C/C++ preprocessor path to library headers", is_node = 1, group = "C/C++ compiler" )
  options.cpppath_const = cpppath_lib
  options.cpppath_lib = cpppath_lib
  
  options.libpath = _PathOption( is_list = 1, help = "Paths to libraries", is_node = 1, group = "C/C++ compiler" )
  options.libs = StrOption( is_list = 1, help = "Libraries", group = "C/C++ compiler" )

