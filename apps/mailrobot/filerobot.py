from JumpScale import j

from robots import *

j.application.start('filerobot')

from robots import *

robot=robots["youtrack"]

channels=j.system.fs.listDirsInDir("in",False,True)
for channel in channels:
    for path in j.system.fs.listFilesInDir("in/%s"%channel):
        C=j.system.fs.fileGetContents(path)
        print "PROCESS:%s"%path
        result=robot.process(C)
        if result.find(">ERROR:")<>-1:
            print "ERROR, see %s"%path
            j.system.fs.writeFile(path,result)
        else:
            j.system.fs.remove(path)
            name=j.system.fs.getBaseName(path)
            path="out/%s/%s"%(channel,name)
            j.system.fs.createDir(j.system.fs.getDirName(path))
            j.system.fs.writeFile(path,result)


j.application.stop(0)
