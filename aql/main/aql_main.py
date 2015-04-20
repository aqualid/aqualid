#
# Copyright (c) 2014-2015 The developers of Aqualid project
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

import gc
import os
import sys
import pstats
import traceback

from aql.util_types import to_unicode
from aql.utils import event_status, event_error, EventSettings,\
    set_event_settings, Chrono, Chdir, memory_usage,\
    split_path, expand_file_path,\
    log_info, log_error, set_log_level, LOG_WARNING

from .aql_project import Project, ProjectConfig
from .aql_info import get_aql_info, dump_aql_info

__all__ = ('main', )

# ==============================================================================


@event_status
def event_reading_scripts(settings):
    log_info("Reading scripts...")


@event_status
def event_reading_scripts_done(settings, elapsed):
    log_info("Reading scripts finished (%s)" % elapsed)


@event_error
def event_aql_error(settings, error):
    log_error(error)

# ==============================================================================


@event_status
def event_building(settings):
    log_info("Building targets...")


@event_status
def event_building_done(settings, success, elapsed):
    status = "finished" if success else "failed"
    log_info("Building targets %s (%s)" % (status, elapsed))

# ==============================================================================


@event_status
def event_build_summary(settings, elapsed):
    log_info("Total time: %s" % elapsed)

# ==============================================================================


def _find_make_script(script):

    if os.path.isabs(script):
        return script

    cwd = split_path(os.path.abspath('.'))
    path_sep = os.path.sep

    while cwd:
        script_path = path_sep.join(cwd) + path_sep + script
        if os.path.isfile(script_path):
            return os.path.normpath(script_path)

        cwd.pop()

    return script

# ==============================================================================


def _start_memory_tracing():
    try:
        import tracemalloc
    except ImportError:
        return

    tracemalloc.start()

# ==============================================================================


def _stop_memory_tracing():
    try:
        import tracemalloc
    except ImportError:
        return

    snapshot = tracemalloc.take_snapshot()

    _log_memory_top(snapshot)

    tracemalloc.stop()

# ==============================================================================


def _log_memory_top(snapshot, group_by='lineno', limit=30):

    try:
        import tracemalloc
        import linecache
    except ImportError:
        return

    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))

    top_stats = snapshot.statistics(group_by)

    log_info("Top %s lines" % limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace "/path/to/module/file.py" with "module/file.py"
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        log_info("#%s: %s:%s: %.1f KiB"
                % (index, filename, frame.lineno, stat.size / 1024))
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            log_info('    %s' % line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        log_info("%s other: %.1f KiB" % (len(other), size / 1024))
    total = sum(stat.size for stat in top_stats)
    log_info("Total allocated size: %.1f KiB" % (total / 1024))

# ==============================================================================


def _print_memory_status():

    _stop_memory_tracing()

    mem_usage = memory_usage()
    num_objects = len(gc.get_objects())

    obj_mem_usage = sum(sys.getsizeof(obj) for obj in gc.get_objects())

    log_info("GC objects: %s, size: %.1f KiB, heap memory usage: %s Kb" %
            (num_objects, obj_mem_usage / 1024, mem_usage))

# ==============================================================================


def _set_build_dir(options, makefile):
    build_dir = options.build_dir.get()
    if os.path.isabs(build_dir):
        return

    makefile_dir = os.path.abspath(os.path.dirname(makefile))
    options.build_dir = os.path.join(makefile_dir, build_dir)

# ==============================================================================


def _read_make_script(prj):
    prj_cfg = prj.config

    makefile = expand_file_path(prj_cfg.makefile)

    if prj_cfg.search_up:
        makefile = _find_make_script(makefile)

    _set_build_dir(prj_cfg.options, makefile)

    event_reading_scripts()

    with Chrono() as elapsed:
        prj.Script(makefile)

    event_reading_scripts_done(elapsed)

# ==============================================================================


def _list_options(prj):
    prj_cfg = prj.config

    text = []

    if prj_cfg.list_options:
        text += prj.ListOptions(brief=not prj_cfg.verbose)

    if prj_cfg.list_tool_options:
        text += prj.ListToolsOptions(
            prj_cfg.list_tool_options, brief=not prj_cfg.verbose)

    log_info('\n'.join(text))


# ==============================================================================

def _build(prj):
    event_building()

    with Chrono() as elapsed:
        success = prj.Build()

    event_building_done(success, elapsed)

    if not success:
        prj.build_manager.print_fails()

    return success


# ==============================================================================


def _main(prj_cfg):
    with Chrono() as total_elapsed:

        ev_settings = EventSettings(brief=not prj_cfg.verbose,
                                    with_output=not prj_cfg.no_output,
                                    trace_exec=prj_cfg.debug_exec)
        set_event_settings(ev_settings)

        with Chdir(prj_cfg.directory):

            if prj_cfg.debug_memory:
                _start_memory_tracing()

            prj = Project(prj_cfg)

            _read_make_script(prj)

            success = True

            if prj_cfg.clean:
                prj.Clear()

            elif prj_cfg.list_targets:
                text = prj.ListTargets()
                log_info('\n'.join(text))

            elif prj_cfg.list_options or prj_cfg.list_tool_options:
                _list_options(prj_cfg)
            else:
                success = _build(prj)

            if prj_cfg.debug_memory:
                _print_memory_status()

    event_build_summary(total_elapsed)

    status = int(not success)

    return status

# ==============================================================================


def _patch_sys_modules():
    aql_module = sys.modules.get('aql', None)
    if aql_module is not None:
        sys.modules.setdefault(get_aql_info().module, aql_module)
    else:
        aql_module = sys.modules.get(get_aql_info().module, None)
        if aql_module is not None:
            sys.modules.setdefault('aql', aql_module)

# ==============================================================================


def _run_main(prj_cfg):
    debug_profile = prj_cfg.debug_profile

    if not debug_profile:
        status = _main(prj_cfg)
    else:
        profiler = c_profile.Profile()

        status = profiler.runcall(_main, prj_cfg)

        profiler.dump_stats(debug_profile)

        p = pstats.Stats(debug_profile)
        p.strip_dirs()
        p.sort_stats('cumulative')
        p.print_stats(prj_cfg.debug_profile_top)

    return status

# ==============================================================================


def _log_error(ex, with_backtrace):
    if with_backtrace:
        err = traceback.format_exc()
    else:
        if isinstance(ex, KeyboardInterrupt):
            err = "Keyboard Interrupt"
        else:
            err = to_unicode(ex)

    event_aql_error(err)

# ==============================================================================


def main():
    with_backtrace = True
    try:
        _patch_sys_modules()

        prj_cfg = ProjectConfig()
        with_backtrace = prj_cfg.debug_backtrace

        if prj_cfg.show_version:
            log_info(dump_aql_info())
            return 0

        if prj_cfg.silent:
            set_log_level(LOG_WARNING)

        status = _run_main(prj_cfg)

    except (Exception, KeyboardInterrupt) as ex:
        _log_error(ex, with_backtrace)
        status = 1

    return status

# ==============================================================================
