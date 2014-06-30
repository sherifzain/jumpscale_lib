from JumpScale import j
from JumpScale.grid.geventws.GeventWSServer import GeventWSServer
import JumpScale.baselib.redisworker


class HTTPRobot(GeventWSServer):
    def __init__(self, addr, port):
        GeventWSServer.__init__(self, addr, port)
        self.robots={}

    def rpcRequest(self, environ, start_response):
        commands_str=environ["wsgi.input"].read()

        robot_processor=environ["PATH_INFO"].strip().strip("/")

        if self.robots.has_key(robot_processor):
            robot=self.robots[robot_processor]
            output = robot.process(commands_str)
        else:
            output = 'Could not match any robot. Please make sure you are sending to the right one, \'youtrack\' & \'machine\' are supported.\n'

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [output]

