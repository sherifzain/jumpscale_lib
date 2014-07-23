from JumpScale import j
from JumpScale.grid.geventws.GeventWSServer import GeventWSServer
import JumpScale.grid.osis
import JumpScale.baselib.redisworker
import urlparse


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

        robot_processor = environ["PATH_INFO"].strip().strip("/")
        if self.robots.has_key(robot_processor):
            robot = self.robots[robot_processor]

            cl = self.osis_job
            job = cl.new()
            job.start = j.base.time.getTimeEpoch()
            job.rscript_name = rscript_name
            job.rscript_content = snippet
            job.rscript_channel = robot_processor
            job.state = "PENDING"
            job.onetime = False
            job.user = userid
            tmp, tmp, guid = cl.set(job)
            # THISIS TEMP
            job.state = "OK"
            job.result = "\n> ".join(job.rscript_content.split("\n"))
            job.log = "1:this is test log\n2:anotherline\n3:morelines\n"
            tmp, tmp, guid = cl.set(job)
            result = robot.process(snippet)

            j.clients.email.send(useremail, "%s@%s" %
                             (robot_processor, self.domain), 'subject', result)
            output = guid
        else:
            output = 'Could not match any robot. Please make sure you are sending to the right one, \'youtrack\', \'user\' & \'machine\' are supported.\n'

        start_response('200 OK', [('Content-Type', 'text/html')])

        return [output]
