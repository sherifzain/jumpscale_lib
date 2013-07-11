from OpenWizzy import o
import time

IDSTR="""
    $action -5d #means all before 5 days from now
    $action -5h #means all before 5 hours from now
    $action -34234 #means all events before 34234
    $action 34234 #means specified event 34234
    $action 2000-34234 #means events between 2000 and 34234
    $action loc:uat #means where location has uat in the name
    $action channel:becloud #means where channel has becloud in the name
    $action channel:becloud loc:uat 2000-3000  #is combination of 3 of above statements
"""


class MailRobotFactory():
    
    def get(self,mailserver,login,passwd):
        return MailRobot(mailserver,login,passwd)
        
class MailRobot():
    def __init__(self,mailserver,login,passwd=""):
        """
        structure of commands is
        @subject can be anything
        @text has '@@' inside & format is @@acommand further params in form of tags & labels, @@needs to be at start of line
        
        example usage self.cmd is dict with as key the command e.g. help and then calue is list with method & helpfor this method
        {source}
        help="ignore events, format:%s" % IDSTR
        help=help.replace("$action","ignore")
        self.cmds["ignore"]=[self.ignore,help]
        
        ### example how to use this class
        robot=o.tools.mailrobot.get("imap.gmail.com",'action@awingu.com','be343483')
        robot.start(process,loghandler=actionlh)  
        
        {source}
        """
        self.cmds={}
        self.cmds["help"]=[self.help,"help"]  #standard cmds
        self.mailserver="imap.gmail.com"
        self.login='action@awingu.com'
        self.passwd=passwd
        self.waittime=10


    def start(self,processNonMatchedMessagesHandler,**args):
        """
        login to imapserver and start walking over messages 
        @param processNonMatchedMessagesHandler is a method which will process messages which do not have @@ inside which point to command
        """
    
        def process(mailfrom,emailepoch,subject,text,args):
	    if text==None:
		return
            if text.find("@@")<>-1:
                self.processMsg(mailfrom,emailepoch,subject,text)
            else:
                processNonMatchedMessagesHandler(mailfrom,emailepoch,subject,text,args)                
                
        while True:
            reader=o.clients.imapreader.get(self.mailserver,self.login,self.passwd)
            reader.processnew(process,**args)
            reader.close()            
            try:
                reader=o.clients.imapreader.get(self.mailserver,self.login,self.passwd)
                reader.processnew(process)
                reader.close()
            except Exception,e:
                print e
                print "could not connect to server, will try again later"
            time.sleep(self.waittime)
            
                        
        
    def processMsg(self,mailfrom,emailepoch,subject,text):
        for line in text.split("\n"):
            line=line.strip().lower()
            if line.find("@@")==0:
                #found cmd
                for cmd in self.cmds.keys():
                    if line.find("@@%s" % cmd)==0:
                        method,helptxt=self.cmds[cmd]
                        params=line.replace("@@%s" % cmd,"")
                        method(mailfrom,emailepoch,subject,text,params)
                            
    def parseFrom(self,mailfrom):
        if mailfrom.find("<")<>-1:
            mailfrom=mailfrom.split("<")[1]
            mailfrom=mailfrom.split(">")[0]
        else:
            if mailfrom.find("@")==-1:
                raise RuntimeError("could not find valid from addr, was %s" % mailfrom)
        
    def help(self,mailfrom,mailepoch,subject,text,params):
        s=""
        for key in self.cmds.keys():
            cmd,help=self.cmds[key]
            s+="%s:%s\n\n" % (key,help)            
        
        self.send(self.parseFrom(mailfrom),"actionrobot: help", s)
    
    def ignore(self,mailfrom,mailepoch,subject,text,params):    
        pass

    def delete(self,mailfrom,mailepoch,subject,text,params):    
        pass

    
    def send(self,to,subject,message):
        import smtplib         
        to = 'mkyong2002@yahoo.com'
        gmail_user = 'mkyong2002@gmail.com'
        gmail_pwd = 'yourpassword'
        smtpserver = smtplib.SMTP("smtp.gmail.com",587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo
        smtpserver.login(gmail_user, gmail_pwd)
        header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:testing \n'
        print header
        msg = header + '\n this is test msg from mkyong.com \n\n'
        smtpserver.sendmail(gmail_user, to, msg)
        print 'done!'
        smtpserver.close()        
        from OpenWizzy.core.Shell import ipshellDebug,ipshell
        print "DEBUG NOW send"
        ipshell()
        