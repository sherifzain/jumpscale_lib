from JumpScale import j
j.base.loader.makeAvailable(j, 'servers')
from .mailrobot import MailRobotFactory
j.servers.mailrobot = MailRobotFactory()
