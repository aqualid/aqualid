import re
import os.path
import datetime
import base64
import hashlib

import aql

# ==============================================================================

info = aql.get_aql_info()

HEADER = """#!/usr/bin/env python
#
# THIS FILE WAS AUTO-GENERATED. DO NOT EDIT!
#
# Copyright (c) 2011-{year} of the {name} project, site: {url}
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
#  OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""".format(year=datetime.date.today().year,
           name=info.name, url=info.url)

# ==============================================================================

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
""".format(date=datetime.date.today().isoformat())


# ==============================================================================
class AqlPreprocess (aql.FileBuilder):

    split = aql.FileBuilder.split_single

    # ----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Preprocess file"

    # ----------------------------------------------------------

    def get_trace_targets(self, target_entities, brief):
        return None

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        src_file = source_entities[0].get()

        empty_re = re.compile(r'^\s*\r*\n', re.MULTILINE)
        slash_re = re.compile(r'\\\r*\n', re.MULTILINE)
        comments_re = re.compile(r"^\s*#.*$", re.MULTILINE)
        all_stmt_re = re.compile(
            r"^__all__\s*=\s*\(.+?\)", re.MULTILINE | re.DOTALL)

        content = aql.read_text_file(src_file)

        content = slash_re.sub("", content)
        content = comments_re.sub("", content)
        content = all_stmt_re.sub("", content)

        # -----------------------------------------------------------

        import_re = re.compile(r"^import\s+(.+)$", re.MULTILINE)

        std_imports = set()

        def import_handler(match, _std_imports=std_imports):
            module_name = match.group(1)
            _std_imports.add(module_name)
            return ""

        content = import_re.sub(import_handler, content)

        # -----------------------------------------------------------

        aql_import_re = re.compile(
            r"^\s*from\s+(\.?aql.+)\s+import\s+.+$", re.MULTILINE)

        aql_imports = set()

        def aql_import_handler(match, _aql_imports=aql_imports):
            module_name = match.group(1)

            if module_name.startswith('.'):
                module_name = os.sep + module_name[1:] + '.py'
            else:
                module_name = os.sep + \
                    module_name.replace('.', os.sep) + os.sep

            _aql_imports.add(module_name)
            return ""

        content = aql_import_re.sub(aql_import_handler, content)

        # -----------------------------------------------------------

        content = empty_re.sub("", content)

        target = aql.SimpleEntity(name=src_file,
                                  data=(std_imports, aql_imports, content))

        targets.add_target_entity(target)


# ==============================================================================
class AqlJoin (aql.FileBuilder):

    def get_trace_name(self, source_entities, brief):
        return "Join preprocessed files"

    # ----------------------------------------------------------

    def get_trace_targets(self, target_entities, brief):
        return None

    # ----------------------------------------------------------

    def get_trace_sources(self, source_entities, brief):
        return (os.path.basename(src.name) for src in source_entities)

    # -----------------------------------------------------------

    def replace(self, options, source_entities):
        return aql.Node(AqlPreprocess(options), source_entities)

    # -----------------------------------------------------------

    @staticmethod
    def _mod_to_files(file2deps, modules):

        mod2files = {}

        for mod in modules:
            files = set()
            for file in file2deps:
                if file.find(mod) != -1:
                    files.add(file)

            mod2files[mod] = files

        return mod2files

    # -----------------------------------------------------------

    @staticmethod
    def _get_dep_to_files(file2deps, mod2files):

        dep2files = {}
        tmp_file2deps = {}

        for file, mods in file2deps.items():
            for mod in mods:
                files = mod2files[mod]
                tmp_file2deps.setdefault(file, set()).update(files)
                for f in files:
                    dep2files.setdefault(f, set()).add(file)

        return dep2files, tmp_file2deps

    # -----------------------------------------------------------

    @staticmethod
    def _get_content(files_content, dep2files, file2deps, tails):

        content = ""
        while tails:
            tail = tails.pop(0)
            content += files_content[tail]

            files = dep2files.pop(tail, [])

            for file in files:
                deps = file2deps[file]
                deps.remove(tail)
                if not deps:
                    tails.append(file)
                    del file2deps[file]

        return content

    # -----------------------------------------------------------

    def build(self, source_entities, targets):

        file2deps = {}
        files_content = {}
        modules = set()
        tails = []

        std_modules = set()

        for entity in source_entities:
            file_name = entity.name
            mod_std_imports, mod_deps, mod_content = entity.data

            if not mod_content:
                continue

            if not mod_deps:
                tails.append(file_name)

            files_content[file_name] = mod_content
            file2deps[file_name] = mod_deps

            std_modules.update(mod_std_imports)
            modules.update(mod_deps)

        mod2files = self._mod_to_files(file2deps, modules)

        dep2files, file2deps = self._get_dep_to_files(file2deps, mod2files)

        content = self._get_content(files_content, dep2files, file2deps, tails)

        imports_content = '\n'.join(
            "import %s" % module for module in sorted(std_modules))

        content = imports_content + '\n' + content

        target = aql.SimpleEntity(data=content)
        targets.add_target_entity(target)


# ==============================================================================
class AqlEmbedTools (aql.FileBuilder):

    split = aql.FileBuilder.split_single

    # ----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Embed tools"

    # ----------------------------------------------------------

    def replace(self, options, source_entities):

        nodes = []

        finder = aql.FindFilesBuilder(options, '*.py')

        for source in source_entities:
            tools_path = source.get()

            tool_files = aql.Node(finder, (source,))

            zip_file = hashlib.md5(tools_path).hexdigest()

            zipper = aql.ZipFilesBuilder(options,
                                         target=zip_file,
                                         basedir=tools_path)

            zip_arch = aql.Node(zipper, tool_files)
            nodes.append(zip_arch)

        return nodes

    # ----------------------------------------------------------

    @staticmethod
    def _split_content(content):
        result = []
        pos = 0
        size = len(content)
        line_size = 64
        while (pos + line_size) < size:
            line = content[pos:line_size]
            result.append(line)
            pos += line_size

        line = content[pos:]
        if line:
            result.append(line)

        return result

    # -----------------------------------------------------------

    def build(self, source_entities, targets):
        for source in source_entities:
            zip_file = source.get()

            content = aql.read_bin_file(zip_file)
            content = base64.b64encode(content)

            result = self._split_content(content)

            result = '_EMBEDDED_EXTERNAL_TOOLS.append("""' +\
                     '\n'.join(result) + '\n""")'

            target = aql.SimpleEntity(data=result)
            targets.add_target_entity(target)


# ==============================================================================
class AqlLink (aql.FileBuilder):

    def __init__(self, options, target):
        self.target = self.get_target_path(target)

    # -----------------------------------------------------------

    def get_trace_name(self, source_entities, brief):
        return "Link AQL script"

    # ----------------------------------------------------------

    def get_trace_sources(self, source_entities, brief):
        return None

    # ----------------------------------------------------------

    def get_target_entities(self, source_values):
        return self.target

    # ----------------------------------------------------------

    def build(self, source_entities, targets):
        content = HEADER + '\n'

        for source in source_entities:
            content += source.get()
            content += '\n'

        content += MAIN

        aql.write_text_file(self.target, content)
        targets.add_target_files(self.target)


# ==============================================================================
class AqlBuildTool(aql.Tool):

    def join(self, options):
        return AqlJoin(options)

    def embed_tools(self, options):
        return AqlEmbedTools(options)

    def link(self, options, target):
        return AqlLink(options, target)

    Join = join
    EmbedTools = embed_tools
    Link = link
