from gevent import monkey
monkey.patch_all()

from JumpScale import j
j.application.start('httprobot')

import JumpScale.lib.mailrobot1
j.servers.mailrobot.startHTTP()
j.application.stop(0)
