from JumpScale import j

class JailFactory(object):

    def __init__(self):
        pass

    def prepareJSJail(self):
        """
        prepare system we can create jail environments for jumpscale
        """

        j.system.process.execute("chmod -R o-rwx /opt")
        j.system.process.execute("chmod -R o+r /usr")
        j.system.process.execute("chmod -R o-w /usr")
        j.system.process.execute("chmod -R o-w /etc")
        j.system.process.execute("chmod -R o-rwx /home")
        j.system.process.execute("chmod o-rwx /mnt")
        j.system.fs.chmod("/opt/code", 0o700)
        j.system.fs.chmod("/opt/code/jumpscale", 0o777)
        j.system.fs.chown("/opt", "root")
        j.system.process.execute("chmod 777 /opt")
        j.system.process.execute("chmod 777 /opt/jumpscale")
        j.system.process.execute("chmod -R 777 /opt/jumpscale/bin")
        j.system.process.execute("chmod -R 777 /opt/jumpscale/lib")
        j.system.process.execute("chmod -R 777 /opt/jumpscale/libext")
        j.system.process.execute("chmod 777 /opt/code")
        j.system.process.execute("chmod 777 /home")


    def createJSJail(self,user,secret):
        """
        create jumpscale jail environment for 1 user
        """
        self.killSessions(user)

        j.system.unix.addSystemUser(user,None,"/bin/bash","/home/%s"%user)
        j.system.unix.setUnixUserPassword(user,secret)
        j.system.fs.copyDirTree("/opt/jumpscale/apps/jail/defaultenv","/home/%s"%user)
        j.system.fs.symlink("/opt/jumpscale/bin","/home/%s/jumpscale/bin"%user)
        j.system.fs.symlink("/opt/jumpscale/lib","/home/%s/jumpscale/lib"%user)
        j.system.fs.symlink("/opt/jumpscale/libext","/home/%s/jumpscale/libext"%user)
        j.system.fs.createDir("/home/%s/jumpscale/apps"%user)
        j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_examples/examples/","/home/%s/jumpscale/apps/examples"%user)
        j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_examples/prototypes/","/home/%s/jumpscale/apps/prototypes"%user)
        
        def portals():
            j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_portal/apps/portalbase/","/home/%s/jumpscale/apps/portalbase"%user)
            j.system.fs.symlink("/opt/code/jumpscale/default__jumpscale_portal/apps/portalexample/","/home/%s/jumpscale/apps/portalexample"%user)
            src="/opt/code/jumpscale/default__jumpscale_grid/apps/incubaidportals/"
            j.system.fs.copyDirTree(src,"/home/%s/jumpscale/apps/incubaidportals"%user)
        portals()

        src="/opt/code/jumpscale/default__jumpscale_lib/apps/cloudrobot/"
        j.system.fs.copyDirTree(src,"/home/%s/jumpscale/apps/cloudrobot"%user)

        src="/opt/code/jumpscale/default__jumpscale_core/apps/admin/"
        j.system.fs.copyDirTree(src,"/home/%s/jumpscale/apps/admin"%user)

        j.system.process.execute("chmod -R ug+rw /home/%s"%user)
        j.system.fs.chown("/home/%s"%user, user)
        j.system.process.execute("rm -rf /tmp/mc-%s"%user)

        secrpath="/home/%s/.secret"%user
        j.system.fs.writeFile(filename=secrpath,contents=secret)

        j.system.fs.writeFile("/etc/sudoers.d/%s"%user,"%s ALL = (root) NOPASSWD:ALL"%user)
        

    def listSessions(self,user):
        res=[]
        rc,out=j.system.process.execute("sudo -P -u %s tmux list-sessions"%user)
        for line in out.split("\n"):
            if line.strip()=="":
                continue
            if line.find(":")<>-1:
                name=line.split(":",1)[0].strip()
                res.append(name)
        return res

    def killSessions(self,user):
        j.system.process.killUserProcesses(user)
        j.system.fs.removeDirTree("/home/%s"%user)        
        j.system.unix.removeUnixUser(user, removehome=True,die=False)

        from IPython import embed
        print "DEBUG NOW ooo"
        embed()
        
    def killAllSessions(self):
        for user in  j.system.fs.listDirsInDir("/home",False,True):
            secrpath="/home/%s/.secret"%user
            if j.system.fs.exists(path=secrpath):
                self.killSessions(user)
        cmd="killall shellinaboxd"
        j.system.process.execute(cmd)

    def send2session(self,user,session,cmd):
        j.system.process.execute("sudo -P -u %s tmux send -t %s %s ENTER"%(user,session,cmd))

    def createJSJailSession(self,user,session,cmd=None):
        secrpath="/home/%s/.secret"%user
        # secret=j.system.fs.fileGetContents(secrpath).strip()

        #check session exists
        sessions=self.listSessions()
        if not session in sessions:
            #need to create session
            if cmd<>None:
                j.system.process.execute("sudo -P -u %s tmux new-session -d -s %s %s"%(user,session,cmd))
            else:
                j.system.process.execute("sudo -P -u %s tmux new-session -d -s %s"%(user,session))
            j.system.process.execute("sudo -P -u %s tmux set-option -t %s status off"%(user,session))
            if cmd=="js":
                self.send2session(user,session,"clear")  


            

             
