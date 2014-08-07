from JumpScale import j
j.base.loader.makeAvailable(j, 'robots')

from .YoutrackRobot import YoutrackRobot
j.robots.youtrack = YoutrackRobot()

