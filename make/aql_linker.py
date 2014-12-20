import re
import os.path
import datetime

import aql

#//===========================================================================//

info = aql.getAqlInfo()

HEADER = """#!/usr/bin/env python
#
# THIS FILE WAS AUTO-GENERATED. DO NOT EDIT!
#
# Copyright (c) 2011-{year} of the {name} project, site: {url}
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
""".format( year = datetime.date.today().year, name = info.name, url = info.url )

#//===========================================================================//

MAIN = """
_AQL_VERSION_INFO.date = "{date}"
if __name__ == '__main__':
  aql_module_globals = globals().copy()
  aql_module_name = "aql"
  aql_module = imp.new_module( aql_module_name )
  aql_module_globals.update( aql_module.__dict__ )
  aql_module.__dict__.update( aql_module_globals )
  sys.modules[ aql_module_name ] = aql_module

  sys.exit( main() )
""".format( date = datetime.date.today().isoformat() )

#//===========================================================================//

class AqlPreprocess (aql.FileBuilder):
  
  split = aql.FileBuilder.splitSingle
  
  def   getTraceTargets( self, node, brief ):
    return None
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    src_file = node.getSources()[0]
    
    empty_re = re.compile(r'^\s*\r*\n', re.MULTILINE)
    slash_re = re.compile(r'\\\r*\n', re.MULTILINE)
    comments_re = re.compile(r"^\s*#.*$", re.MULTILINE )
    all_stmt_re = re.compile(r"^__all__\s*=\s*\(.+?\)", re.MULTILINE | re.DOTALL )
    
    content = aql.readTextFile( src_file )
    
    content = slash_re.sub( "", content )
    content = comments_re.sub( "", content )
    content = all_stmt_re.sub( "", content )
    
    #//-------------------------------------------------------//
    
    import_re = re.compile(r"^import\s+(.+)$", re.MULTILINE )
    
    std_imports = set()
    def   importHandler( match, _std_imports = std_imports ):
      module_name = match.group(1)
      _std_imports.add(module_name)
      return ""
    
    content = import_re.sub( importHandler, content )
    
    #//-------------------------------------------------------//
    
    aql_import_re = re.compile(r"^\s*from\s+(\.?aql.+)\s+import\s+.+$", re.MULTILINE )
    
    aql_imports = set()
    def   aqlImportHandler( match, _aql_imports = aql_imports ):
      module_name = match.group(1)
      
      if module_name.startswith('.'):
        module_name = os.sep + module_name[1:] + '.py'
      else:
        module_name = os.sep + module_name.replace('.', os.sep ) + os.sep
      
      _aql_imports.add(module_name)
      return ""
    
    content = aql_import_re.sub( aqlImportHandler, content )
    
    #//-------------------------------------------------------//
    
    content = empty_re.sub( "", content )
    
    target = aql.SimpleValue( name = src_file, data = (std_imports, aql_imports, content) )
    
    node.addTargets( target )

#//===========================================================================//

class AqlLink (aql.Builder):
  
  def   __init__(self, options, target ):
    self.target = self.getTargetFilePath( target )
  
  #//-------------------------------------------------------//
  
  def   getTargetValues( self, source_values ):
    return self.target
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   _modToFiles( file2deps, modules ):
    
    mod2files = {}
    
    for mod in modules:
      files = set()
      for file in file2deps:
        if file.find( mod ) != -1:
          files.add( file )
      
      mod2files[ mod ] = files
    
    return mod2files
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   _getDep2Files( file2deps, mod2files ):
    
    dep2files = {}
    tmp_file2deps = {}
    
    for file, mods in file2deps.items():
      for mod in mods:
        files = mod2files[ mod ]
        tmp_file2deps.setdefault( file, set() ).update( files )
        for f in files:
          dep2files.setdefault( f, set() ).add( file )
    
    return dep2files, tmp_file2deps
  
  #//-------------------------------------------------------//
  
  @staticmethod
  def   _getContent( files_content, dep2files, file2deps, tails ):
    
    content = ""
    while tails:
      tail = tails.pop(0)
      content += files_content[ tail ]
      
      files = dep2files.pop( tail, [] )
      
      for file in files:
        deps = file2deps[ file ]
        deps.remove( tail )
        if not deps:
          tails.append( file )
          del file2deps[ file ]
    
    return content
  
  #//-------------------------------------------------------//
  
  def   build( self, node ):
    
    file2deps = {}
    files_content = {}
    modules = set()
    tails = []
    
    std_modules = set()
    
    for value in node.getSourceValues():
      file_name = value.name
      mod_std_imports, mod_deps, mod_content = value.data
      
      if not mod_content:
        continue
      
      if not mod_deps:
        tails.append( file_name )
      
      files_content[ file_name ] = mod_content
      file2deps[ file_name ] = mod_deps
      
      std_modules.update( mod_std_imports )
      modules.update( mod_deps )
    
    mod2files = self._modToFiles( file2deps, modules )
    
    dep2files, file2deps = self._getDep2Files( file2deps, mod2files )
    
    content = self._getContent( files_content, dep2files, file2deps, tails )
    
    imports_content = '\n'.join( "import %s" % module for module in sorted(std_modules) )
    
    content = HEADER + '\n' + imports_content + '\n' + content + '\n' + MAIN
    
    aql.writeTextFile( self.target, content )
    
    target = self.makeFileValue( self.target  )
    
    node.addTargets( target )

#//===========================================================================//

class AqlBuildTool( aql.Tool ):
  
  def   Preprocess( self, options ):
    return AqlPreprocess( options )
  
  def   Link( self, options, target ):
    return AqlLink( options, target )

