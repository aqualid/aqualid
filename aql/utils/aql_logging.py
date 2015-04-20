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


import logging

__all__ = (
    'set_log_level', 'log_critical',  'log_warning',  'log_error', 'log_debug',
    'log_info', 'add_log_handler',
    'LOG_CRITICAL', 'LOG_WARNING', 'LOG_ERROR', 'LOG_DEBUG', 'LOG_INFO',
)

LOG_CRITICAL = logging.CRITICAL
LOG_ERROR = logging.ERROR
LOG_WARNING = logging.WARNING
LOG_INFO = logging.INFO
LOG_DEBUG = logging.DEBUG

# -------------------------------------------------------------------------------


class LogFormatter(logging.Formatter):

    __slots__ = ('other',)

    def __init__(self, *args, **kw):
        logging.Formatter.__init__(self, *args, **kw)

        self.other = logging.Formatter("%(levelname)s: %(message)s")

    def formatTime(self, record, datefmt=None):
        if record.levelno == logging.INFO:
            return logging.Formatter.formatTime(self, record, datefmt=datefmt)
        else:
            return self.other.formatTime(record, datefmt=datefmt)

    def format(self, record):
        if record.levelno == logging.INFO:
            return logging.Formatter.format(self, record)
        else:
            return self.other.format(record)

# -------------------------------------------------------------------------------


def _make_aql_logger():
    logger = logging.getLogger("AQL")
    handler = logging.StreamHandler()

    formatter = LogFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger

# -------------------------------------------------------------------------------

_logger = _make_aql_logger()

set_log_level = _logger.setLevel
log_critical = _logger.critical
log_error = _logger.error
log_warning = _logger.warning
log_info = _logger.info
log_debug = _logger.debug
add_log_handler = _logger.addHandler

# -------------------------------------------------------------------------------
