import smtpd
import asyncore
from JumpScale import j
import jinja2
import JumpScale.grid.agentcontroller

class MailRobot(smtpd.SMTPServer):

    def __init__(self, *args, **kwargs):
        self.acl = j.clients.agentcontroller.get()
        templatefolder = j.system.fs.joinPaths(j.dirs.baseDir, 'apps', 'mailrobot', 'templates')
        loader = jinja2.FileSystemLoader(templatefolder)
        self.jenv = jinja2.Environment(loader=loader)
        smtpd.SMTPServer.__init__(self, *args, **kwargs)
    
    def process_message(self, peer, mailfrom, rcpttos, data):
        try:
            hrd = j.core.hrd.getHRD(content=data)
        except:
            print "Invalid hrd given %s" % data
            raise
        allkeys = hrd.prefix('')
        appdict = dict()
        hrddict = dict()
        for key in allkeys:
            if key.startswith('_') or key in ('changed', 'path'):
                continue
            if key.startswith('appdeck'):
                appdict[key] = hrd.get(key)
            hrddict[key] = hrd.get(key)
        hrd = ""
        for line in data.splitlines():
            if line.startswith('appdeck'):
                continue
            hrd += line + "\n"
        result = self.acl.executeJumpScript('jumpscale', 'mailrobotrequest', nid=j.application.whoAmI.nid, args={'appkwargs': appdict, 'hrd': hrd})
        appname = appdict.get("appdeck_app_name", "Unknown")
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
        MailRobot(('0.0.0.0', 1025), None)
        asyncore.loop()
