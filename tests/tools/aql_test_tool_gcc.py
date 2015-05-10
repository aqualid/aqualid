import os
import sys
import itertools

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import AqlTestCase
from tests_utils import run_local_tests

from aql.utils import Tempfile, Tempdir

from aql.main import Project, ProjectConfig

# ==============================================================================


class TestToolGcc(AqlTestCase):

    # -----------------------------------------------------------

    def test_gcc_compiler(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')
            src_dir = os.path.join(tmp_dir, 'src')
            os.makedirs(src_dir)

            num_src_files = 5

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            gcc = prj.tools.try_tool('g++', tools_path=tools_path)
            if gcc is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            gcc.Compile(src_files, batch_build=False)
            self.build_prj(prj, num_src_files)

            gcc.Compile(src_files, batch_build=False)
            self.build_prj(prj, 0)

            gcc.Compile(src_files, batch_build=False)

            self.touch_cpp_file(hdr_files[0])
            self.build_prj(prj, 1)

            gcc.Compile(src_files, batch_build=False)
            self.build_prj(prj, 0)

            gcc.Compile(src_files, batch_build=False)
            self.clear_prj(prj)

    def test_gcc_compiler_target(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')
            src_dir = os.path.join(tmp_dir, 'src')
            os.makedirs(src_dir)

            num_src_files = 2

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)
            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            gcc = prj.tools.try_tool('g++', tools_path=tools_path)
            if gcc is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            gcc.options.batch_build = False
            gcc.options.If().target.is_true().objsuffix = ''

            targets = [os.path.join(build_dir, 'src_file%s.o' % i)
                       for i in range(len(src_files))]

            for src, target in zip(src_files, targets):
                gcc.Compile(src, target=target)

            for target in targets:
                self.assertFalse(os.path.isfile(target))

            self.build_prj(prj, num_src_files)

            for target in targets:
                self.assertTrue(os.path.isfile(target))

            for src, target in zip(src_files, targets):
                gcc.Compile(src, target=target)

            self.build_prj(prj, 0)

            for src, target in zip(src_files, targets):
                gcc.Compile(src, target=target)

            self.clear_prj(prj)

            for target in targets:
                self.assertFalse(os.path.isfile(target))

    # ==============================================================================

    def test_gcc_compiler_target_errors(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')
            src_dir = os.path.join(tmp_dir, 'src')
            os.makedirs(src_dir)

            num_src_files = 2

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)
            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            gcc = prj.tools.try_tool('g++', tools_path=tools_path)
            if gcc is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            gcc.Compile(src_files, target='src_file0', batch_build=False)

            try:
                prj.build()
                raise AssertionError("No Exception")
            except Exception as ex:
                self.assertEqual(ex.__class__.__name__,
                                 'ErrorCompileWithCustomTarget')

            gcc.Compile(src_files, target='src_file0', batch_build=True)

            try:
                prj.build()
                raise AssertionError("No Exception")
            except Exception as ex:
                self.assertEqual(ex.__class__.__name__,
                                 'ErrorBatchCompileWithCustomTarget')

    # -----------------------------------------------------------

    def test_gcc_res_compiler(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')
            src_dir = os.path.join(tmp_dir, 'src')
            os.makedirs(src_dir)

            num_src_files = 2

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)
            res_file = self.generate_res_file(src_dir, 'foo')

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)
            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            gcc = prj.tools.try_tool('g++', tools_path=tools_path)
            if gcc is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            rc = prj.tools.try_tool('windres', tools_path=tools_path)
            if rc is None:
                print("WARNING: Windres tool has not been found. "
                      "Skip the test.")
                return

            gcc.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.build_prj(prj, num_src_files + 1)

            gcc.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.build_prj(prj, 0)

            gcc.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.touch_cpp_file(res_file)
            self.build_prj(prj, 1)

            gcc.Compile(src_files, batch_build=False)
            rc.Compile(res_file)
            self.build_prj(prj, 0)

    # -----------------------------------------------------------

    def test_gcc_archiver(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_groups = 4
            group_size = 8
            num_src_files = num_groups * group_size

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            cpp = prj.tools.try_tool('g++', tools_path=tools_path)
            if cpp is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            cpp.LinkLibrary(src_files, target='foo', batch_build=False)

            self.build_prj(prj, num_src_files + 1)

            cpp.LinkLibrary(src_files, target='foo')
            self.build_prj(prj, 0)

            self.touch_cpp_file(hdr_files[0])

            cpp.LinkLibrary(src_files, target='foo')
            self.build_prj(prj, 1)

            # prj.config.debug_explain = True

            cpp.LinkLibrary(src_files, target='foo', batch_build=False)
            self.build_prj(prj, 0)

            self.touch_cpp_files(hdr_files)

            cpp.LinkLibrary(src_files, target='foo', batch_build=False)
            self.build_prj(prj, num_src_files)

    # -----------------------------------------------------------

    def test_gcc_linker(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_groups = 4
            group_size = 8
            num_src_files = num_groups * group_size

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)
            main_src_file = self.generate_main_cpp_file(src_dir, 'main')

            cfg = ProjectConfig(
                args=["build_dir=%s" % build_dir, "batch_build=0"])

            prj = Project(cfg)

            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            cpp = prj.tools.try_tool('g++', tools_path=tools_path)
            if cpp is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            cpp.LinkSharedLibrary(src_files, target='foo')
            cpp.LinkSharedLibrary(src_files, target='foo')
            cpp.LinkProgram(src_files, main_src_file, target='foo')

            self.build_prj(prj, num_src_files + 3)

            cpp.LinkSharedLibrary(src_files, target='foo')
            cpp.LinkProgram(src_files, main_src_file, target='foo')
            self.build_prj(prj, 0)

            self.touch_cpp_file(hdr_files[0])

            cpp.LinkSharedLibrary(src_files, target='foo')
            cpp.LinkProgram(src_files, main_src_file, target='foo')
            self.build_prj(prj, 1)

            self.touch_cpp_files(hdr_files)
            cpp.LinkSharedLibrary(src_files, target='foo', batch_build=False)
            cpp.LinkProgram(
                src_files, main_src_file, target='foo', batch_build=False)
            self.build_prj(prj, num_src_files)

    # -----------------------------------------------------------

    def test_gcc_compiler_batch(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_groups = 4
            group_size = 8
            num_src_files = num_groups * group_size

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            cpp = prj.tools.try_tool('g++', tools_path=tools_path)
            if cpp is None:
                print("WARNING: g++ tool has not been found. Skip the test.")
                return

            cpp.Compile(src_files, batch_build=True)
            self.build_prj(prj, num_groups, jobs=num_groups)

            cpp.Compile(src_files, batch_build=False)
            self.build_prj(prj, 0)

            self.touch_cpp_file(hdr_files[0])
            cpp.Compile(src_files, batch_build=False)
            self.build_prj(prj, 1)

            self.touch_cpp_files(hdr_files[:group_size])

            cpp.Compile(src_files, batch_build=True, batch_groups=num_groups)
            self.build_prj(prj, num_groups)

            cpp.Compile(src_files, batch_build=True, batch_groups=num_groups)
            self.clear_prj(prj)

    # -----------------------------------------------------------

    def test_gcc_compiler_batch_error(self):
        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'output')
            src_dir = os.path.join(tmp_dir, 'src')

            os.makedirs(src_dir)

            num_src_files = 5

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            src_file_orig = Tempfile(folder=tmp_dir)
            src_file_orig.close()

            self.copy_file(src_files[0], src_file_orig)

            self.add_error_to_cpp_file(src_files[0])

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)

            tools_path = os.path.join(os.path.dirname(__file__),
                                      '../../tools')
            cpp = prj.tools.try_tool('g++', tools_path=tools_path)
            if cpp is None:
                print("WARNING: g++ tool has not been found. Skip the test.")
                return

            cpp.Compile(src_files, batch_build=True, batch_groups=1)

            self.build_prj(prj, 0, num_failed_nodes=1)

            self.copy_file(src_file_orig, src_files[0])

            cpp.Compile(src_files)

            self.build_prj(prj, 1)

    # -----------------------------------------------------------

    def test_gcc_copy_ideps(self):

        with Tempdir() as tmp_dir:

            build_dir = os.path.join(tmp_dir, 'build')
            src_dir = os.path.join(tmp_dir, 'src')
            copy_dir = os.path.join(tmp_dir, 'dist')
            os.makedirs(src_dir)

            num_src_files = 5

            src_files, hdr_files = self.generate_cpp_files(
                src_dir, 'foo', num_src_files)

            cfg = ProjectConfig(args=["build_dir=%s" % build_dir])

            prj = Project(cfg)
            tools_path = os.path.join(os.path.dirname(__file__), '../../tools')
            gcc = prj.tools.try_tool('g++', tools_path=tools_path)
            if gcc is None:
                print("WARNING: GCC tool has not been found. Skip the test.")
                return

            node = gcc.Compile(src_files, batch_build=False)
            prj.tools.CopyFiles(node.filter_sources(),
                                node.filter_implicit_dependencies(),
                                target=copy_dir,
                                batch_groups=1)

            self.build_prj(prj, num_src_files + 1)

            for file in itertools.chain(src_files, hdr_files):
                self.assertTrue(os.path.isfile(
                    os.path.join(copy_dir, os.path.basename(file))))

            node = gcc.Compile(src_files, batch_build=False)
            prj.tools.CopyFiles(node.filter_sources(),
                                node.filter_implicit_dependencies(),
                                target=copy_dir,
                                batch_groups=1)
            self.build_prj(prj, 0)

# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
