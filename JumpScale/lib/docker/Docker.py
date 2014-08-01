#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os
# import JumpScale.baselib.netconfig
import netaddr
import JumpScale.baselib.remote
import docker

class Docker():

    def __init__(self):
        self._basepath = "/mnt/vmstor/docker"
        self._prefix=""
        self.client = docker.Client(base_url='unix://var/run/docker.sock',
                  version='1.12',
                  timeout=10)


    def execute(self, command):
        env = os.environ.copy()
        env.pop('PYTHONPATH', None)
        (exitcode, stdout, stderr) = j.system.process.run(command, showOutput=False, captureOutput=True, stopOnError=False, env=env)
        if exitcode != 0:
            raise RuntimeError("Failed to execute %s: Error: %s, %s" % (command, stdout, stderr))
        return stdout

    @property
    def basepath(self):
        if not self._basepath:
            if j.application.config.exists('docker.basepath'):
                self._basepath = j.application.config.get('docker.basepath')
            else:
                self._basepath="/mnt/vmstor/docker" #btrfs subvol create
        return self._basepath

    def _getChildren(self,pid,children):
        process=j.system.process.getProcessObject(pid)
        children.append(process)
        for child in process.get_children():
            children=self._getChildren(child.pid,children)
        return children

    def _get_rootpath(self,name):
        rootpath=j.system.fs.joinPaths(self.basepath, '%s%s' % (self._prefix, name), 'rootfs')
        return rootpath

    def _getMachinePath(self,machinename,append=""):
        if machinename=="":
            raise RuntimeError("Cannot be empty")
        base = j.system.fs.joinPaths( self.basepath,'%s%s' % (self._prefix, machinename))
        if append<>"":
            base=j.system.fs.joinPaths(base,append)
        return base

    def list(self):
        """
        return list of names
        """        
        res={}
        for item in self.client.containers():
            res[str(item["Names"][0].strip("/").strip())]=str(item["Id"].strip())
        return res

    def ps(self):
        """
        return detailed info
        """
        return self.client.containers()        

    def getInfo(self,name):
        for item in self.ps():
            if "/%s"%name in item["Names"]:
                return item

    def getProcessList(self, name, stdout=True):
        """
        @return [["$name",$pid,$mem,$parent],....,[$mem,$cpu]]
        last one is sum of mem & cpu
        """
        raise RuntimeError("not implemented")
        pid = self.getPid(name)
        children = list()
        children=self._getChildren(pid,children)
        result = list()
        pre=""
        mem=0.0
        cpu=0.0
        cpu0=0.0
        prevparent=""
        for child in children:
            if child.parent.name != prevparent:
                pre+=".."
                prevparent=child.parent.name
            # cpu0=child.get_cpu_percent()
            mem0=int(round(child.get_memory_info().rss/1024,0))
            mem+=mem0
            cpu+=cpu0
            if stdout:
                print "%s%-35s %-5s mem:%-8s" % (pre,child.name, child.pid, mem0)
            result.append([child.name,child.pid,mem0,child.parent.name])
        cpu=children[0].get_cpu_percent()
        result.append([mem,cpu])
        if stdout:
            print "TOTAL: mem:%-8s cpu:%-8s" % (mem, cpu)
        return result

    def exportRsync(self,name,backupname,key="pub"):
        raise RuntimeError("not implemented")
        self.removeRedundantFiles(name)
        ipaddr=j.application.config.get("jssync.addr")
        path=self._getMachinePath(name)
        if not j.system.fs.exists(path):
            raise RuntimeError("cannot find machine:%s"%path)
        if backupname[-1]<>"/":
            backupname+="/"
        if path[-1]<>"/":
            path+="/"
        cmd="rsync -a %s %s::upload/%s/images/%s --delete-after --modify-window=60 --compress --stats  --progress --exclude '.Trash*'"%(path,ipaddr,key,backupname)
        # print cmd
        j.system.process.executeWithoutPipe(cmd)

    def _btrfsExecute(self,cmd):
        cmd="btrfs %s"%cmd
        print cmd
        return self.execute(cmd)

    def btrfsSubvolList(self):
        raise RuntimeError("not implemented")
        out=self._btrfsExecute("subvolume list %s"%self.basepath)
        res=[]
        for line in out.split("\n"):
            if line.strip()=="":
                continue
            if line.find("path ")<>-1:
                path=line.split("path ")[-1]
                path=path.strip("/")
                path=path.replace("lxc/","")
                res.append(path)
        return res

    def btrfsSubvolNew(self,name):
        raise RuntimeError("not implemented")
        if not self.btrfsSubvolExists(name):
            cmd="subvolume create %s/%s"%(self.basepath,name)
            self._btrfsExecute(cmd)

    def btrfsSubvolCopy(self,nameFrom,NameDest):
        raise RuntimeError("not implemented")
        if not self.btrfsSubvolExists(nameFrom):
            raise RuntimeError("could not find vol for %s"%nameFrom)
        if j.system.fs.exists(path="%s/%s"%(self.basepath,NameDest)):
            raise RuntimeError("path %s exists, cannot copy to existing destination, destroy first."%nameFrom)            
        cmd="subvolume snapshot %s/%s %s/%s"%(self.basepath,nameFrom,self.basepath,NameDest)
        self._btrfsExecute(cmd)    

    def btrfsSubvolExists(self,name):
        raise RuntimeError("not implemented")
        subvols=self.btrfsSubvolList()
        # print subvols
        return name in subvols

    def btrfsSubvolDelete(self,name):
        raise RuntimeError("not implemented")
        if self.btrfsSubvolExists(name):
            cmd="subvolume delete %s/%s"%(self.basepath,name)
            self._btrfsExecute(cmd)
        path="%s/%s"%(self.basepath,name)
        if j.system.fs.exists(path=path):
            j.system.fs.removeDirTree(path)
        if self.btrfsSubvolExists(name):
            raise RuntimeError("vol cannot exist:%s"%name)

    def removeRedundantFiles(self,name):
        raise RuntimeError("not implemented")
        basepath=self._getMachinePath(name)
        j.system.fs.removeIrrelevantFiles(basepath,followSymlinks=False)

        toremove="%s/rootfs/var/cache/apt/archives/"%basepath
        j.system.fs.removeDirTree(toremove)

    def importRsync(self,backupname,name,basename="",key="pub"):
        """
        @param basename is the name of a start of a machine locally, will be used as basis and then the source will be synced over it
        """    
        raise RuntimeError("not implemented")
        ipaddr=j.application.config.get("jssync.addr")
        path=self._getMachinePath(name)    

        self.btrfsSubvolNew(name)

        # j.system.fs.createDir(path)

        if backupname[-1]<>"/":
            backupname+="/"
        if path[-1]<>"/":
            path+="/"

        if basename<>"":
            basepath=self._getMachinePath(basename)
            if basepath[-1]<>"/":
                basepath+="/"
            if not j.system.fs.exists(basepath):
                raise RuntimeError("cannot find base machine:%s"%basepath)
            cmd="rsync -av -v %s %s --delete-after --modify-window=60 --size-only --compress --stats  --progress"%(basepath,path)            
            print cmd
            j.system.process.executeWithoutPipe(cmd)

        cmd="rsync -av -v %s::download/%s/images/%s %s --delete-after --modify-window=60 --compress --stats  --progress"%(ipaddr,key,backupname,path)
        print cmd
        j.system.process.executeWithoutPipe(cmd)        

    def exportTgz(self,name,backupname):
        raise RuntimeError("not implemented")
        self.removeRedundantFiles(name)
        path=self._getMachinePath(name)
        bpath= j.system.fs.joinPaths(self.basepath,"backups")
        if not j.system.fs.exists(path):
            raise RuntimeError("cannot find machine:%s"%path)
        j.system.fs.createDir(bpath)
        bpath= j.system.fs.joinPaths(bpath,"%s.tgz"%backupname)
        cmd="cd %s;tar Szcf %s ."%(path,bpath)
        j.system.process.executeWithoutPipe(cmd)
        return bpath

    def importTgz(self,backupname,name):
        raise RuntimeError("not implemented")
        path=self._getMachinePath(name)        
        bpath= j.system.fs.joinPaths(self.basepath,"backups","%s.tgz"%backupname)
        if not j.system.fs.exists(bpath):
            raise RuntimeError("cannot find import path:%s"%bpath)
        j.system.fs.createDir(path)

        cmd="cd %s;tar xzvf %s -C ."%(path,bpath)        
        j.system.process.executeWithoutPipe(cmd)

    def create(self,name="",ports="",vols="",volsro="",stdout=True,base="despiegk/js",nameserver="8.8.8.8",replace=True,cpu=None,mem=0):
        """
        @param ports in format as follows  "22:8022 80:8080"  the first arg e.g. 22 is the port in the container
        @param vols in format as follows "/var/insidemachine:/var/inhost # /var/1:/var/1 # ..."   '#' is separator
        """
        name=name.lower().strip()
        print "create:%s"%name
        running=self.list()
        running=running.keys()
        if not replace:
            if name in running:
                j.events.opserror_critical("Cannot create machine with name %s, because it does already exists.")   

        self.destroy(name)

        if vols==None:
            vols=""
        if volsro==None:
            volsro=""

        if mem==None:
            mem=0

        if int(mem)>0:
            mem=long(mem)*1024

        portsdict={}
        if len(ports)>0:
            items=ports.split(" ")
            for item in items:
                key,val=item.split(":",1)
                portsdict[int(key)]=int(val)

        volsdict={}
        if len(vols)>0:
            items=vols.split("#")
            for item in items:
                key,val=item.split(":",1)
                volsdict[str(key).strip()]=str(val).strip()

        volsdictro={}
        if len(volsro)>0:
            items=volsro.split("#")
            for item in items:
                key,val=item.split(":",1)
                volsdictro[str(key).strip()]=str(val).strip()
                
        volsdict["/var/js/%s/"%name]="/opt/jsbox_data/var/data/"
        volsdict["/var/js/all/jpfiles/"]="/opt/jsbox_data/var/jpackages/files/"

        binds={}

        for key,path in volsdict.iteritems():
            j.system.fs.createDir(path) #create the path on hostname
            binds[key]={"bind":path,"ro":False}

        for key,path in volsdictro.iteritems():
            j.system.fs.createDir(path) #create the path on hostname
            binds[key]={"bind":path,"ro":True}

        volskeys=volsdict.keys()+volsdictro.keys()

        cmd="sh -c \"chmod 777 /var/run/screen; /var/run/screen;exec >/dev/tty 2>/dev/tty </dev/tty && /sbin/my_init -- /usr/bin/screen -s bash\""        

        # mem=1000000

        res=self.client.create_container(image=base, command=cmd, hostname=name, user="root", \
            detach=False, stdin_open=False, tty=True, mem_limit=mem, ports=portsdict.keys(), environment=None, volumes=volskeys,  \
            network_disabled=False, name=name, entrypoint=None, cpu_shares=cpu, working_dir=None, domainname=None, memswap_limit=0)
        
        id=res["Id"]
        
        self.client.start(container=id, binds=binds, port_bindings=portsdict, lxc_conf=None, \
            publish_all_ports=False, links=None, privileged=False, dns=nameserver, dns_search=None, volumes_from=None, network_mode=None)
         
        self.pushSSHKey(name)

        # return self.getIp(name)

    def setHostName(self,name):
        raise RuntimeError("not implemented")
        lines=j.system.fs.fileGetContents("/etc/hosts")
        out=""
        for line in lines.split("\n"):
            if line.find(name)<>-1:
                continue
            out+="%s\n"%line
        out+="%s      %s\n"%(self.getIp(name),name)
        j.system.fs.writeFile(filename="/etc/hosts",contents=out)
        
    def getPubPortForInternalPort(self,name,port):
        info=self.getInfo(name)
        for port2 in info["Ports"]:
            if int(port2["PrivatePort"])==int(port):
                return port2["PublicPort"]

    def pushSSHKey(self,name):
        # path=j.system.fs.joinPaths(self._get_rootpath(name),"root",".ssh","authorized_keys")
        keyloc="/root/.ssh/id_dsa.pub"
        if not j.system.fs.exists(path=keyloc):
            j.system.process.executeWithoutPipe("ssh-keygen -t dsa")            
            if not j.system.fs.exists(path=keyloc):
                raise RuntimeError("cannot find path for key %s, was keygen well executed"%keyloc)            
        key=j.system.fs.fileGetContents(keyloc)
        # j.system.fs.writeFile(filename=path,contents="%s\n"%content)
        # path=j.system.fs.joinPaths(self._get_rootpath(name),"root",".ssh","known_hosts")
        # j.system.fs.writeFile(filename=path,contents="")

        c=j.remote.cuisine.api
        c.fabric.api.env['password'] = "js007js"
        c.fabric.api.env['connection_attempts'] = 5

        ssh_port=self.getPubPortForInternalPort(name,22)
        if ssh_port==None:
            j.events.opserror_critical("cannot find pub port ssh")

        c.connect('%s:%s' % ("localhost", ssh_port), u"root")

        c.ssh_authorize("root",key)
        return key

    def getSSH(self,name):
        ssh_port=self.getPubPortForInternalPort(name,22)        
        c=j.remote.cuisine.api
        c.fabric.api.env['connection_attempts'] = 2
        c.connect('%s:%s' % ("localhost", ssh_port), u"root")
        return c

    def destroyall(self):
        running=self.list()
        for item in running.keys():
            self.destroy(item)

        # startpath="/mnt/vmstor"
        # cmd="btrfs subvol list %s"%startpath
        # res=self.execute(cmd)
        # for line in res.split("\n"):
        #     if line.find("path")<>-1:
        #         part=line.split("path",1)[1]
        #         if part.find("docker2")<>-1:
        #             # id=line.split("gen")[0].strip("ID").strip()
        #             part=part.strip()
        #             path="%s/%s"%(startpath,part)
        #             command="btrfs subvol delete %s"%path
        #             print j.system.process.execute(command, dieOnNonZeroExitCode=False, outputToStdout=False, useShell=False, ignoreErrorOutput=False)

    def destroy(self,name):        
        running=self.list()        
        if name in running.keys():
            idd=running[name]    
            self.client.kill(idd)
            self.client.remove_container(idd)

    def stop(self,name):
        running=self.list()        
        if name in running.keys():
            idd=running[name]    
            self.client.kill(idd)
