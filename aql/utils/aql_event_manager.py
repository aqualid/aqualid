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


import types
import itertools

from aql.util_types import to_sequence

from .aql_utils import equal_function_args

__all__ = (
    'EVENT_WARNING', 'EVENT_STATUS', 'EVENT_DEBUG', 'EVENT_ALL',
    'event_warning',  'event_status',  'event_debug', 'event_error',
    'event_handler', 'disable_events', 'enable_events', 'EventSettings',
    'set_event_settings', 'disable_default_handlers', 'enable_default_handlers',
    'add_user_handler', 'remove_user_handler',
    'ErrorEventUserHandlerWrongArgs', 'ErrorEventHandlerAlreadyDefined',
    'ErrorEventHandlerUnknownEvent',
)

# ==============================================================================

EVENT_ERROR, \
    EVENT_WARNING, \
    EVENT_STATUS, \
    EVENT_DEBUG, \
    = EVENT_ALL = tuple(range(4))

# ==============================================================================


class ErrorEventUserHandlerWrongArgs (Exception):

    def __init__(self, event, handler):
        msg = "Invalid arguments of event '%s' handler method: '%s'" % (
            event, handler)
        super(ErrorEventUserHandlerWrongArgs, self).__init__(msg)

# ==============================================================================


class ErrorEventHandlerAlreadyDefined (Exception):

    def __init__(self, event, handler, other_handler):
        msg = "Default event '%s' handler is defined twice: '%s', '%s'" % \
              (event, handler, other_handler)
        super(ErrorEventHandlerAlreadyDefined, self).__init__(msg)

# ==============================================================================


class ErrorEventHandlerUnknownEvent (Exception):

    def __init__(self, event):
        msg = "Unknown event: '%s'" % (event,)
        super(ErrorEventHandlerUnknownEvent, self).__init__(msg)

# ==============================================================================


class EventSettings(object):
    __slots__ = (
        'brief',
        'with_output',
        'trace_exec'
    )

    def __init__(self, brief=True, with_output=True, trace_exec=False):
        self.brief = brief
        self.with_output = with_output
        self.trace_exec = trace_exec

# ==============================================================================


class EventManager(object):

    __slots__ = (
        'default_handlers',
        'user_handlers',
        'ignored_events',
        'disable_defaults',
        'settings',
    )

    # -----------------------------------------------------------

    def __init__(self):
        self.default_handlers = {}
        self.user_handlers = {}
        self.ignored_events = set()
        self.disable_defaults = False
        self.settings = EventSettings()

    # -----------------------------------------------------------

    def add_default_handler(self, handler, importance_level, event=None):
        if not event:
            event = handler.__name__

        pair = (handler, importance_level)
        other = self.default_handlers.setdefault(event, pair)
        if other != pair:
            raise ErrorEventHandlerAlreadyDefined(event, other[0], handler)

    # -----------------------------------------------------------

    def add_user_handler(self, user_handler, event=None):

        if not event:
            event = user_handler.__name__

        try:
            default_handler = self.default_handlers[event][0]
        except KeyError:
            raise ErrorEventHandlerUnknownEvent(event)

        if not equal_function_args(default_handler, user_handler):
            raise ErrorEventUserHandlerWrongArgs(event, user_handler)

        self.user_handlers.setdefault(event, []).append(user_handler)

    # -----------------------------------------------------------

    def remove_user_handler(self, user_handlers):

        for event, handlers in self.user_handlers.items():
            for user_handler in to_sequence(user_handlers):
                try:
                    handlers.remove(user_handler)
                except ValueError:
                    pass

    # -----------------------------------------------------------

    def send_event(self, event, *args, **kw):

        if event in self.ignored_events:
            return

        if self.disable_defaults:
            default_handlers = []
        else:
            default_handlers = [self.default_handlers[event][0]]

        user_handlers = self.user_handlers.get(event, [])

        args = (self.settings,) + args
        for handler in itertools.chain(user_handlers, default_handlers):
            handler(*args, **kw)

    # -----------------------------------------------------------

    def __get_events(self, event_filters):
        events = set()

        for event_filter in to_sequence(event_filters):
            if event_filter not in EVENT_ALL:
                events.add(event_filter)
            else:
                for event, pair in self.default_handlers.items():
                    handler, level = pair
                    if event_filter == level:
                        events.add(event)

        return events

    # -----------------------------------------------------------

    def enable_events(self, event_filters, enable):

        events = self.__get_events(event_filters)

        if enable:
            self.ignored_events.difference_update(events)
        else:
            self.ignored_events.update(events)

    # -----------------------------------------------------------

    def enable_default_handlers(self, enable):
        self.disable_defaults = not enable

    # -----------------------------------------------------------

    def set_settings(self, settings):
        self.settings = settings

_event_manager = EventManager()

# ==============================================================================


def _event_impl(handler, importance_level, event=None):

    if not event:
        event = handler.__name__

    _event_manager.add_default_handler(handler, importance_level)

    def _send_event(*args, **kw):
        _event_manager.send_event(event, *args, **kw)

    return _send_event

# ==============================================================================


def event_error(handler):
    return _event_impl(handler, EVENT_ERROR)


def event_warning(handler):
    return _event_impl(handler, EVENT_WARNING)


def event_status(handler):
    return _event_impl(handler, EVENT_STATUS)


def event_debug(handler):
    return _event_impl(handler, EVENT_DEBUG)

# ==============================================================================


def event_handler(event=None):

    if isinstance(event, (types.FunctionType, types.MethodType)):
        _event_manager.add_user_handler(event)
        return event

    def _event_handler_impl(handler):
        _event_manager.add_user_handler(handler, event)
        return handler

    return _event_handler_impl

# ==============================================================================


def set_event_settings(settings):
    _event_manager.set_settings(settings)

# ==============================================================================


def enable_events(event_filters):
    _event_manager.enable_events(event_filters, True)

# ==============================================================================


def disable_events(event_filters):
    _event_manager.enable_events(event_filters, False)

# ==============================================================================


def disable_default_handlers():
    _event_manager.enable_default_handlers(False)

# ==============================================================================


def enable_default_handlers():
    _event_manager.enable_default_handlers(True)

# ==============================================================================


def add_user_handler(handler, event=None):
    _event_manager.add_user_handler(handler, event)

# ==============================================================================


def remove_user_handler(handler):
    _event_manager.remove_user_handler(handler)

# ==============================================================================
