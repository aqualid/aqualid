#
# Copyright (c) 2011,2012 The developers of Aqualid project - http://aqualid.googlecode.com
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

__all__ = ( 'LOG_CRITICAL', 'LOG_FATAL', 'LOG_ERROR', 'LOG_WARNING', 'LOG_INFO', 'LOG_DEBUG')

import logging


_logger = None

LOG_CRITICAL = logging.CRITICAL
LOG_FATAL = CRITICAL
LOG_ERROR = logging.ERROR
LOG_WARNING = logging.WARNING
LOG_INFO = logging.INFO
LOG_DEBUG = logging.DEBUG

#//---------------------------------------------------------------------------//

class Logger( logging.Logger ):
  def   __new__( cls ):
    self = logging.getLogger( "AQL" )
    handler = logging.StreamHandler()
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    
    self.addHandler( handler )
    self.setLevel( logging.DEBUG )
    
    return self

_logger = Logger()

#//---------------------------------------------------------------------------//

def   setLogLevel( level = logging.NOTSET, logger = _logger ):
  _logger.setLevel( level )

def     logCritical(msg, *args, **kwargs):
  _logger.critical( msg, *args, **kwargs )

logFatal = logCritical

#//---------------------------------------------------------------------------//

def     logError(msg, *args, **kwargs):
    global _logger
    _logger.error( msg, *args, **kwargs )

#//---------------------------------------------------------------------------//

def     logWarning(msg, *args, **kwargs):
    global _logger
    _logger.warning( msg, *args, **kwargs )

logWarn = logWarning

#//---------------------------------------------------------------------------//

def     logInfo(msg, *args, **kwargs):
    global _logger
    _logger.info( msg, *args, **kwargs )

#//---------------------------------------------------------------------------//

def     logDebug(msg, *args, **kwargs):
    global _logger
    _logger.debug( msg, *args, **kwargs )

#//---------------------------------------------------------------------------//

