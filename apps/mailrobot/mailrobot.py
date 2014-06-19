from gevent import monkey
monkey.patch_all()

from JumpScale import j

j.application.start('mailrobot')

import JumpScale.lib.mailrobot1
import logging
logger = logging.getLogger('gsmtpd')
logger.setLevel(logging.ERROR)

j.servers.mailrobot.start()

j.application.stop(0)
