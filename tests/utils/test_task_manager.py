import time
import threading

from aql_testcase import AqlTestCase

from aql.utils import TaskManager, TaskResult


# ==============================================================================
def _do_append(arg, results, delay=0):
    time.sleep(delay)
    results.add(arg)


# ==============================================================================
def _do_fail(delay=0, fail_event=None):
    if fail_event is not None:
        fail_event.set()
    time.sleep(delay)
    raise Exception("Expected fail")


# ==============================================================================
def _do_expensive(event, delay=0.5):
    if event.wait(delay):
        raise Exception("Concurrent run")
    event.set()
    time.sleep(delay)   # doing a heavy work
    event.clear()


# ==============================================================================
def _do_non_expensive(event, delay=2):
    if event.wait(delay):
        raise Exception("Concurrent run")
    time.sleep(delay)


# ==============================================================================
class TestTaskManager(AqlTestCase):

    @staticmethod
    def get_done_tasks(tm):
        results = []

        while True:
            tmp_results = tm.get_finished_tasks()
            if not tmp_results:
                break
            results.extend(tmp_results)

        return results

    # ----------------------------------------------------------

    def test_task_manager(self):

        jobs = 1
        tm = TaskManager()

        results = set()

        num_of_tasks = 8

        for i in range(num_of_tasks):
            tm.add_task(num_of_tasks - i, i, _do_append, i, results)

        tm.start(jobs)

        done_tasks = [result.task_id for result in self.get_done_tasks(tm)]
        expected_tasks = sorted(range(num_of_tasks), reverse=True)

        self.assertEqual(done_tasks, expected_tasks)
        self.assertEqual(results, set(range(num_of_tasks)))

    # ----------------------------------------------------------

    def test_task_manager_fail(self):

        jobs = 4

        tm = TaskManager()
        tm.start(jobs)

        num_of_tasks = 100

        for i in range(num_of_tasks):
            tm.add_task(0, i, _do_fail, 0.0)

        tm.start(jobs)

        done_tasks = self.get_done_tasks(tm)

        self.assertEqual(len(done_tasks), num_of_tasks)

        for i, t in enumerate(sorted(done_tasks)):
            self.assertEqual(t.task_id, i)
            self.assertIsNotNone(t.error)

    # ----------------------------------------------------------

    def test_task_manager_stop(self):

        jobs = 4
        num_tasks = 8

        tm = TaskManager()
        tm.start(jobs)

        tm.stop()
        tm.start(jobs)

        results = set()

        for i in range(num_tasks):
            tm.add_task(0, i, _do_append, i, results, 0.2 * (i + 1))

        time.sleep(0.1)

        tm.stop()
        tm.stop()

        done_tasks = sorted(result.task_id
                            for result in self.get_done_tasks(tm))

        self.assertEqual(len(done_tasks), jobs)
        self.assertEqual(results, set(done_tasks))

        tm.start(jobs)
        done_tasks = sorted(result.task_id
                            for result in self.get_done_tasks(tm))

        self.assertEqual(len(done_tasks), max(0, num_tasks - jobs))
        tm.stop()

        tm.start(jobs)

        for i in range(jobs):
            tm.add_task(0, i, _do_append, i, results, 0.2 * i)

        self.get_done_tasks(tm)

        tm.stop()

    # ----------------------------------------------------------

    def test_task_manager_one_fail(self):
        tm = TaskManager()
        tm.start(4)

        results = set()

        num_tasks = 3

        tm.add_task(0, 0, _do_append, 0, results, 0.3)

        tm.add_task(0, 1, _do_fail, 0.1)

        tm.add_task(0, 2, _do_append, 2, results, 0)

        done_tasks = sorted(self.get_done_tasks(tm), key=lambda v: v.task_id)
        self.assertEqual(len(done_tasks), num_tasks)

        items = zip(range(num_tasks), [None] * num_tasks, [None] * num_tasks)

        expected_tasks = [TaskResult(task_id, error, result)
                          for task_id, error, result in items]

        self.assertEqual(done_tasks[0], expected_tasks[0])

        self.assertEqual(done_tasks[1].task_id, 1)
        self.assertIsNotNone(done_tasks[1].error)

        self.assertEqual(done_tasks[2], expected_tasks[2])

    # ----------------------------------------------------------

    def test_task_manager_abort_on_fail(self):
        num_tasks = 8
        jobs = 4

        tm = TaskManager()
        tm.disable_keep_going()

        results = set()

        for i in range(jobs - 1):
            tm.add_task(0, i, _do_append, i, results, 0.5)

        tm.add_task(1, jobs - 1, _do_fail, 0.1)

        for i in range(jobs, num_tasks):
            tm.add_task(2, i, _do_append, i, results, 0)

        tm.start(jobs)

        done_tasks = sorted(self.get_done_tasks(tm), key=lambda t: t.task_id)
        self.assertEqual(len(done_tasks), jobs)

        items = zip(range(jobs), [None] * num_tasks, [None] * num_tasks)
        expected_tasks = [TaskResult(task_id, error, result)
                          for task_id, error, result in items]

        self.assertEqual(done_tasks[:3], expected_tasks[:3])

        self.assertEqual(done_tasks[3].task_id, 3)
        self.assertIsNotNone(done_tasks[3].error)

    # ----------------------------------------------------------

    def test_tm_expensive_success(self):

        expensive_event = threading.Event()

        num_tasks = 8
        jobs = 16

        tm = TaskManager()
        tm.disable_keep_going()

        for i in range(num_tasks):
            tm.add_task(0, i, _do_non_expensive, expensive_event)

        tm.start(jobs)
        time.sleep(0.25)

        expensive_task_ids = set()

        for i in range(num_tasks, num_tasks * 2):
            if i % 2:
                expensive_task_ids.add(i)
                tm.add_expensive_task(i, _do_expensive, expensive_event)
            else:
                tm.add_task(0, i, _do_non_expensive, expensive_event)

        results = self.get_done_tasks(tm)

        for result in results:
            self.assertFalse(result.is_failed(), str(result))

        self.assertEqual(len(results), num_tasks * 2)

        task_ids = [result.task_id for result in results]

        finished_expensive_tasks = set(task_ids[-len(expensive_task_ids):])

        self.assertEqual(finished_expensive_tasks, expensive_task_ids)

    # ----------------------------------------------------------

    def test_tm_expensive_keep_going(self):

        expensive_event = threading.Event()

        num_tasks = 8
        jobs = 16

        tm = TaskManager()
        tm.disable_backtrace()

        for i in range(num_tasks):
            tm.add_task(0, i, _do_non_expensive, expensive_event)

        tm.add_task(0, num_tasks, _do_fail, 1)

        tm.start(jobs)
        time.sleep(0.25)

        tm.add_expensive_task(num_tasks + 1, _do_expensive, expensive_event)

        results = self.get_done_tasks(tm)

        self.assertEqual(len(results), num_tasks + 2)

    # ----------------------------------------------------------

    def test_tm_expensive_stop(self):

        expensive_event = threading.Event()
        fail_event = threading.Event()

        num_tasks = 4
        jobs = 16

        tm = TaskManager()
        tm.disable_keep_going()

        for i in range(num_tasks):
            tm.add_task(0, i, _do_non_expensive, expensive_event)

        tm.add_task(0, num_tasks, _do_fail, 1, fail_event)

        tm.start(jobs)

        fail_event.wait()

        tm.add_expensive_task(num_tasks + 1, _do_expensive, expensive_event)

        results = self.get_done_tasks(tm)

        self.assertEqual(len(results), num_tasks + 1)
        task_ids = sorted(result.task_id for result in results)
        self.assertEqual(task_ids, list(range(num_tasks + 1)))
