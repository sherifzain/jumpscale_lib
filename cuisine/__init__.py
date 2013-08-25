
from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')

from Cuisine import Cuisine

j.tools.cuisine = Cuisine()
