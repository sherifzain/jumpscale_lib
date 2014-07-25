from gevent import monkey
monkey.patch_all()

from robots import *

from JumpScale import j
j.application.start('filerobot')

import JumpScale.lib.cloudrobots
j.servers.cloudrobot.startFileRobot(robots=robots)

j.application.stop(0)
