from JumpScale import j
from JumpScale.grid.geventws.GeventWSServer import GeventWSServer
import JumpScale.grid.osis
import JumpScale.baselib.redisworker
import urlparse
import JumpScale.lib.cloudrobots


class HTTPRobot(GeventWSServer):
    def __init__(self, addr, port):
        GeventWSServer.__init__(self, addr, port)
        self.domain = j.application.config.get("mailrobot.mailserver")
        self.robots = {}
        self.osis = j.core.osis.getClient(user='root')
        self.osis_job = j.core.osis.getClientForCategory(self.osis, 'robot', 'job')

    def rpcRequest(self, environ, start_response):
        commands_str = environ["wsgi.input"].read()
        snippet = environ['QUERY_STRING']

        params = urlparse.parse_qs(commands_str)
        snippet = params['snippet'][0]
        userid = params['userid'][0]
        useremail = params['useremail'][0]
        rscript_name = params['rscript_name'][0]

        args={}

        robot_processor = environ["PATH_INFO"].strip().strip("/")
        if self.robots.has_key(robot_processor):
            jobguid=j.servers.cloudrobot.toFileRobot(robot_processor,snippet,useremail,rscript_name,args)
            output = jobguid
        else:
            output = 'Could not match any robot. Please make sure you are sending to the right one, \'youtrack\', \'user\' & \'machine\' are supported.\n'

        start_response('200 OK', [('Content-Type', 'text/html')])

        return [output]
