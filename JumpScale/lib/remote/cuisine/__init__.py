
from JumpScale import j

j.base.loader.makeAvailable(j, 'remote')

from Cuisine import Cuisine

j.remote.cuisine = Cuisine()
