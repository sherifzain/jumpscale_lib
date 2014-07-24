from JumpScale import j
import JumpScale.lib.cloudrobots
import time

class FileRobot():
    def __init__(self):
        self.basepath="%s/cloudrobot"%j.dirs.varDir
        self.robots = {}


    def findGlobal(self,C,name):
        for line in C.split("\n"):
            line=line.strip()
            print line    
            if line.find("@%s"%name)==0:
                name,val=line.split("=",1)
                return val.strip()
        return None

    def start(self):

        for channel in self.robots.keys():
            for item in ["in","out","err","draft"]:  #,"jobs"
                j.system.fs.createDir("%s/%s/%s"%(self.basepath,channel,item))

        print "Started"

        while True:
            # channels=j.system.fs.listDirsInDir("data",False,True)

            #is to get access to the other robots from a robot
            for channel in self.robots.keys():
                self.robots[channel].robots=self.robots
                # for channel in channels:                
                for path in j.system.fs.listFilesInDir("%s/%s/in/"%(self.basepath,channel)):
                    name0=j.system.fs.getBaseName(path).replace(".txt","").replace(".py","")
                    C=j.system.fs.fileGetContents(path)            

                    mail=self.findGlobal(C,"msg_email")
                    if mail<>None:
                        username=j.servers.cloudrobot.getUserGuidOrEmail(mail)
                    else:
                        username=""

                    name="%s_%s_%s_%s.txt"%(j.base.time.getTimeEpoch(),j.base.time.getLocalTimeHRForFilesystem(),name0,username)
                    # j.system.fs.writeFile("%s/%s/jobs/%s"%(self.basepath,channel,name),C)

                    cl = j.servers.cloudrobot.osis_robot_job

                    print "PROCESS:%s"%path            
                    
                    jobguid=self.findGlobal(C,"msg_jobguid")
                    if jobguid==None:
                        print "new job"
                        job = cl.new()
                        job.start = j.base.time.getTimeEpoch()
                        job.rscript_name = name0
                        job.rscript_content = C
                        job.rscript_channel = channel
                        job.onetime = True
                        mailfrom=self.findGlobal(C,"msg_email")
                        job.user = username
                    else:
                        job=cl.get(jobguid)
                        print "existing job:%s"%jobguid
                    job.state = "RUNNING"
                    tmp, tmp, guid=cl.set(job)
                    j.servers.cloudrobot.job2redis(job)

                    result=self.robots[channel].process(C)

                    j.system.fs.remove(path)

                    job.result = result
                    job.end = j.base.time.getTimeEpoch()
                    
                    if result.find(">ERROR:")<>-1:
                        print "ERROR, see %s"%path
                        job.state = "ERROR"
                        path="%s/%s/err/%s"%(self.basepath,channel,name)
                        j.system.fs.writeFile(path,result)
                    else:
                        job.state = "OK"
                        path="%s/%s/out/%s"%(self.basepath,channel,name)
                        j.system.fs.writeFile(path,result)

                    tmp, tmp, guid = cl.set(job)
                    j.servers.cloudrobot.job2redis(job)

            time.sleep(0.5)

