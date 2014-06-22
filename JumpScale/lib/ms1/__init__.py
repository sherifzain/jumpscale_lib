from JumpScale import j
j.base.loader.makeAvailable(j, 'tools.ms1')
from .ms1 import MS1
from .ms1factory import MS1RobotFactory
j.tools.ms1 = MS1()
j.tools.ms1robot = MS1RobotFactory()