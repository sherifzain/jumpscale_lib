from gevent import monkey
monkey.patch_all()

from JumpScale import j
j.application.start('filerobot')

import JumpScale.lib.cloudrobots

from robots import *

j.servers.cloudrobot.startFileRobot(robots=robots)

j.application.stop(0)
