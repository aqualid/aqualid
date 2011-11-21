
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
