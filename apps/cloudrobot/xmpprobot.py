

from JumpScale import j

from robots import *


import JumpScale.lib.cloudrobots

import sys

args=sys.argv

j.servers.cloudrobot.startXMPPRobot(args[1],args[2],robots=robots)

j.application.stop(0)
