#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os
import JumpScale.baselib.netconfig

class Lxc():

    def __init__(self):
        self._prefix="mach_"

    def _getChildren(self,pid,children):
        process=j.system.process.getProcessObject(pid)
        children.append(process)
        for child in process.get_children():
            children=self._getChildren(child.pid,children)
        return children

    def _get_rootpath(self,name):
        rootpath=j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, name), 'delta0')
        return rootpath

    def resetNetworkConfigSystemDhcpSimple(self,nameserver=None,pubinterface="eth0",privnet="192.168.30.254/24",gateway=None,bridgename=None):
        """
        will remove all network config (DANGEROUS)
        will put pubinterface on dhcp
        will create bridge linked to pub interface with specified privnet
        gw will be applied
        """
        if not nameserver:
            raise RuntimeError("Need to provide nameserver")
        if not bridgename:
            bridgename = j.application.config.get('lxc.bridge.public')
        if not gateway:
            gateway = j.application.config.get('lxc.gateway.public')

        j.system.netconfig.reset(shutdown=True)        
        j.system.netconfig.setNameserver(nameserver)
        j.system.netconfig.enableDhcpInterface(pubinterface,start=True)
        j.system.netconfig.addIpaddrStaticBridge(bridgename,privnet,gateway,pubinterface,start=True)

    def list(self):
        """
        names of running & stopped machines
        @return (running,stopped)
        """
        cmd="lxc-ls --fancy"
        resultcode,out=j.system.process.execute(cmd)

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
        cmd="lxc-ls --fancy --fancy-format name,ipv4 --running"
        resultcode,out=j.system.process.execute(cmd)
        lxcname="%s%s"%(self._prefix,name)
        for line in out.splitlines():
            lineparts = line.strip().split()
            if len(lineparts) == 2 and lineparts[0] == lxcname:
                ip = lineparts[1]
                if ip == '-':
                    if fail:
                        raise RuntimeError('Machine is not running but has no IP')
                    else:
                        ip = None
                return ip
        if fail:
            raise RuntimeError("machine %s not found"%name)
        else:
            return None

    def getPid(self,name,fail=True):
        resultcode,out=j.system.process.execute("lxc-info -n %s%s -p"%(self._prefix,name))
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

    def create(self,name="",stdout=True,base="base",start=False,nameserver=None):
        """
        @param name if "" then will be an incremental nr
        """
        print "create:%s"%name
        if not nameserver:
            nameserver = j.application.config.get('lxc.bridge.nameserver')        
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
        cmd="lxc-clone --snapshot -B overlayfs -o %s -n %s"%(base,lxcname)
        resultcode,out=j.system.process.execute(cmd)
        j.system.netconfig.setRoot(self._get_rootpath(name)) #makes sure the network config is done on right spot
        j.system.netconfig.reset()
        j.system.netconfig.setNameserver(nameserver)
        j.system.netconfig.root=""#set back to normal
        if start:
            return self.start(name)
        
    def destroyAll(self):
        running,stopped=self.list()
        alll=running+stopped
        for item in alll:
            self.destroy(item)

    def destroy(self,name):
        running,stopped=self.list()
        alll=running+stopped
        if name in alll:
            cmd="lxc-destroy -n %s%s -f"%(self._prefix,name)
            resultcode,out=j.system.process.execute(cmd)
        #@todo put timeout in
        while name in alll:
            running,stopped=self.list()
            alll=running+stopped
        
    def stop(self,name):
        cmd="lxc-stop -n %s%s"%(self._prefix,name)
        resultcode,out=j.system.process.execute(cmd)

    def start(self,name):
        print "start:%s"%name
        cmd="lxc-start -d -n %s%s"%(self._prefix,name)
        resultcode,out=j.system.process.execute(cmd)
        start=time.time()
        now=start
        while now<start+10:
            ip=self.getIp(name,fail=False)
            if ip:
                break
            time.sleep(0.2)
            now=time.time()
        if ip=="":
            msg= "could not start new machine, ipaddress not found."
            if stdout:
                print msg
            raise RuntimeError(msg)
        if stdout:
            print "ip:%s"%ip
        return ip

    def networkSetPublic(self, machinename,netname="pub0",pubips=[],bridge=None,gateway=None):
        print "set pub network %s on %s" %(pubips,machinename)
        machine_cfg_file = j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, machinename), 'config')
        
        if not bridge:
            bridge = j.application.config.get('lxc.bridge.public')
        if not gateway:
            gateway = j.application.config.get('lxc.gateway.public')

        config = '''
lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = %s
lxc.network.name = %s
#lxc.network.hwaddr = 00:FF:12:34:52:79
#lxc.network.ipv4 = 192.168.22.1/24
#lxc.network.ipv4.gateway = 192.168.22.254
'''  % (bridge, netname)

        ed=j.codetools.getTextFileEditor(machine_cfg_file)
        ed.setSection(netname,config)        

        #do not do will configure in fs of root of clone
        # for pubip in pubips:
        #     config += '''lxc.network.ipv4 = %s\n''' % pubip

        j.system.netconfig.setRoot(self._get_rootpath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in pubips:        
            j.system.netconfig.addIpaddrStatic(dev=netname,ipaddr=ipaddr,gw=gateway,start=False)#do never start because is for lxc container, we only want to manipulate config
        j.system.netconfig.root=""#set back to normal



    def networkSetPrivateOnBridge(self, machinename,netname="dmz0", bridge=None, ipaddresses=["192.168.30.20/24"]):
        print "set private network %s on %s" %(ipaddresses,machinename)
        machine_cfg_file = j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, machinename), 'config')
        
        config = '''
lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = %s
lxc.network.name = %s
'''  % (bridge, netname)

        ed=j.codetools.getTextFileEditor(machine_cfg_file)
        ed.setSection(netname,config)

        j.system.netconfig.setRoot(self._get_rootpath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in ipaddresses:        
            j.system.netconfig.addIpaddrStatic(dev=netname,ipaddr=ipaddr,gw=None,start=False)
        j.system.netconfig.root=""#set back to normal


    def networkSetPrivateVXLan(self, name, vxlanid, ipaddresses):
        raise RuntimeError("not implemented")
