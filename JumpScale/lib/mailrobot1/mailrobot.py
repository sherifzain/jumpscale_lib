import smtpd
import asyncore
from JumpScale import j
import jinja2

class MailRobot(smtpd.SMTPServer):

    def __init__(self, *args, **kwargs):
        self.acl = j.clients.agentcontroller.get()
        templatefolder = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'mailrobot', 'templates')
        loader = jinja2.FileSystemLoader(templatefolder)
        self.jenv = jinja2.Environment(loader=loader)
        MailRobot.__init__(self, *args, **kwargs)
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        result = self.acl.executeJumpScript('jumpscale', 'mailrobotrequest', nid=j.application.whoAmI, args={'data', data})
        appname = ""
        hrddict = {}
        if result['state'] != "OK":
            msg = """
You request for deployment has failed.
Our support team has been notified and will contact you as soon as possible
"""
            j.clients.mail.sendmail([mailfrom], 'mailrobot@mothership1.com', 'Deployment %s Failed' % appname, msg)
        else:
            template = self.jenv.get_template("%s.tmpl" % appname)
            msg = template.render(**hrddict)
            j.clients.mail.sendmail([mailfrom], 'mailrobot@mothership1.com', 'Deployment %s Succesfull', msg)

class MailRobotFactory(object):
    def start(self):
        MailRobot(('127.0.0.1', 1025), None)
        asyncore.loop()
