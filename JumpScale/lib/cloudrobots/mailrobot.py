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
from .httprobot import HTTPRobot
import JumpScale.lib.html

import JumpScale.baselib.redisworker

class MailRobot(SMTPServer):

    def __init__(self, *args, **kwargs):
        self.emailparser = email.Parser.Parser()
        self.acl = j.clients.agentcontroller.get()
        self.templatefolder = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'mailrobot', 'templates')
        SMTPServer.__init__(self, *args, **kwargs)
        self.domain=j.application.config.get("mailrobot.mailserver")
        self.robots={}    
        self.mailserver = j.application.config.get('mailrobot.mailserver')   

    def _html2text(self, html):
        from IPython import embed
        print "DEBUG NOW id"
        embed()
        p
        
        output = StringIO()
        writer = DumbWriter(output)
        p = HTMLParser(AbstractFormatter(writer))
        p.feed(html)
        return output.getvalue()
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        gevent.spawn(self.green_message, peer, mailfrom, rcpttos, data)

    def toFileRobot(self,robot,fromm,subject,msg):
        from IPython import embed
        print "DEBUG NOW ooo"
        embed()
        
        out=""
        state="start"
        var=""
        for line in msg.split("\n"):
            if state=="start" and (line.find("=")<>-1 or line.find("@")==0 or line.find("!")==0 or line.find("#")==0):
                out+="%s\n"%line
                state="in"
                continue

            if state=="in" and (line.find("<")==0 or line.find(">")==0 or line.find("--")==0):
                break

            if state=="in":
                out+="%s\n"%line

        robotdir=j.system.fs.joinPaths(j.dirs.varDir, 'var', 'cloudrobot', 'templates',robot)
        if not j.system.fs.exists(path=robotdir):
            output = 'Could not find robot on fs. Please make sure you are sending to the right one, \'youtrack\' & \'machine\' & \'user\' are supported.'
            j.clients.email.send([mailfrom], "%s@%"%(robot,self.domain), subject, output)
            return

        subject2=j.tools.text.toAscii(subject,80)
        fromm2=j.tools.text.toAscii(fromm)
        j.system.fs.joinPaths(j.dirs.varDir, 'var', 'cloudrobot', robot,'in',"%s_%s.py"%(fromm2subject2))

        from IPython import embed
        print "DEBUG NOW ooo"
        embed()
        




    def green_message(self, peer, mailfrom, rcpttos, data):
        
        msg = self.emailparser.parsestr(data)
        if self.mailserver not in msg['To'].split('@')[1]:
            print 'Received a message which is not going to be processed. Mail server does not match'
            return
        mailfrom = msg['From']
        try:
            if msg.is_multipart():
                msg_parts = msg.get_payload()
                commands_str=""
                for msg_part in msg_parts:
                    if 'text/plain' in msg_part.get_content_type():
                        commands_str+=msg_part.get_payload()
                        commands_str+="\n"
                        from IPython import embed
                        print "DEBUG NOW uuu"
                        embed()
                        
                    elif 'text/html' in msg_part.get_content_type():
                        txt=msg_part.get_payload()
                        if txt.find('"gmail_extra"')<>-1:
                            continue
                        else:
                            output="please only send txt commands to robot, we got html."
                            j.clients.email.send([mailfrom], "%s@%"%(robot_processor,self.domain), msg.get('subject'), output)                        
                    else:                    
                        from IPython import embed
                        print "DEBUG NOW othercontent type"
                        embed()
                        p
                    
                # ct2msg = dict([(msg_part.get_content_type(), msg_part) for msg_part in msg_parts])
                # if 'text/plain' in ct2msg:
                #     commands_str = ct2msg['text/plain'].get_payload()
                # else:
                #     for ct, msg_part in ct2msg.iteritems():
                #         if 'text' in ct:
                #             commands_str = self._html2text(msg_part.get_payload())
                #             break
            else:
                commands_str = msg.get_payload()            

            print "Processing message from %s"  % msg['From']
            output = ''
            robot_processor = msg['To'].split('@')[0]
            if not self.robots.has_key(robot_processor):
                output = 'Could not match any robot. Please make sure you are sending to the right one, \'youtrack\' & \'machine\' are supported.'            
                j.clients.email.send([mailfrom], "%s@%"%(robot_processor,self.domain), msg.get('subject'), output)
            else:
                commands_str="@mail_subject=%s\n@mail_from=%s\n%s"%(mailfrom,msg.get('subject'),commands_str)
                self.toFileRobot(robot_processor,mailfrom,msg.get('subject'),commands_str)

        except Exception,e:
            print j.errorconditionhandler.parsePythonErrorObject(e)            
            j.clients.email.send([mailfrom], "%s@%"%(robot_processor,self.domain), msg.get('subject'), 'A generic error has occured on server.')

