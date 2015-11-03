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
class _NoLock(object):
    def acquire_shared(self):
        return self

    def acquire_exclusive(self):
        return self

    def release(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# ==============================================================================
class _SharedLock(object):
    def __init__(self):
        self.cond = threading.Condition(threading.Lock())
        self.count = 0

    # ----------------------------------------------------------

    def acquire_shared(self):
        cond = self.cond
        with cond:
            while self.count < 0:
                cond.wait()

            self.count += 1

        return self

    # ----------------------------------------------------------

    def acquire_exclusive(self):
        cond = self.cond
        with cond:
            while self.count != 0:
                cond.wait()

            self.count -= 1

        return self

    # ----------------------------------------------------------

    def release(self):
        cond = self.cond
        with cond:
            if self.count > 0:
                self.count -= 1
            elif self.count < 0:
                self.count += 1

            cond.notify_all()

    # ----------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


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

    def __call__(self, lock):
        with lock.acquire_shared():
            return self.func(*self.args, **self.kw)


# ==============================================================================
class _NullTask(_Task):

    __slots__ = (
        'task_id',
    )

    def __init__(self):
        self.task_id = None

    def __lt__(self, other):
        return True

    def __call__(self, lock):
        pass

_null_task = _NullTask()


# ==============================================================================
class _ExpensiveTask(_Task):

    def __init__(self, task_id, func, args, kw):
        super(_ExpensiveTask, self).__init__(None, task_id, func, args, kw)

    def __lt__(self, other):
        return False

    def __call__(self, lock):
        with lock.acquire_exclusive():
            return self.func(*self.args, **self.kw)


# ==============================================================================
class TaskResult (object):
    __slots__ = ('task_id', 'error', 'result')

    def __init__(self, task_id=None, result=None, error=None):
        self.task_id = task_id
        self.result = result
        self.error = error

    def is_failed(self):
        return self.error is not None

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
class _WorkerThread(threading.Thread):

    def __init__(self, tasks, finished_tasks, task_lock,
                 stop_event, fail_event, stop_on_fail, with_backtrace):

        super(_WorkerThread, self).__init__()

        self.tasks = tasks
        self.finished_tasks = finished_tasks
        self.task_lock = task_lock
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
        task_lock = self.task_lock

        while not is_stopped():

            task = tasks.get()

            task_id = task.task_id

            if task_id is not None:
                task_result = TaskResult(task_id=task_id)
            else:
                task_result = None

            try:
                result = task(task_lock)

                if task_result is not None:
                    task_result.result = result

            except BaseException as ex:
                self.fail_task(task_result, ex)

            finally:
                if task_result is not None:
                    finished_tasks.put(task_result)

                tasks.task_done()

    # ----------------------------------------------------------

    def fail_task(self, task_result, ex):

        if self.with_backtrace:
            err = traceback.format_exc()
        else:
            err = str(ex)

        if task_result is not None:
            task_result.error = err
        else:
            log_warning("Task failed with error: %s", err)

        self.fail_event.set()
        if self.stop_on_fail:
            self.stop_event.set()


# ==============================================================================
class TaskManager (object):
    __slots__ = (

        'task_lock',
        'num_threads',
        'threads',
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
        self.task_lock = _NoLock()

        self.unfinished_tasks = 0
        self.threads = []
        self.stop_on_fail = stop_on_fail
        self.stop_event = threading.Event()
        self.fail_event = threading.Event()
        self.with_backtrace = with_backtrace

        self.start(num_threads)

    # ----------------------------------------------------------

    def start(self, num_threads):
        threads = self.threads

        num_threads -= len(threads)

        args = (self.tasks, self.finished_tasks, self.task_lock,
                self.stop_event, self.fail_event,
                self.stop_on_fail, self.with_backtrace)

        for i in range(num_threads):
            thread = _WorkerThread(*args)
            threads.append(thread)

            thread.start()

    # -----------------------------------------------------------

    def stop(self):

        stop_event = self.stop_event

        if not stop_event.is_set():
            stop_event.set()

        put_task = self.tasks.put

        for thread in self.threads:
            put_task(_null_task)
            thread.join()

        self.threads.clear()
        stop_event.clear()

    # ----------------------------------------------------------

    def __add_task(self, task):
        self.tasks.put(task)
        if task.task_id is not None:
            self.unfinished_tasks += 1

    # -----------------------------------------------------------

    def add_task(self, priority, task_id, function, *args, **kw):
        task = _Task(priority, task_id, function, args, kw)
        self.__add_task(task)

    # -----------------------------------------------------------

    def __enable_expensive(self):

        num_threads = len(self.threads)

        self.stop()
        if self.stop_on_fail and self.fail_event.is_set():
            return

        self.task_lock = _SharedLock()
        self.start(num_threads)

    # ----------------------------------------------------------

    def add_expensive_task(self, task_id, function, *args, **kw):
        task = _ExpensiveTask(task_id, function, args, kw)

        if isinstance(self.task_lock, _NoLock):
            self.__enable_expensive()

        self.__add_task(task)

    # -----------------------------------------------------------

    def get_finished_tasks(self, block=True):
        result = []
        is_stopped = self.stop_event.is_set
        finished_tasks = self.finished_tasks
        if is_stopped():
            self.stop()

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
