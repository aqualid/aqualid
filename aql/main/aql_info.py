__all__ = (
  'getAqlInfo',
  'dumpAqlInfo',
)

#//===========================================================================//

class AqlInfo (object):
  __slots__ = (
    'name',
    'module',
    'description',
    'version',
    'date',
    'url',
    'license',
  )

  #//-------------------------------------------------------//

  def   __init__(self):
    self.name         = "Aqualid"
    self.module       = "aqualid"
    self.description  = "General purpose build tool."
    self.version      = 0.5
    self.date         = None
    self.url          = 'https://github.com/aqualid'
    self.license      = "MIT License"

  #//-------------------------------------------------------//

  def dump(self):
    result = "{name} {version}".format( name = self.name, version = self.version )
    if self.date:
      result += ' ({date})'.format( date = self.date )

    result += "\n"
    result += self.description
    result += "\nSite: %s" % self.url

    return result

#//-------------------------------------------------------//

_AQL_VERSION_INFO = AqlInfo()

#//===========================================================================//

def   getAqlInfo():
  return _AQL_VERSION_INFO

#//===========================================================================//

def   dumpAqlInfo():
  return _AQL_VERSION_INFO.dump()

