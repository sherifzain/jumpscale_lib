from JumpScale import j

from .httprobot import HTTPRobot
from .mailrobot import MailRobot



class CloudRobotFactory(object):
    def startMailServer(self,robots={}):
        robot = MailRobot(('0.0.0.0', 25))
        robot.robots=robots
        print "start server on port:25"
        robot.serve_forever()

    def startHTTP(self, addr='0.0.0.0', port=8099,robots={}):
        robot=HTTPRobot(addr=addr, port=port)
        robot.robots=robots
        robot.start()
