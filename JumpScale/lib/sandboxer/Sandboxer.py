from JumpScale import j

class Dep():
    def __init__(self,name,path):
        self.name=name
        self.path=path
        if j.system.fs.isLink(self.path):
            link=j.system.fs.readlink(self.path)
            if j.system.fs.exists(path=link):
                self.path=link
                return
            else:
                base=j.system.fs.getDirName(self.path)
                potpath=j.system.fs.joinPaths(base,link)
                if j.system.fs.exists(potpath):
                    self.path=potpath
                    return
        else:
            if j.system.fs.exists(self.path):
                return
        raise RuntimeError("could not find lib %s"%self.path)

    def copyTo(self,path):
        dest=j.system.fs.joinPaths(path,self.name)
        j.system.fs.createDir(j.system.fs.getDirName(dest))
        j.system.fs.copyFile(self.path, dest)

    def __str__(self):
        return "%-40s %s"%(self.name,self.path)

    __repr__=__str__

class Sandboxer():
    """
    sandbox any linux app
    """

    def __init__(self):
        self._done=[]

    def _ldd(self,path,result={}):
        cmd="ldd %s"%path
        rc,out=j.system.process.execute(cmd)
        for line in out.split("\n"):
            line=line.strip()
            if line=="":
                continue
            if line.find('=>')==-1:
                continue
            name,lpath=line.split("=>")
            name=name.strip()       
            lpath=lpath.split("(")[0]
            lpath=lpath.strip()
            if lpath=="":
                continue
            if name.find("libc.so")<>0 and name.lower().find("libx")<>0 and name not in self._done \
                and name.find("libdl.so")<>0:
                print "found:%s"%name
                result[name]=Dep(name,lpath)
                self._done.append(name)
            result=self._ldd(lpath,result)

        return result

    def findLibs(self,path):
        result=self._ldd(path)
        return result

    def copyLibsTo(self,path,dest):
        result=self.findLibs(path)
        for name,deb in result.iteritems():
            deb.copyTo(dest)
        

