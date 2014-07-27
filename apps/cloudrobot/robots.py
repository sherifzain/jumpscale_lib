
from JumpScale import j


import JumpScale.lib.ms1
import JumpScale.lib.youtrackclient
import JumpScale.lib.usermgmt
import JumpScale.baselib.mailclient

robots={}
if j.application.config.exists("youtrackrobot.url"):
    robots["youtrack"]= j.tools.youtrack.getRobot(j.application.config.get("youtrackrobot.url"))
robots["machine"]= j.tools.ms1robot.getRobot()
robots["user"]= j.tools.usermgmt.getRobot()

