#
# Copyright (c) 2011,2012 The developers of Aqualid project
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__all__ = (
  'setLogLevel', 'logCritical',  'logWarning',  'logError',  'logDebug',  'logInfo', 'addLogHandler',
                 'LOG_CRITICAL', 'LOG_WARNING', 'LOG_ERROR', 'LOG_DEBUG', 'LOG_INFO',
)

import logging

LOG_CRITICAL = logging.CRITICAL
LOG_ERROR = logging.ERROR
LOG_WARNING = logging.WARNING
LOG_INFO = logging.INFO
LOG_DEBUG = logging.DEBUG

#//---------------------------------------------------------------------------//

class LogFormatter( object ):
  
  __slots__ = ('info', 'other')
  
  def   __init__(self):
    self.info = logging.Formatter()
    self.other = logging.Formatter("%(levelname)s: %(message)s")
  
  def formatTime(self, record, datefmt=None):
    if record.levelno == logging.INFO:
      return self.info.formatTime( record, datefmt = datefmt)
    else:
      return self.other.formatTime( record, datefmt = datefmt)
  
  def format(self, record ):
    if record.levelno == logging.INFO:
      return self.info.format( record )
    else:
      return self.other.format( record )
    
  def formatException(self, ei):
    return self.other.formatException( ei )
  
  def usesTime(self):
    return self.other.usesTime()
  
#//---------------------------------------------------------------------------//

def   _makeAqlLogger():
  logger = logging.getLogger( "AQL" )
  handler = logging.StreamHandler()
  
  formatter = LogFormatter()
  handler.setFormatter(formatter)
  
  logger.addHandler( handler )
  logger.setLevel( logging.DEBUG )
  
  return logger

#//---------------------------------------------------------------------------//

_logger = _makeAqlLogger()

setLogLevel   = _logger.setLevel
logCritical   = _logger.critical
logError      = _logger.error
logWarning    = _logger.warning
logInfo       = _logger.info
logDebug      = _logger.debug
addLogHandler = _logger.addHandler

#//---------------------------------------------------------------------------//
