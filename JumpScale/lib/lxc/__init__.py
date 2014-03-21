from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform.lxc')
from Lxc import Lxc
j.system.platform.lxc = Lxc()

