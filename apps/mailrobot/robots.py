
from JumpScale import j

import JumpScale.lib.youtrackclient
import JumpScale.lib.ms1


robots={}
robots["youtrack"]= j.tools.youtrack.getRobot(j.application.config.get("youtrackrobot.url"))
robots["machine"]= j.tools.ms1robot.getRobot()

