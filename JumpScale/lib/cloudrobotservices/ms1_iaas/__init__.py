from JumpScale import j
j.base.loader.makeAvailable(j, 'robots')

from .MS1IaasRobot import MS1IaasRobot
j.robots.ms1_iaas = MS1IaasRobot()

