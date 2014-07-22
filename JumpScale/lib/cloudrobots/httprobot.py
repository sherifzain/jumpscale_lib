from JumpScale import j
from JumpScale.grid.geventws.GeventWSServer import GeventWSServer
import JumpScale.baselib.redisworker
import urlparse


class HTTPRobot(GeventWSServer):
    def __init__(self, addr, port):
        GeventWSServer.__init__(self, addr, port)
        self.domain=j.application.config.get("mailrobot.mailserver")
        self.robots={}

    def rpcRequest(self, environ, start_response):
        commands_str=environ["wsgi.input"].read()
        snippet = environ['QUERY_STRING']

        params = urlparse.parse_qs(commands_str)
        snippet = params['snippet']
        useremail = params['useremail']


        robot_processor=environ["PATH_INFO"].strip().strip("/")

        if self.robots.has_key(robot_processor):
            robot=self.robots[robot_processor]
            output = robot.process(snippet)
        else:
            output = 'Could not match any robot. Please make sure you are sending to the right one, \'youtrack\', \'user\' & \'machine\' are supported.\n'

        start_response('200 OK', [('Content-Type', 'text/html')])

        j.clients.email.send(useremail, "%s@%s"%(robot_processor, self.domain), 'subject', output)


        #create job
        return [output]

