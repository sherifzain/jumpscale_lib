from JumpScale import j

from .HTTPRobot import HTTPRobot
from .MailRobot import MailRobot
from .FileRobot import FileRobot
import JumpScale.baselib.redis
import ujson as json
import time

class CloudRobotFactory(object):
    def __init__(self):
        self.domain=j.application.config.get("mailrobot.mailserver")
        self.osis = j.core.osis.getClient(user='root')
        self.osis_robot_job = j.core.osis.getClientForCategory(self.osis, 'robot', 'job')        
        self.osis_oss_user = j.core.osis.getClientForCategory(self.osis, 'oss', 'user')
        self.redis=j.clients.redis.getRedisClient("127.0.0.1", 7768)

    def startMailServer(self,robots={}):
        robot = MailRobot(('0.0.0.0', 25))
        robot.robots=robots
        print "start server on port:25"
        robot.serve_forever()

    def startHTTP(self, addr='0.0.0.0', port=8099,robots={}):
        robot=HTTPRobot(addr=addr, port=port)
        robot.robots=robots
        robot.start()

    def startFileRobot(self,robots={}):
        robot=FileRobot()
        robot.robots=robots
        robot.start()

    def job2redis(self,job):
        q=self._getQueue(job)
        data=json.dumps(job.__dict__)
        self.redis.hset("robot:jobs",job.guid,data)   
        print "job:%s to redis"%job.guid
        if job.end<>0:
            n=j.base.time.getTimeEpoch()
            print "QUEUE OK"
            q.put(str(n))
            q.set_expire(n+120)

    def jobWait(self,jobguid):
        q=j.clients.redis.getGeventRedisQueue("127.0.0.1", 7768, "robot:queues:%s" % jobguid)
        print "wait for job:%s"%jobguid
        # while q.empty():
        #     print "queue empty for %s"%jobguid
        #     time.sleep(0.1)
        jobguid=q.get()
        return 
        
    def _getQueue(self,job):    
        queue=j.clients.redis.getGeventRedisQueue("127.0.0.1", 7768, "robot:queues:%s" % job.guid)
        return queue

    def toFileRobot(self,channel,msg,mailfrom,rscriptname,args={}):
        
        # msg=j.tools.text.toAscii(msg)

        if msg.strip()=="":
            raise RuntimeError("Cannot be empty msg")

        if msg[-1]<>"\n":
            msg+="\n"
        
        robotdir=j.system.fs.joinPaths(j.dirs.varDir, 'cloudrobot', channel)
        if not j.system.fs.exists(path=robotdir):
            msg = 'Could not find robot for channel \'%s\' on fs. Please make sure you are sending to the right one, \'youtrack\' & \'machine\' & \'user\' are supported.'%channel
            raise RuntimeError("E:%s"%msg)

        args["msg_subject"]=rscriptname
        args["msg_email"]=mailfrom
        args["msg_channel"]=channel


        subject2=j.tools.text.toAscii(args["msg_subject"],80)
        fromm="%s@%s"%(channel,self.domain)
        fromm2=j.tools.text.toAscii(fromm)
        filename="%s_%s.py"%(fromm2,subject2)

        cl=self.osis_robot_job

        job = cl.new()
        job.start = j.base.time.getTimeEpoch()
        job.rscript_name = rscriptname
        job.rscript_content = msg
        job.rscript_channel = channel
        job.state = "PENDING"
        job.onetime = True
        job.user = self.getUserGuidOrEmail(mailfrom)
        tmp, tmp, guid = cl.set(job)

        args["msg_jobguid"]=job.guid

        premsg=""
        for key in args.keys():
            premsg+="@%s=%s\n"%(key,args[key])
        msg="%s\n%s\n"%(premsg,msg)

        self.job2redis(job)

        path=j.system.fs.joinPaths(j.dirs.varDir, 'cloudrobot', channel,'in',filename)
        

        j.system.fs.writeFile(path,msg)

        return guid


    def getUserGuidOrEmail(self,email):
        if email.find("<")<>-1:
            email=email.split("<",1)[1]
            email=email.split(">",1)[0]        
        return email        
        