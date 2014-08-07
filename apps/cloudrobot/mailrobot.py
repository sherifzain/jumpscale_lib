from gevent import monkey
monkey.patch_all()

from JumpScale import j


j.application.start('mailrobot')

import JumpScale.lib.cloudrobots

import logging
logger = logging.getLogger('gsmtpd')
logger.setLevel(logging.ERROR)

from robots import *

j.servers.cloudrobot.startMailServer(robots=robots)

j.application.stop(0)
