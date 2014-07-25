#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os
import JumpScale.baselib.netconfig
import netaddr


class Lxc():

    def __init__(self):
        self._prefix="" #no longer use prefixes
        self._basepath = None

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
            if j.application.config.exists('lxc.basepath'):
                self._basepath = j.application.config.get('lxc.basepath')
            else:
                self._basepath="/mnt/vmstor/lxc" #btrfs subvol create
            if not j.system.fs.exists(path=self._basepath):
                raise RuntimeError("only btrfs lxc supported for now")
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
        names of running & stopped machines
        @return (running,stopped)
        """
        cmd="lxc-ls --fancy  -P %s"%self.basepath
        out=self.execute(cmd)

        stopped = []
        running = []
        current = None
        for line in out.split("\n"):
            line = line.strip()
            if line.find('RUNNING')<>-1:
                current = running
            elif line.find('STOPPED')<>-1:
                current = stopped
            else:
                continue
            name=line.split(" ")[0]
            if name.find(self._prefix)==0:
                name=name.replace(self._prefix,"")
                current.append(name)
        running.sort()
        stopped.sort()
        return (running,stopped)

    def getIp(self,name,fail=True):
        hrd=self.getConfig(name)
        return hrd.get("ipaddr")

    def getConfig(self,name):
        configpath=j.system.fs.joinPaths(self.basepath, '%s%s' % (self._prefix, name),"jumpscaleconfig.hrd")
        if not j.system.fs.exists(path=configpath):
            content="""
ipaddr=
"""
            j.system.fs.writeFile(configpath,contents=content)
        return j.core.hrd.getHRD( path=configpath)

    def getPid(self,name,fail=True):
        out=self.execute("lxc-info -n %s%s -p"%(self._prefix,name))
        pid=0
        for line in out.splitlines():
            line=line.strip().lower()
            name, pid = line.split(':')
            pid = int(pid.strip())
        if pid==0:
            if fail:
                raise RuntimeError("machine:%s is not running"%name)
            else:
                return 0
        return pid

    def getProcessList(self, name, stdout=True):
        """
        @return [["$name",$pid,$mem,$parent],....,[$mem,$cpu]]
        last one is sum of mem & cpu
        """
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
        if not self.btrfsSubvolExists(name):
            cmd="subvolume create %s/%s"%(self.basepath,name)
            self._btrfsExecute(cmd)

    def btrfsSubvolCopy(self,nameFrom,NameDest):
        if not self.btrfsSubvolExists(nameFrom):
            raise RuntimeError("could not find vol for %s"%nameFrom)
        if j.system.fs.exists(path="%s/%s"%(self.basepath,NameDest)):
            raise RuntimeError("path %s exists, cannot copy to existing destination, destroy first."%nameFrom)            
        cmd="subvolume snapshot %s/%s %s/%s"%(self.basepath,nameFrom,self.basepath,NameDest)
        self._btrfsExecute(cmd)    

    def btrfsSubvolExists(self,name):
        subvols=self.btrfsSubvolList()
        # print subvols
        return name in subvols

    def btrfsSubvolDelete(self,name):
        if self.btrfsSubvolExists(name):
            cmd="subvolume delete %s/%s"%(self.basepath,name)
            self._btrfsExecute(cmd)
        path="%s/%s"%(self.basepath,name)
        if j.system.fs.exists(path=path):
            j.system.fs.removeDirTree(path)
        if self.btrfsSubvolExists(name):
            raise RuntimeError("vol cannot exist:%s"%name)

    def removeRedundantFiles(self,name):
        basepath=self._getMachinePath(name)
        j.system.fs.removeIrrelevantFiles(basepath,followSymlinks=False)

        toremove="%s/rootfs/var/cache/apt/archives/"%basepath
        j.system.fs.removeDirTree(toremove)

    def importRsync(self,backupname,name,basename="",key="pub"):
        """
        @param basename is the name of a start of a machine locally, will be used as basis and then the source will be synced over it
        """    
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
        path=self._getMachinePath(name)        
        bpath= j.system.fs.joinPaths(self.basepath,"backups","%s.tgz"%backupname)
        if not j.system.fs.exists(bpath):
            raise RuntimeError("cannot find import path:%s"%bpath)
        j.system.fs.createDir(path)

        cmd="cd %s;tar xzvf %s -C ."%(path,bpath)        
        j.system.process.executeWithoutPipe(cmd)

    def create(self,name="",stdout=True,base="base",start=False,nameserver="8.8.8.8",replace=True):
        """
        @param name if "" then will be an incremental nr
        """
        print "create:%s"%name
        if replace:
            if j.system.fs.exists(self._getMachinePath(name)):
                self.destroy(name)
   

        running,stopped=self.list()
        machines=running+stopped
        if name=="":
            nr=0#max
            for m in machines:
                if j.basetype.integer.checkString(m):
                    if int(m) > nr:
                        nr=int(m)
            nr += 1
            name = nr
        lxcname="%s%s"%(self._prefix,name)

        # cmd="lxc-clone --snapshot -B overlayfs -B btrfs -o %s -n %s -p %s -P %s"%(base,lxcname,self.basepath,self.basepath)
        # print cmd
        # out=self.execute(cmd)

        self.btrfsSubvolCopy(base,lxcname)
       
        # if lxcname=="base":
        self._setConfig(lxcname,base)

        #is in path need to remove
        resolvconfpath=j.system.fs.joinPaths(self._get_rootpath(name),"etc","resolv.conf")
        if j.system.fs.isLink(resolvconfpath):
            j.system.fs.unlink(resolvconfpath)            

        hostpath=j.system.fs.joinPaths(self._get_rootpath(name),"etc","hostname")
        j.system.fs.writeFile(filename=hostpath,contents=name)

        #add host in own hosts file
        hostspath=j.system.fs.joinPaths(self._get_rootpath(name),"etc","hosts")
        lines=j.system.fs.fileGetContents(hostspath)
        out=""
        for line in lines:
            line=line.strip()
            if line.strip()=="" or line[0]=="#":
                continue
            if line.find(name)<>-1:
                continue
            out+="%s\n"%line
        out+="%s      %s\n"%("127.0.0.1",name)
        j.system.fs.writeFile(filename=hostspath,contents=out)

        j.system.netconfig.setRoot(self._get_rootpath(name)) #makes sure the network config is done on right spot

        j.system.netconfig.reset()
        j.system.netconfig.setNameserver(nameserver)

        j.system.netconfig.root=""#set back to normal

        hrd=self.getConfig(name)
        ipaddrs=j.application.config.getDict("lxc.mgmt.ipaddresses")
        if ipaddrs.has_key(name):
            ipaddr=ipaddrs[name]
        else:
            #find free ip addr
            import netaddr            
            existing=[netaddr.ip.IPAddress(item).value for item in  ipaddrs.itervalues() if item.strip()<>""]
            ip = netaddr.IPNetwork(j.application.config.get("lxc.mgmt.ip"))
            for i in range(ip.first+2,ip.last-2):
                if i not in existing:
                    ipaddr=str(netaddr.ip.IPAddress(i))
                    break
            ipaddrs[name]=ipaddr
            j.application.config.setDict("lxc.mgmt.ipaddresses",ipaddrs)

        # mgmtiprange=j.application.config.get("lxc.management.iprange")
        self.networkSet( name,netname="mgmt0", bridge="lxc", pubips=["%s/24"%ipaddr]) #@todo make sure other ranges also supported

        #set ipaddr in hrd file
        hrd.set("ipaddr",ipaddr)

        if start:
            return self.start(name)
        self.setHostName(name)
        self.pushSSHKey(name)

        return self.getIp(name)

    def setHostName(self,name):
        lines=j.system.fs.fileGetContents("/etc/hosts")
        out=""
        for line in lines.split("\n"):
            if line.find(name)<>-1:
                continue
            out+="%s\n"%line
        out+="%s      %s\n"%(self.getIp(name),name)
        j.system.fs.writeFile(filename="/etc/hosts",contents=out)
        
    def pushSSHKey(self,name):
        path=j.system.fs.joinPaths(self._get_rootpath(name),"root",".ssh","authorized_keys")
        content=j.system.fs.fileGetContents("/root/.ssh/id_dsa.pub")
        j.system.fs.writeFile(filename=path,contents="%s\n"%content)
        path=j.system.fs.joinPaths(self._get_rootpath(name),"root",".ssh","known_hosts")
        j.system.fs.writeFile(filename=path,contents="")

    def destroyAll(self):
        running,stopped=self.list()
        alll=running+stopped
        for item in alll:
            self.destroy(item)

    def destroy(self,name):
        running,stopped=self.list()
        alll=running+stopped
        print "running:%s"%",".join(running)
        print "stopped:%s"%",".join(stopped)
        if name in running:            
            # cmd="lxc-destroy -n %s%s -f"%(self._prefix,name)
            cmd="lxc-kill -P %s -n %s%s"%(self.basepath,self._prefix,name)
            self.execute(cmd)
        while name in running:
            running,stopped=self.list()
            time.sleep(0.1)
            print "wait stop"
            alll=running+stopped

        self.btrfsSubvolDelete(name)
        # #@todo put timeout in
             
    def stop(self,name):
        # cmd="lxc-stop -n %s%s"%(self._prefix,name)
        cmd="lxc-stop -P %s -n %s%s"%(self.basepath,self._prefix,name)
        self.execute(cmd)

    def start(self,name,stdout=True,test=True):
        print "start:%s"%name
        cmd="lxc-start -d -P %s -n %s%s"%(self.basepath,self._prefix,name)
        print cmd
        # cmd="lxc-start -d -n %s%s"%(self._prefix,name)
        self.execute(cmd)
        start=time.time()
        now=start
        found=False
        while now<start+20:
            running=self.list()[0]
            if name in running:
                found=True
                break
            time.sleep(0.2)
            now=time.time()

        if found==False:
            msg= "could not start new machine, did not start in 20 sec."
            if stdout:
                print msg
            raise RuntimeError(msg)
    
        self.setHostName(name)

        ipaddr=self.getIp(name)
        print "test ssh access to %s"%ipaddr
        timeout=time.time()+10        
        while time.time()<timeout:  
            if j.system.net.tcpPortConnectionTest(ipaddr,22):
                return
            time.sleep(0.1)
        raise RuntimeError("Could not connect to machine %s over port 22 (ssh)"%ipaddr)

    def networkSet(self, machinename,netname="pub0",pubips=[],bridge="public",gateway=None):
        bridge=bridge.lower()
        print "set pub network %s on %s" %(pubips,machinename)
        machine_cfg_file = j.system.fs.joinPaths(self.basepath, '%s%s' % (self._prefix, machinename), 'config')
        machine_ovs_file = j.system.fs.joinPaths(self.basepath, '%s%s' % (self._prefix, machinename), 'ovsbr_%s'%bridge)
        
        # mgmt = j.application.config.get('lxc.mgmt.ip')
        # netaddr.IPNetwork(mgmt)

        config = '''
lxc.network.type = veth
lxc.network.flags = up
#lxc.network.veth.pair = %s_%s
lxc.network.name = %s
lxc.network.script.up = $basedir/%s/ovsbr_%s
lxc.network.script.down = $basedir/%s/ovsbr_%s
'''  % (machinename,netname,netname,machinename,bridge,machinename,bridge)
        config=config.replace("$basedir",self.basepath)

        Covs="""
#!/bin/bash
if [ "$3" = "up" ] ; then
/usr/bin/ovs-vsctl --may-exist add-port %s $5
else
/usr/bin/ovs-vsctl --if-exists del-port %s $5
fi        
""" % (bridge,bridge)

        j.system.fs.writeFile(filename=machine_ovs_file,contents=Covs)

        j.system.unix.chmod(machine_ovs_file, 0755)

        ed=j.codetools.getTextFileEditor(machine_cfg_file)
        ed.setSection(netname,config)

        j.system.netconfig.setRoot(self._get_rootpath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in pubips:        
            j.system.netconfig.enableInterfaceStatic(dev=netname,ipaddr=ipaddr,gw=gateway,start=False)#do never start because is for lxc container, we only want to manipulate config
        j.system.netconfig.root=""#set back to normal


    def networkSetPrivateVXLan(self, name, vxlanid, ipaddresses):
        raise RuntimeError("not implemented")

    def _setConfig(self,name,parent):
        print "SET CONFIG"
        base=self._getMachinePath(name)
        baseparent=self._getMachinePath(parent)
        machine_cfg_file = self._getMachinePath(name,'config')
        C="""
lxc.tty = 4
lxc.pts = 1024
lxc.arch = x86_64
lxc.cgroup.devices.deny = a
lxc.cgroup.devices.allow = c *:* m
lxc.cgroup.devices.allow = b *:* m
lxc.cgroup.devices.allow = c 1:3 rwm
lxc.cgroup.devices.allow = c 1:5 rwm
lxc.cgroup.devices.allow = c 5:1 rwm
lxc.cgroup.devices.allow = c 5:0 rwm
lxc.cgroup.devices.allow = c 1:9 rwm
lxc.cgroup.devices.allow = c 1:8 rwm
lxc.cgroup.devices.allow = c 136:* rwm
lxc.cgroup.devices.allow = c 5:2 rwm
lxc.cgroup.devices.allow = c 254:0 rm
lxc.cgroup.devices.allow = c 10:229 rwm
lxc.cgroup.devices.allow = c 10:200 rwm
lxc.cgroup.devices.allow = c 1:7 rwm
lxc.cgroup.devices.allow = c 10:228 rwm
lxc.cgroup.devices.allow = c 10:232 rwm
lxc.utsname = $name
lxc.cap.drop = sys_module
lxc.cap.drop = mac_admin
lxc.cap.drop = mac_override
lxc.cap.drop = sys_time
lxc.hook.clone = /usr/share/lxc/hooks/ubuntu-cloud-prep
#lxc.rootfs = overlayfs:$baseparent/rootfs:$base/delta0
lxc.rootfs = $base/rootfs
lxc.pivotdir = lxc_putold

#lxc.mount.entry=/var/lib/lxc/jumpscale $base/rootfs/jumpscale none defaults,bind 0 0
#lxc.mount.entry=/var/lib/lxc/shared $base/rootfs/shared none defaults,bind 0 0
lxc.mount = $base/fstab
"""        
        C=C.replace("$name",name)    
        C=C.replace("$baseparent",baseparent)
        C=C.replace("$base",base)
        j.system.fs.writeFile(machine_cfg_file,C)
        # j.system.fs.createDir("%s/delta0/jumpscale"%base)
        # j.system.fs.createDir("%s/delta0/shared"%base)
        

