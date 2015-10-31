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
import weakref

try:
    import queue
except ImportError:
    import Queue as queue  # python 2

from .aql_logging import log_warning

__all__ = (
    'TaskManager', 'TaskResult'
)
#
#
# ==============================================================================
# class _SharedLock(object):
#     def __init__(self):
#         self.cond = threading.Condition(threading.Lock())
#         self.state = 0
#
#     # ----------------------------------------------------------
#
#     def acquire_shared(self):
#         cond = self.cond
#         with cond:
#             while self.state < 0:
#                 cond.wait()
#
#             self.state += 1
#
#         return self
#
#     # ----------------------------------------------------------
#
#     def acquire_exclusive(self):
#         cond = self.cond
#         with cond:
#             while self.state != 0:
#                 cond.wait()
#
#             self.state -= 1
#
#         return self
#
#     # ----------------------------------------------------------
#
#     def release(self):
#         cond = self.cond
#         with cond:
#             if self.state > 0:
#                 self.state -= 1
#             else:
#                 self.state += 1
#             if self.state == 0:
#                 cond.notify_all()
#
#     # ----------------------------------------------------------
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.release()
#
#
# ==============================================================================
# class _SharedLockStub(object):
#     def acquire_shared(self):
#         return self
#
#     # ----------------------------------------------------------
#
#     def acquire_exclusive(self):
#         return self
#
#     # ----------------------------------------------------------
#
#     def release(self):
#         pass
#
#     # ----------------------------------------------------------
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         pass


# ==============================================================================
class _StopException(Exception):
    pass


class _NullTask(object):

    __slots__ = (
        'task_id',
    )

    def __init__(self):
        self.task_id = None

    def __lt__(self, other):
        return True

    def __call__(self):
        pass

_null_task = _NullTask()


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
        if isinstance(other, _NullTask):
            return False

        if isinstance(other, _ExpensiveTask):
            return True

        return self.priority < other.priority

    def __call__(self):
        return self.func(*self.args, **self.kw)


# ==============================================================================
class _ExpensiveTask(_Task):
    def __init__(self, task_manager, task_id, func, args, kw):
        super(_ExpensiveTask, self).__init__(None, task_id, func, args, kw)
        self.task_manager = weakref.ref(task_manager)

    def __lt__(self, other):
        return False

    def __enter__(self):
        task_manager = self.task_manager()
        if task_manager is not None:
            task_manager._pause()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        task_manager = self.task_manager()
        if task_manager is not None:
            failed = exc_type is not None
            task_manager._resume(failed=failed)

        return False

    def __call__(self):
        with self:
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
class _Worker(threading.Thread):

    def __init__(self, tasks, finished_tasks, fail_event,
                 stop_event, stop_on_fail, with_backtrace):

        super(_Worker, self).__init__()

        self.tasks = tasks
        self.finished_tasks = finished_tasks
        self.stop_on_fail = stop_on_fail
        self.stop_event = stop_event
        self.fail_event = fail_event

        # let the main thread to exit even if task threads are still active
        self.daemon = True
        self.with_backtrace = with_backtrace

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

            except BaseException as ex:
                self.fail_task(task_result, ex)

            finally:
                if task_result is not None:
                    finished_tasks.put(task_result)

                tasks.task_done()

    # ----------------------------------------------------------

    def fail_task(self, task_result, ex):
        task_result.error = "Internal error"

        if self.with_backtrace:
            err = traceback.format_exc()
        else:
            err = str(ex)

        if task_result is not None:
            task_result.error = err
        else:
            log_warning("Task failed with error: %s", err)

        if self.stop_on_fail:
            self.stop_event.set()
            self.fail_event.set()


# ==============================================================================
class TaskManager (object):
    __slots__ = (

        'threads_lock',
        'num_threads',
        'threads',
        'tasks_lock',
        'tasks',
        'finished_tasks',
        'unfinished_tasks',
        'stop_on_fail',
        'stop_event',
        'fail_event',
        'with_backtrace',
    )

    # -----------------------------------------------------------

    def __init__(self, num_threads, stop_on_fail=False, with_backtrace=True):

        self.tasks = queue.PriorityQueue()
        self.finished_tasks = queue.Queue()
        self.threads_lock = threading.Lock()
        self.tasks_lock = threading.Lock()
        self.unfinished_tasks = 0
        self.num_threads = num_threads if num_threads > 1 else 1
        self.threads = []
        self.stop_on_fail = stop_on_fail
        self.stop_event = threading.Event()
        self.fail_event = threading.Event()
        self.with_backtrace = with_backtrace

        self.start(num_threads)

    # ----------------------------------------------------------

    def __start(self, num_threads):
        with self.tasks_lock:
            threads = self.threads

            if num_threads < 0:
                num_threads = self.num_threads

            num_threads -= len(threads)

            while num_threads > 0:
                num_threads -= 1
                t = _Worker(self.tasks, self.finished_tasks,
                            self.fail_event, self.stop_event,
                            self.stop_on_fail, self.with_backtrace)
                threads.append(t)

                t.start()

            self.num_threads = len(threads)

    # -----------------------------------------------------------

    def __stop(self):
        remain_threads = []

        current_thread_id = threading.current_thread().ident

        put_task = self.tasks.put

        for thread in self.threads:
            put_task(_null_task)

        for thread in self.threads:
            if thread.ident == current_thread_id:
                remain_threads.append(thread)
                continue  # can't stop the current thread

            thread.join()

        self.threads = remain_threads

    # -----------------------------------------------------------

    def start(self, num_threads=-1):
        with self.lock:
            self.__start(num_threads)

    # -----------------------------------------------------------

    def stop(self):
        self.stop_event.set()

        with self.lock:
            self.__stop()

        self.stop_event.clear()

    # -----------------------------------------------------------

    def _pause(self):
        self.stop()

        if self.stop_on_fail and self.fail_event.is_set():
            raise _StopException()

    # -----------------------------------------------------------

    def _resume(self, failed=False):
        if not (failed and self.stop_on_fail):
            self.start()

    # -----------------------------------------------------------

    def _add_task(self, task):
        with self.lock:
            self.tasks.put(task)
            if task.task_id is not None:
                self.unfinished_tasks += 1

    # -----------------------------------------------------------

    def add_task(self, priority, task_id, function, *args, **kw):
        task = _Task(priority, task_id, function, args, kw)
        self._add_task(task)

    def add_expensive_task(self, task_id, function, *args, **kw):
        task = _ExpensiveTask(task_id, function, args, kw)
        self._add_task(task)

    # -----------------------------------------------------------

    def get_finished_tasks(self, block=True):
        result = []
        is_stopped = self.stop_event.is_set
        finished_tasks = self.finished_tasks
        if is_stopped():
            self.__stop()

        if block:
            with self.lock:
                block = (self.unfinished_tasks > 0) and self.threads

        while True:
            try:
                task_result = finished_tasks.get(block=block)
                block = False

                result.append(task_result)
                finished_tasks.task_done()
            except queue.Empty:
                with self.lock:
                    if self.tasks.empty() and not self.threads:
                        self.unfinished_tasks = 0
                        return result
                break

        with self.lock:
            self.unfinished_tasks -= len(result)
            assert self.unfinished_tasks >= 0

        return result
