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

__all__ = (
  'optionsCCpp',
)

import os

from aql.types import FilePath

from .aql_options import Options
from .aql_option_types import BoolOptionType, ListOptionType, PathOptionType, StrOptionType, VersionOptionType

#//===========================================================================//

def   _commonCCppCompilerOptions( options ):
  
  options.objsuffix = PathOptionType( description = "Object suffix." )
  options.cc_name = StrOptionType( ignore_case = True, description = "C/C++ compiler name" )
  options.cc_ver = VersionOptionType( description = "C/C++ compiler version" )
  
  options.ccflags = ListOptionType( description = "Common C/C++ compiler options" )
  options.occflags = ListOptionType( description = "Common C/C++ compiler optimization options" )
  
  options.cppdefines = ListOptionType( unique = True, description = "C/C++ preprocessor defines" )
  options.defines = options.cppdefines
  
  options.cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor paths to headers" )
  options.include = options.cpppath
  
  options.ext_cpppath = ListOptionType( value_type = FilePath, unique = True, description = "C/C++ preprocessor path to extenal headers" )
  options.ext_include = options.ext_cpppath
  
#//===========================================================================//

def   _cxxCompilerOptions( options ):
  
  options.cxx = PathOptionType( description = "C++ compiler program" )
  options.cxxflags = ListOptionType( description = "C++ compiler options" )
  options.ocxxflags = ListOptionType( description = "C++ compiler optimization options" )
  
  options.cxxflags += options.ccflags
  options.cxxflags += options.occflags
  options.cxxflags += options.ocxxflags
  
  options.no_rtti = BoolOptionType( description = 'Disable C++ realtime type information' )
  options.no_exceptions = BoolOptionType( description = 'Disable C++ exceptions' )
  
#//===========================================================================//

def   _cCompilerOptions( options ):
  
  options.cc = PathOptionType( description = "C compiler program" )
  options.cflags = ListOptionType( description = "C compiler options" )
  options.ocflags = ListOptionType( description = "C compiler optimization options" )
  
  options.cflags += options.ccflags
  options.cflags += options.occflags
  options.cflags += options.ocflags

#//===========================================================================//

def   _linkerOptions( options ):
  
  options.libsuffix = PathOptionType( description = "Static library suffix." )
  options.shlibsuffix = PathOptionType( description = "Shared library suffix." )
  options.progsuffix = PathOptionType( description = "Program suffix." )
  
  options.link = PathOptionType( description = "Program or dynamic library linker" )
  options.lib = PathOptionType( description = "Static library archiver program" )
  
  options.linkflags = ListOptionType( description = "Linker options" )
  options.libflags = ListOptionType( description = "Archiver options" )
  
  options.olinkflags = ListOptionType( description = "Linker optimization options" )
  options.olibflags = ListOptionType( description = "Archiver optimization options" )
  
  options.linkflags += options.olinkflags
  options.libflags += options.olibflags
  
  options.libpath = ListOptionType( value_type = FilePath, unique = True, description = "Paths to extenal libraries" )
  options.libs = ListOptionType( value_type = FilePath, unique = True, description = "Linking extenal libraries" )

#//===========================================================================//

def   optionsCCpp():
  options = Options()
  _commonCCppCompilerOptions( options )
  _cxxCompilerOptions( options )
  _cCompilerOptions( options )
  _linkerOptions( options )
  
  return options
