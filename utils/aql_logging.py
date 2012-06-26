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


import logging


_logger = None

CRITICAL = logging.CRITICAL
FATAL = CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG


#//---------------------------------------------------------------------------//

def   _init():
    logger = logging.getLogger( "AQL" )
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel( logging.DEBUG )
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    
    logger.addHandler( handler )
    
    global _logger
    _logger = logger

#//---------------------------------------------------------------------------//

def     logLevel( level = None ):
    global _logger
    _logger.setLevel( level )

#//---------------------------------------------------------------------------//

def     logCritical(msg, *args, **kwargs):
    global _logger
    _logger.error( msg, *args, **kwargs )

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

_init()
