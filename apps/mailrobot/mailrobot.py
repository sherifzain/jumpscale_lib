from JumpScale import j

j.application.start('mailrobot')

import JumpScale.lib.mailrobot1

j.servers.mailrobot.start()

j.application.stop(0)
