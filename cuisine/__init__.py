
from OpenWizzy import o

o.base.loader.makeAvailable(o, 'tools')

from Cuisine import Cuisine

o.tools.cuisine=Cuisine()
