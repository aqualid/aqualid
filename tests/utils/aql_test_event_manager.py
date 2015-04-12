import sys
import os.path
import time
import pprint

sys.path.insert(
    0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

from aql_tests import skip, AqlTestCase, runLocalTests

from aql.utils import eventWarning, eventStatus, eventHandler, \
    disableEvents, disableDefaultHandlers, enableDefaultHandlers, \
    EVENT_STATUS, EVENT_WARNING, \
    ErrorEventHandlerAlreadyDefined, ErrorEventHandlerUnknownEvent, ErrorEventUserHandlerWrongArgs

from aql.utils.aql_event_manager import EventManager

# //===========================================================================//


class TestEventManager(AqlTestCase):

    # //-------------------------------------------------------//

    def test_event_manager(self):

        @eventWarning
        def testEvent1(settings, status):
            status.append("default-event1")

        @eventHandler('testEvent1')
        def testUserEvent1(settings, status):
            status.append("user-event1")

        @eventStatus
        def testEvent2(settings, status):
            status.append("default-event2")

        @eventHandler('testEvent2')
        def testUserEvent2(settings, status):
            status.append("user-event2")

        status = []
        testEvent1(status)
        self.assertIn("default-event1", status)
        self.assertIn("user-event1", status)

        status = []
        testEvent1(status)
        self.assertIn("default-event1", status)
        self.assertIn("user-event1", status)

        status = []
        disableDefaultHandlers()
        testEvent1(status)
        self.assertNotIn("default-event1", status)
        self.assertIn("user-event1", status)

        status = []
        enableDefaultHandlers()
        disableEvents(EVENT_WARNING)
        testEvent1(status)
        testEvent2(status)
        self.assertNotIn("default-event1", status)
        self.assertNotIn("user-event1", status)
        self.assertIn("default-event2", status)
        self.assertIn("user-event2", status)

    # //=======================================================//

    def test_event_manager_errors(self):

        em = EventManager()

        def testEvent1(settings, status):
            status.append("default-event1")

        def testUserEvent1(settings, status):
            status.append("user-event1")

        def testEvent2(settings, status):
            status.append("default-event2")

        def testUserEvent2(settings, msg, status):
            status.append("user-event2")

        em.addDefaultHandler(testEvent1, EVENT_WARNING)
        em.addDefaultHandler(testEvent2, EVENT_STATUS)
        em.addUserHandler(testUserEvent1, 'testEvent1')

        # //-------------------------------------------------------//

        self.assertRaises(ErrorEventHandlerAlreadyDefined,
                          em.addDefaultHandler, testEvent2, EVENT_WARNING)
        self.assertRaises(
            ErrorEventHandlerUnknownEvent, em.addUserHandler, testUserEvent2)
        self.assertRaises(
            ErrorEventUserHandlerWrongArgs, em.addUserHandler, testUserEvent2, 'testEvent2')

# //===========================================================================//

if __name__ == "__main__":
    runLocalTests()
