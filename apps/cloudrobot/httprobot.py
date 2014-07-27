from gevent import monkey
monkey.patch_all()

from robots import *

from JumpScale import j
j.application.start('httprobot')

import JumpScale.lib.cloudrobots
j.servers.cloudrobot.startHTTP(robots=robots)

j.application.stop(0)
