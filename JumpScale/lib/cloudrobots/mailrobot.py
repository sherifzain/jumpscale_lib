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
        self.archivefolder="%s/mailarchive/in"%j.dirs.varDir
        j.system.fs.createDir(self.archivefolder)

    def _html2text(self, html):
        path=self.archivefolder
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

    def processReply(self,msg):

        return j.tools.text.prefix_remove_withtrailing(":*: ",msg,onlyPrefix=True)

        # cmdfound=False
        # reply=False
        # out=""
        # for line in msg.split("\n"):
        #     if line.find("@mail_subject")==0 or line.find("@mail_from")==0:
        #         out+="%s\n"%line
        #     if line.find("!")==0:
        #         cmdfound=True
        #     if cmdfound:
        #         if line.find("<user@robot.vscalers.com>")<>-1:
        #             break
        #         out+="%s\n"%line
        #     if reply:
        #         #start processing reply
        #         if line.find("> ")==0:
        #             line=line[2:]
        #             out+="%s\n"%line
        #         # if line.strip()=="":
        #         else:
        #             break

        #     if cmdfound==False and line.find("<user@robot.vscalers.com>")<>-1:
        #         reply=True

        # return out


    def toFileRobot(self,robot,fromm,subject,msg,html,addcommands=""):
        
        msg=msg.replace("=3D","=")
        msg=msg.replace("=20","")
        # msg=msg.replace("=\r\n","")


        def findNonReply(msg):
            out=""
            state="start"
            var=""
            for line in msg.split("\n"):
                if state=="start" and (line.find("=")<>-1 or line.find("@")==0 or line.find("!")==0 or line.find("#")==0):
                    out+="%s\n"%line
                    state="in"
                    continue

                if state=="start" and (line.find("> wrote:")<>-1 or \
                    line.find("> ")==0 or line.find("--")==0 or line.find("***")==0):
                    break

                if state=="in" and (line.find("> wrote:")<>-1 or line.find("<")==0 or \
                    line.find(">")==0 or line.find("--")==0 or line.find("***")==0):
                    break

                if state=="in":
                    out+="%s\n"%line

            if len(out)>1 and out[-1]<>"\n":
                out+="\n"

            return out
        # or msg.find("<user@robot.vscalers.com> wrote:")<>-1
        
        out=""

        if msg.find(":*: ")<>-1:
            #means is a reply we need to process it
            out=self.processReply(msg)

        if out=="":
            out=findNonReply(msg)

        if out.strip()=="":
            output = 'E:Robot could not find instructions.'
            j.clients.email.send(fromm, "%s@%s"%(robot,self.domain), subject, output)   

        out="%s\n%s"%(addcommands,out)

        robotdir=j.system.fs.joinPaths(j.dirs.varDir, 'cloudrobot', robot)
        if not j.system.fs.exists(path=robotdir):
            output = 'Could not find robot on fs. Please make sure you are sending to the right one, \'youtrack\' & \'machine\' & \'user\' are supported.'
            j.clients.email.send(fromm, "%s@%s"%(robot,self.domain), subject, output)
            print "COULD NOT FIND ROBOT ON %s"%robotdir
            return

        subject2=j.tools.text.toAscii(subject,80)
        fromm2=j.tools.text.toAscii(fromm)
        path=j.system.fs.joinPaths(j.dirs.varDir, 'cloudrobot', robot,'in',"%s_%s.py"%(fromm2,subject2))
        j.system.fs.writeFile(path,out)


    def green_message(self, peer, mailfrom, rcpttos, data):
        
        msg = self.emailparser.parsestr(data)
        tto=[item.strip().lower() for item in msg['To'].split(",")]
        ttostr=msg['To'].lower()

        #custom config does not belong here, will have to remove later
        if 'smtp@robot.vscalers.com' in tto or \
            (msg['Received'].find("<smtp@robot.vscalers.com>")<>-1 and msg['Received'].find("google.com")<>-1):
            subject2=j.tools.text.toAscii(msg["subject"],40).replace("/","_").replace("\\","_").replace("?","_")
            fromm2=j.tools.text.toAscii(mailfrom,30)
            name="%s_%s_%s_%s"%(j.base.time.getTimeEpoch(),j.base.time.getLocalTimeHRForFilesystem(),fromm2,subject2)
            path=j.system.fs.joinPaths(self.archivefolder,name)
            print "archive:%s"%name
            j.system.fs.writeFile(path,msg.as_string())            
            return

        if "@%s"%self.mailserver not in ttostr:
            print 'Received a message which is not going to be processed. Mail server does not match'
            return
        mailfrom = msg['From']
        html=False


        def do(msg_part):
            contenttype=msg_part.get_content_type()
            if 'text/plain' in contenttype:
                txt=msg_part.get_payload()
                if txt[-1]<>"\n":
                    txt="\n"

            elif 'text/html' in contenttype:
                html=True
                txt=msg_part.get_payload()
                if txt.find('"gmail_extra"')<>-1:
                    return "C"
                else:
                    output="please only send txt commands to robot, we got html."
                    j.clients.email.send([mailfrom], "%s@%s"%(robot_processor,self.domain), msg.get('subject'), output)                        
                    return "S"
            return txt

        
        try:
            robot_processor = msg['To'].split('@')[0]
            if robot_processor.find("<"):
                robot_processor=robot_processor.split("<",1)[0].strip()

            if msg.is_multipart():
                msg_parts = msg.get_payload()
                commands_str=""
                for msg_part in msg_parts:
                    res=do(msg_part)
                    if res=="C":
                        continue
                    elif res=="S":
                        break
                    commands_str+=res
                    
            else:
                res=do(msg)
                if res=="S":
                    return
                if res=="C":                    
                    output="please only send txt commands to robot, we got html."
                    j.clients.email.send([mailfrom], "%s@%s"%(robot_processor,self.domain), msg.get('subject'), output)                        
                    return
                commands_str = res

            print "Processing message from %s"  % msg['From']
            output = ''            
            if not self.robots.has_key(robot_processor):
                output = 'Could not match any robot. Please make sure you are sending to the right one, \'youtrack\' & \'machine\' are supported.'            
                j.clients.email.send([mailfrom], "%s@%s"%(robot_processor,self.domain), msg.get('subject'), output)
                return
            else:
                mail_robot="%s@%s"%(robot_processor,self.domain)
                commands_str_add="@mail_subject=%s\n@mail_from=%s\n@mail_robot=%s\n"%(msg.get('subject'),mailfrom,\
                    mail_robot)
                self.toFileRobot(robot_processor,mailfrom,msg.get('subject'),commands_str,html,addcommands=commands_str_add)

        except Exception,e:
            print j.errorconditionhandler.parsePythonErrorObject(e)            
            j.clients.email.send([mailfrom], "%s@%"%(robot_processor,self.domain), msg.get('subject'), 'A generic error has occured on server.')

