
# from robots import *

from JumpScale import j
j.application.start('jailtest')

# import JumpScale.lib.cloudrobots

import JumpScale.lib.jail

#make everything ready for the jail
# j.tools.jail.prepareJSJail()

user="kds"
session="asession"

j.tools.jail.createJSJail(user,"1234")
j.tools.jail.createJSJailSession(user,session,"js")

# j.tools.jail.killAllSessions()



j.application.stop(0)
