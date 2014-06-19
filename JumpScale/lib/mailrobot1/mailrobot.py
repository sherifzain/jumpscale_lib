import smtpd
import asyncore
from JumpScale import j
import JumpScale.grid.agentcontroller
import JumpScale.baselib.mailclient
import email

class MailRobot(smtpd.SMTPServer):

    def __init__(self, *args, **kwargs):
        self.emailparser = email.Parser.Parser()
        self.acl = j.clients.agentcontroller.get()
        self.templatefolder = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'mailrobot', 'templates')
        smtpd.SMTPServer.__init__(self, *args, **kwargs)
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        mailserver = j.application.config.get('mailrobot.mailserver')
        msg = self.emailparser.parsestr(data)
        if mailserver != msg['To'].split('@')[1]:
            print 'Received a message which is not going to be processed. Mail server does not match'
            return
        mailfrom = msg['From']
        try:
            hrdstr = msg.get_payload()
            try:
                hrd = j.core.hrd.getHRD(content=hrdstr)
            except:
                print "Invalid hrd given %s" % data
                raise
            print "Processing message from %s"  % msg['From']
            allkeys = hrd.prefix('')
            appdict = dict()
            hrddict = dict()
            for key in allkeys:
                if key.startswith('_') or key in ('changed', 'path'):
                    continue
                if key.startswith('appdeck'):
                    appdict[key] = hrd.get(key)
                hrddict[key] = hrd.get(key)
            hrdstr = ""
            for line in data.splitlines():
                if line.startswith('appdeck'):
                    continue
                hrdstr += line + "\n"
            result = self.acl.executeJumpScript('jumpscale', 'mailrobotrequest', nid=j.application.whoAmI.nid, args={'appkwargs': appdict, 'hrd': hrdstr})
            appname = appdict.get("appdeck.app.name", "default")
            if result['state'] != "OK":
                msg = """
You request for deployment has failed.
Our support team has been notified and will contact you as soon as possible
    """
                j.clients.email.send([mailfrom], 'mailrobot@mothership1.com', 'Deployment %s Failed' % appname, msg)
            else:
                template = j.system.fs.fileGetContents(j.system.fs.joinPaths(self.templatefolder, "%s.tmpl" % appname))
                msg = hrd.applyOnContent(template, result['result'])
                j.clients.email.send([mailfrom], 'mailrobot@mothership1.com', 'Deployment %s Succesfull' % appname, msg)
        except:
            msg = '''
Deployment failed. A generic error has occured.
Please try again later.
    '''
            j.clients.email.send([mailfrom], 'mailrobot@mothership1.com', 'Deployment Failed', msg)

class MailRobotFactory(object):
    def start(self):
        MailRobot(('0.0.0.0', 25), None)
        asyncore.loop(timeout=300)
