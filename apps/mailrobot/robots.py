
from JumpScale import j

import JumpScale.lib.youtrackclient
import JumpScale.lib.ms1


robots={}
robots["youtrack"]= j.tools.youtrack.getRobot("http://incubaid.myjetbrains.com/youtrack/")
robots["machine"]= j.tools.ms1robot.getRobot()

