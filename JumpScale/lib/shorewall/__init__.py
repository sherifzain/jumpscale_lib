from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform.shorewall')
from shorewall import ShorewallFactory
j.system.platform.shorewall = ShorewallFactory()