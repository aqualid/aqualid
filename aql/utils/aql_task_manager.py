#
# Copyright (c) 2011-2015 The developers of Aqualid project
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


import threading
import traceback

try:
    import queue
except ImportError:
    import Queue as queue  # python 2

from .aql_logging import log_warning

__all__ = (
    'TaskManager', 'TaskResult'
)

# ==============================================================================


class _StopException(Exception):
    pass


class _StopTask(object):

    __slots__ = (
        'task_id',
    )

    def __init__(self):
        self.task_id = None

    def __lt__(self, other):
        return True

    def __call__(self):
        raise _StopException()

_stop_task = _StopTask()

# ==============================================================================


class _Task(object):
    __slots__ = (
        'priority',
        'task_id',
        'func',
        'args',
        'kw'
    )

    def __init__(self, priority, task_id, func, args, kw):

        self.priority = priority
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kw = kw

    def __lt__(self, other):
        if isinstance(other, _StopTask):
            return False

        return self.priority < other.priority

    def __call__(self):
        return self.func(*self.args, **self.kw)

# ==============================================================================


class TaskResult (object):
    __slots__ = ('task_id', 'error', 'result')

    def __init__(self, task_id=None, result=None, error=None):
        self.task_id = task_id
        self.result = result
        self.error = error

    def __lt__(self, other):
        return (self.task_id, self.result, self.error) < \
               (other.task_id, other.result, other.error)

    def __eq__(self, other):
        return (self.task_id, self.result, self.error) == \
               (other.task_id, other.result, other.error)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "task_id: %s, result: %s, error: %s" %\
               (self.task_id, self.result, self.error)

# ==============================================================================


class _TaskExecutor(threading.Thread):

    def __init__(self,
                 tasks,
                 finished_tasks,
                 stop_on_error,
                 stop_event,
                 with_backtrace):

        super(_TaskExecutor, self).__init__()

        self.tasks = tasks
        self.finished_tasks = finished_tasks
        self.stop_on_error = stop_on_error
        self.stop_event = stop_event
        # let that main thread to exit even if task threads are still active
        self.daemon = True
        self.with_backtrace = with_backtrace

        self.start()

    # -----------------------------------------------------------

    def run(self):

        tasks = self.tasks
        finished_tasks = self.finished_tasks
        is_stopped = self.stop_event.is_set

        while not is_stopped():
            task = tasks.get()

            task_id = task.task_id

            if task_id is not None:
                task_result = TaskResult(task_id=task_id)
            else:
                task_result = None

            try:
                result = task()

                if task_result is not None:
                    task_result.result = result

            except _StopException:
                task_result = None
                break

            except (Exception, BaseException) as ex:
                self.fail_task(task_result, ex)

            finally:
                if task_result is not None:
                    finished_tasks.put(task_result)

                tasks.task_done()

    # ==========================================================

    def fail_task(self, task_result, ex):
        task_result.error = "Internal error"

        if self.with_backtrace:
            err = traceback.format_exc()
        else:
            err = str(ex)

        if task_result is not None:
            task_result.error = err
        else:
            log_warning("Task failed with error: %s" % (err,))

        if self.stop_on_error:
            self.stop_event.set()


# ==============================================================================


class TaskManager (object):
    __slots__ = (

        'lock',
        'threads',
        'tasks',
        'finished_tasks',
        'unfinished_tasks',
        'stop_on_error',
        'stop_event',
        'with_backtrace',
    )

    # -----------------------------------------------------------

    def __init__(self, num_threads, stop_on_fail=False, with_backtrace=True):
        self.tasks = queue.PriorityQueue()
        self.finished_tasks = queue.Queue()
        self.lock = threading.Lock()
        self.unfinished_tasks = 0
        self.threads = []
        self.stop_on_error = stop_on_fail
        self.stop_event = threading.Event()
        self.with_backtrace = with_backtrace

        self.start(num_threads)

    # -----------------------------------------------------------

    def start(self, num_threads):
        with self.lock:
            if self.stop_event.is_set():
                self.__stop()

            threads = self.threads

            num_threads -= len(threads)

            while num_threads > 0:
                num_threads -= 1
                t = _TaskExecutor(self.tasks,
                                  self.finished_tasks,
                                  self.stop_on_error,
                                  self.stop_event,
                                  self.with_backtrace)
                threads.append(t)

    # -----------------------------------------------------------

    def __stop(self):
        threads = self.threads
        if not threads:
            return

        for t in threads:
            self.tasks.put(_stop_task)

        for t in threads:
            t.join()

        self.threads = []
        self.tasks = queue.PriorityQueue()
        self.stop_event.clear()

    # -----------------------------------------------------------

    def stop(self):
        self.stop_event.set()
        with self.lock:
            self.__stop()

    # -----------------------------------------------------------

    def add_task(self, priority, task_id, function, *args, **kw):
        with self.lock:
            task = _Task(priority, task_id, function, args, kw)
            self.tasks.put(task)
            if task_id is not None:
                self.unfinished_tasks += 1

    # -----------------------------------------------------------

    def get_finished_tasks(self, block=True):
        result = []
        is_stopped = self.stop_event.is_set
        finished_tasks = self.finished_tasks
        with self.lock:

            if is_stopped():
                self.__stop()

            if block:
                block = (self.unfinished_tasks > 0) and self.threads

            while True:
                try:
                    task_result = finished_tasks.get(block=block)
                    block = False

                    result.append(task_result)
                    finished_tasks.task_done()
                except queue.Empty:
                    if self.tasks.empty() and not self.threads:
                        self.unfinished_tasks = 0
                        return result
                    break

            self.unfinished_tasks -= len(result)
            assert self.unfinished_tasks >= 0

        return result
