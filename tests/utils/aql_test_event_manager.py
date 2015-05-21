import sys
import os.path

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_testcase import AqlTestCase
from tests_utils import run_local_tests

from aql.utils import event_warning, event_status, event_handler, \
    disable_events, disable_default_handlers, enable_default_handlers, \
    EVENT_STATUS, EVENT_WARNING, \
    ErrorEventHandlerAlreadyDefined, ErrorEventHandlerUnknownEvent,\
    ErrorEventUserHandlerWrongArgs

from aql.utils.aql_event_manager import EventManager

# ==============================================================================


class TestEventManager(AqlTestCase):

    # -----------------------------------------------------------

    def test_event_manager(self):

        @event_warning
        def test_event1(settings, status):
            status.append("default-event1")

        @event_handler('test_event1')
        def test_user_event1(settings, status):
            status.append("user-event1")

        @event_status
        def test_event2(settings, status):
            status.append("default-event2")

        @event_handler('test_event2')
        def test_user_event2(settings, status):
            status.append("user-event2")

        status = []
        test_event1(status)
        self.assertIn("default-event1", status)
        self.assertIn("user-event1", status)

        status = []
        test_event1(status)
        self.assertIn("default-event1", status)
        self.assertIn("user-event1", status)

        status = []
        disable_default_handlers()
        test_event1(status)
        self.assertNotIn("default-event1", status)
        self.assertIn("user-event1", status)

        status = []
        enable_default_handlers()
        disable_events(EVENT_WARNING)
        test_event1(status)
        test_event2(status)
        self.assertNotIn("default-event1", status)
        self.assertNotIn("user-event1", status)
        self.assertIn("default-event2", status)
        self.assertIn("user-event2", status)

    # ==========================================================

    def test_event_manager_errors(self):

        em = EventManager()

        def test_event1(settings, status):
            status.append("default-event1")

        def test_user_event1(settings, status):
            status.append("user-event1")

        def test_event2(settings, status):
            status.append("default-event2")

        def test_user_event2(settings, msg, status):
            status.append("user-event2")

        em.add_default_handler(test_event1, EVENT_WARNING)
        em.add_default_handler(test_event2, EVENT_STATUS)
        em.add_user_handler(test_user_event1, 'test_event1')

        # -----------------------------------------------------------

        self.assertRaises(ErrorEventHandlerAlreadyDefined,
                          em.add_default_handler,
                          test_event2,
                          EVENT_WARNING)

        self.assertRaises(ErrorEventHandlerUnknownEvent,
                          em.add_user_handler,
                          test_user_event2)

        self.assertRaises(ErrorEventUserHandlerWrongArgs,
                          em.add_user_handler,
                          test_user_event2,
                          'test_event2')

# ==============================================================================

if __name__ == "__main__":
    run_local_tests()
