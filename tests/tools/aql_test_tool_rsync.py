import os
import sys

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import skip, AqlTestCase, run_local_tests

from aql.utils import Tempdir
from aql.main import Project, ProjectConfig, ErrorToolNotFound

# ==============================================================================


def _build(prj):
    if not prj.build():
        prj.build_manager.print_fails()
        assert False, "Build failed"

# ==============================================================================


class TestToolRsync(AqlTestCase):

    def test_rsync_push_local(self):
        with Tempdir() as tmp_dir:
            with Tempdir() as src_dir:
                with Tempdir() as target_dir:
                    src_files = self.generate_cpp_files(src_dir, "src_test", 3)

                    cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir])

                    prj = Project(cfg)

                    try:
                        rsync = prj.tools.get_tool(
                            'rsync', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
                    except ErrorToolNotFound:
                        print(
                            "WARNING: Rsync tool has not been found. Skip the test.")
                        return

                    rsync.Push(src_files, target=target_dir)

                    _build(prj)

                    rsync.Push(src_files, target=target_dir)

                    _build(prj)

    # ==========================================================

    @skip
    def test_rsync_push_remote(self):
        with Tempdir() as tmp_dir:
            with Tempdir() as src_dir:
                src_files = self.generate_cpp_files(src_dir, "src_test", 3)

                cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir])

                prj = Project(cfg)

                rsync = prj.tools.get_tool(
                    'rsync', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))

                remote_files = rsync.Push(src_dir + '/', target='test_rsync_push/',
                                          host='nas', key_file=r'C:\cygwin\home\me\rsync.key',
                                          exclude="*.h")
                remote_files.options.rsync_flags += ['--chmod=u+xrw,g+xr,o+xr']
                remote_files.options.rsync_flags += ['--delete-excluded']
                _build(prj)

    # ==========================================================

    def test_rsync_pull(self):
        with Tempdir() as tmp_dir:
            with Tempdir() as src_dir:
                with Tempdir() as target_dir:
                    src_files = self.generate_cpp_files(src_dir, "src_test", 3)

                    cfg = ProjectConfig(args=["build_dir=%s" % tmp_dir])

                    prj = Project(cfg)

                    try:
                        rsync = prj.tools.get_tool(
                            'rsync', tools_path=os.path.join(os.path.dirname(__file__), '../../tools'))
                    except ErrorToolNotFound:
                        print(
                            "WARNING: Rsync tool has not been found. Skip the test.")
                        return

                    rsync.Pull(src_files, target=target_dir)

                    _build(prj)

                    rsync.Pull(src_files, target=target_dir)

                    _build(prj)

# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
