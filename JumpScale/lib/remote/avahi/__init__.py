
from JumpScale import j

j.base.loader.makeAvailable(j, 'remote')

from Avahi import Avahi

j.remote.avahi = Avahi()
