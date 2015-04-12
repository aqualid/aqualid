import os
import sys

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import Tempdir, Tempfile
from aql.main import Project, ProjectConfig, ErrorToolNotFound

# ==============================================================================


class TestToolMsvc(AqlTestCase):

    def test_msvc_compiler(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_src_files = 5

            src_files, hdr_files = self.generateCppFiles(
                src_dir, 'foo', num_src_files)
            res_file = self.generateResFile(src_dir, 'foo')

            cfg = ProjectConfig(
                args=["build_dir=%s" % build_dir, "batch_build=0"])

            prj = Project(cfg)

            try:
                cpp = prj.tools.Tool(
                    'msvc++', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MSVC tool has not been found. Skip the test.")
                return

            cpp.Compile(src_files, batch_build=False)
            cpp.CompileResource(res_file)

            self.buildPrj(prj, num_src_files + 1)

            cpp.Compile(src_files)
            cpp.CompileResource(res_file)

            self.buildPrj(prj, 0)

            self.touchCppFile(hdr_files[0])

            cpp.Compile(src_files)
            self.buildPrj(prj, 1)

    # -----------------------------------------------------------

    def test_msvc_compiler_batch(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_groups = 4
            group_size = 8
            num_src_files = num_groups * group_size

            src_files, hdr_files = self.generateCppFiles(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            try:
                cpp = prj.tools.Tool(
                    'msvc++', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MSVC tool has not been found. Skip the test.")
                return

            cpp.Compile(src_files, batch_build=True)
            self.buildPrj(prj, num_groups, jobs=num_groups)

            cpp.Compile(src_files, batch_build=False)
            self.buildPrj(prj, 0)

            self.touchCppFile(hdr_files[0])
            cpp.Compile(src_files, batch_build=False)
            self.buildPrj(prj, 1)

            self.touchCppFiles(hdr_files[:group_size])

            cpp.Compile(src_files, batch_build=True, batch_groups=num_groups)
            self.buildPrj(prj, num_groups)

    # -----------------------------------------------------------

    def test_msvc_compiler_batch_error(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_src_files = 5

            src_files, hdr_files = self.generateCppFiles(
                src_dir, 'foo', num_src_files)

            src_file_orig = Tempfile(folder=tmp_dir)
            src_file_orig.close()

            self.copyFile(src_files[0], src_file_orig)

            self.addErrorToCppFile(src_files[0])

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            try:
                cpp = prj.tools.Tool(
                    'msvc++', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MSVC tool has not been found. Skip the test.")
                return

            cpp.Compile(src_files, batch_build=True, batch_groups=1)

            self.buildPrj(prj, 0, num_failed_nodes=1)

            self.copyFile(src_file_orig, src_files[0])

            cpp.Compile(src_files)

            self.buildPrj(prj, 1)

    # -----------------------------------------------------------

    def test_msvc_archiver(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_groups = 4
            group_size = 8
            num_src_files = num_groups * group_size

            src_files, hdr_files = self.generateCppFiles(
                src_dir, 'foo', num_src_files)
            res_file = self.generateResFile(src_dir, 'foo')

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            try:
                cpp = prj.tools.Tool(
                    'msvc++', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MSVC tool has not been found. Skip the test.")
                return

            cpp.LinkLibrary(
                src_files, res_file, target='foo', batch_build=True, batch_groups=num_groups)

            self.buildPrj(prj, num_groups + 2)

            cpp.LinkLibrary(src_files, res_file, target='foo')
            self.buildPrj(prj, 0)

            self.touchCppFile(hdr_files[0])

            cpp.LinkLibrary(src_files, res_file, target='foo')
            self.buildPrj(prj, 2)

            cpp.LinkLibrary(
                src_files, res_file, target='foo', batch_build=True)
            self.buildPrj(prj, 0)

            self.touchCppFiles(hdr_files)
            cpp.LinkLibrary(
                src_files, res_file, target='foo', batch_build=True, batch_groups=num_groups)
            self.buildPrj(prj, num_groups + 1)

    # -----------------------------------------------------------

    def test_msvc_linker(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_groups = 4
            group_size = 2
            num_src_files = num_groups * group_size

            src_files, hdr_files = self.generateCppFiles(
                src_dir, 'foo', num_src_files)
            res_file = self.generateResFile(src_dir, 'foo')
            main_src_file = self.generateMainCppFile(src_dir, 'main')

            cfg = ProjectConfig(
                args=["build_dir=%s" % build_dir, "batch_build=0"])

            prj = Project(cfg)

            try:
                cpp = prj.tools.Tool(
                    'msvc++', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MSVC tool has not been found. Skip the test.")
                return

            cpp.LinkSharedLibrary(src_files, res_file, target='foo')
            cpp.LinkSharedLibrary(src_files, res_file, target='foo')
            cpp.LinkProgram(src_files, main_src_file, res_file, target='foo')

            self.buildPrj(prj, num_src_files + 4)

            cpp.LinkSharedLibrary(src_files, res_file, target='foo')
            cpp.LinkProgram(src_files, main_src_file, res_file, target='foo')
            self.buildPrj(prj, 0)

            self.touchCppFile(hdr_files[0])

            cpp.LinkSharedLibrary(src_files, res_file, target='foo')
            cpp.LinkProgram(src_files, main_src_file, res_file, target='foo')
            self.buildPrj(prj, 3)

            self.touchCppFiles(hdr_files)

            cpp.LinkSharedLibrary(
                src_files, res_file, target='foo', batch_build=True, batch_groups=num_groups)
            cpp.LinkProgram(src_files, main_src_file, res_file,
                            target='foo', batch_build=True, batch_groups=num_groups)
            self.buildPrj(prj, num_groups + 2, jobs=1)

    # -----------------------------------------------------------

    def test_msvc_res_compiler(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')
            src_dir = os.path.join(tmp_dir, 'src')
            os.makedirs(src_dir)

            num_src_files = 2

            src_files, hdr_files = self.generateCppFiles(
                src_dir, 'foo', num_src_files)
            res_file = self.generateResFile(src_dir, 'foo')

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)
            try:
                cpp = prj.tools.Tool(
                    'msvc++', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MSVC tool has not been found. Skip the test.")
                return
            try:
                rc = prj.tools.Tool(
                    'msrc', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
            except ErrorToolNotFound:
                print("WARNING: MS RC tool has not been found. Skip the test.")
                return

            cpp.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.buildPrj(prj, num_src_files + 1)

            cpp.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.buildPrj(prj, 0)

            cpp.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.touchCppFile(res_file)
            self.buildPrj(prj, 1)

            cpp.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.buildPrj(prj, 0)

# ==============================================================================

if __name__ == "__main__":
    runLocalTests()
