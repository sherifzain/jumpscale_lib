
# from robots import *

from JumpScale import j
j.application.start('jailtest')

# import JumpScale.lib.cloudrobots

import JumpScale.lib.jail

#make everything ready for the jail
# j.tools.jail.prepareJSJail()

j.tools.jail.killAllSessions()

j.tools.jail.createJSJail("kds","1234")

j.application.stop(0)
