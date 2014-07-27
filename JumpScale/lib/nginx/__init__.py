from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform.nginx')
from nginx import NginxFactory
j.system.platform.nginx = NginxFactory()