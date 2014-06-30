from JumpScale import j

from robots import *
import time

j.application.start('filerobot')

from robots import *

# robot=robots["youtrack"]

basepath="%s/cloudrobot"%j.dirs.varDir

for channel in robots.keys():
    for item in ["in","out","err","logs","jobs","draft"]:
        j.system.fs.createDir("%s/%s/%s"%(basepath,channel,item))

def findGlobal(C,name):
    for line in C.split("\n"):
        line=line.strip()
        print line    
        if line.find("@%s"%name)==0:
            name,val=line.split("=",1)
            return val.strip()
    return "?"

while True:
    # channels=j.system.fs.listDirsInDir("data",False,True)
    for channel in robots.keys():
    # for channel in channels:
        for path in j.system.fs.listFilesInDir("%s/%s/in/"%(basepath,channel)):
            name0=j.system.fs.getBaseName(path).replace(".txt","")
            C=j.system.fs.fileGetContents(path)            
            name="%s_%s_%s_%s.txt"%(j.base.time.getTimeEpoch(),j.base.time.getLocalTimeHRForFilesystem(),name0,findGlobal(C,"source"))
            j.system.fs.writeFile("%s/%s/jobs/%s"%(basepath,channel,name),C)
            print "PROCESS:%s"%path
            result=robots[channel].process(C)
            j.system.fs.remove(path)
            
            if result.find(">ERROR:")<>-1:
                print "ERROR, see %s"%path
                path="%s/%s/err/%s"%(basepath,channel,name)
                j.system.fs.writeFile(path,result)
            else:
                path="%s/%s/out/%s"%(basepath,channel,name)
                j.system.fs.writeFile(path,result)
    time.sleep(0.5)

j.application.stop(0)
