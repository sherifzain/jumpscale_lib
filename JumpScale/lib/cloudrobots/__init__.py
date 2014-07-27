from JumpScale import j
j.base.loader.makeAvailable(j, 'servers')

from .CloudRobotFactory import CloudRobotFactory

j.servers.cloudrobot = CloudRobotFactory()
