#
# Copyright (c) 2012 The developers of Aqualid project - http://aqualid.googlecode.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = ( 'Project', 'ProjectConfig',
            'ErrorProjectBuilderMethodExists',
            'ErrorProjectBuilderMethodFewArguments',
            'ErrorProjectBuilderMethodResultInvalid',
            'ErrorProjectBuilderMethodUnbound',
            'ErrorProjectBuilderMethodWithKW',
            'ErrorProjectInvalidMethod',
          )

from .aql_project import Project

#//===========================================================================//

def   main():
  prj_cfg = ProjectConfig()
  


#//===========================================================================//

if __name__ == "__main__":
  
  configuration.Update( '' )
  
  prj_cfg = aql.ProjectConfig()
  prj_cfg.readConfig( config_file )
  
  prj = aql.Project( prj_cfg, tool_paths )
  
  prj.Tool('c').Compile( c_files, optimization = 'size', debug_symbols = False )
  
  cpp = prj.Tool( 'c++' )
  cpp.Compile( cpp_files, optimization = 'speed' )
  
  prj.Tool('c++')
  
  prj.Compile( c_files, optimization = 'size', debug_symbols = False )
  
  prj_c = aql.Project( prj_cfg, tool_paths )
  prj_c.Tool( 'c' )
  prj_c.Compile( cpp_files, optimization = 'speed' )
  
  #//-------------------------------------------------------//
  
  prj = aql.Project( prj_cfg, tool_paths )
  prj.Tool( 'c++', 'c' )
  
  cpp_objs = prj.CompileCpp( cpp_files, optimization = 'size' )
  c_objs = prj.CompileC( c_files, optimization = 'speed' )
  objs = prj.Compile( c_cpp_files )
  
  cpp_lib = prj.LinkSharedLib( cpp_objs )
  c_lib = prj.LinkLibrary( c_objs )
  
  prog = prj.LinkProgram( [ objs, prj.FilterLibs( cpp_lib ), c_lib ] )
  
  #//-------------------------------------------------------//
  
  prj = aql.Project( prj_cfg, tool_paths )
  
  prj.Tools( 'g++', 'gcc' )
  
  cpp_objs = prj.cpp.Compile( cpp_files, optimization = 'size' )
  c_objs = prj.c.Compile( c_files, optimization = 'speed' )
  
  cpp_lib = prj.cpp.LinkSharedLib( cpp_objs )
  c_lib = prj.c.LinkLibrary( c_objs )
  
  prog = prj.cpp.LinkProgram( [ objs, prj.FilterLibs( cpp_lib ), c_lib ] )
  
  
  """
  1. kw - args
  
  """
  
  
