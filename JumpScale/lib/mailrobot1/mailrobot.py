from JumpScale import j
import JumpScale.grid.agentcontroller
import JumpScale.baselib.mailclient
import email
import gevent
from gsmtpd import SMTPServer

# for html parsing
from htmllib import HTMLParser
from formatter import AbstractFormatter, DumbWriter
from cStringIO import StringIO

class MailRobot(SMTPServer):

    def __init__(self, *args, **kwargs):
        self.emailparser = email.Parser.Parser()
        self.acl = j.clients.agentcontroller.get()
        self.templatefolder = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'mailrobot', 'templates')
        SMTPServer.__init__(self, *args, **kwargs)

    def _html2text(self, html):
        output = StringIO()
        writer = DumbWriter(output)
        p = HTMLParser(AbstractFormatter(writer))
        p.feed(html)
        return output.getvalue()
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        gevent.spawn(self.green_message, peer, mailfrom, rcpttos, data)

    def green_message(self, peer, mailfrom, rcpttos, data):
        mailserver = j.application.config.get('mailrobot.mailserver')
        msg = self.emailparser.parsestr(data)
        if mailserver not in msg['To'].split('@')[1]:
            print 'Received a message which is not going to be processed. Mail server does not match'
            return
        mailfrom = msg['From']
        try:
            if msg.is_multipart():
                msg_parts = msg.get_payload()
                ct2msg = dict([(msg_part.get_content_type(), msg_part) for msg_part in msg_parts])
                if 'text/plain' in ct2msg:
                    commands_str = ct2msg['text/plain'].get_payload()
                else:
                    for ct, msg_part in ct2msg.iteritems():
                        if 'text' in ct:
                            commands_str = self._html2text(msg_part.get_payload())
                            break
            else:
                commands_str = msg.get_payload()

            print "Processing message from %s"  % msg['From']
            output = ''
            robot_processor = msg['To'].split('@')[0]
            if 'youtrack' in robot_processor:
                import JumpScale.lib.youtrackclient
                robot = j.tools.youtrack.getRobot("http://incubaid.myjetbrains.com/youtrack/")
                output = robot.process(commands_str)
            elif 'machine' in robot_processor:
                import JumpScale.lib.ms1
                robot = j.tools.ms1robot.getRobot()
                output = robot.process(commands_str)
            
            output = output or 'Could not match any robot. Please make sure you are sending to the right one.'
            j.clients.email.send([mailfrom], 'mailrobot@mothership1.com', msg.get('subject'), output)
        except:
            j.clients.email.send([mailfrom], 'mailrobot@mothership1.com', msg.get('subject'), 'A generic error has occured. Please try again later')

class MailRobotFactory(object):
    def start(self):
        robot = MailRobot(('0.0.0.0', 25))
        robot.serve_forever()
