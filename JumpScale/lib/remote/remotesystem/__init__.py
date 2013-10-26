
from JumpScale import j

j.base.loader.makeAvailable(j, 'remote')

from RemoteSystem import RemoteSystem

j.remote.system = RemoteSystem()
