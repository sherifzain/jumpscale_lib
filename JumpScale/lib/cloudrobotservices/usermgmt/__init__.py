from JumpScale import j
j.base.loader.makeAvailable(j, 'robots')

from .UserMgmtRobot import UserMgmtRobot
j.robots.usermgmt = UserMgmtRobot()

