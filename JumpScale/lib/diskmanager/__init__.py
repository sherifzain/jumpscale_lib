from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform.diskmanager')
from Diskmanager import Diskmanager
j.system.platform.diskmanager = Diskmanager()

