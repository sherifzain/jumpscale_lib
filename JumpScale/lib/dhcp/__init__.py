from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform.dhcp')
from dhcp import DhcpFactory
j.system.platform.dhcp = DhcpFactory()