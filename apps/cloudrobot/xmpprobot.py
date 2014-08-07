

from JumpScale import j



import JumpScale.lib.cloudrobots

import sys

args=sys.argv

from robots import *

j.servers.cloudrobot.startXMPPRobot(args[1],args[2],robots=robots)

j.application.stop(0)
