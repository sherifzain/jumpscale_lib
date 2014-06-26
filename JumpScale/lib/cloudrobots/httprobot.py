from JumpScale import j
from JumpScale.grid.geventws.GeventWSServer import GeventWSServer


class HTTPRobot(GeventWSServer):
    def __init__(self, addr, port):
        GeventWSServer.__init__(self, addr, port)

    def rpcRequest(self, environ, start_response):
        data=environ["wsgi.input"].read()
        import JumpScale.lib.ms1
        robot = j.tools.ms1robot.getRobot()
        try:
            output = robot.process(data)
        except:
            output = 'A generic error has occured. Please try again later'
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [output]

