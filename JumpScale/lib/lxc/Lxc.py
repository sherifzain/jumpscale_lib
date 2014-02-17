#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os
import JumpScale.baselib.netconfig
import netaddr

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


    def resetNetworkConfigHostSystemDhcpSimple(self,nameserver=None,pubinterface="eth0"):
        """
        works on host 
        will remove all network config (DANGEROUS)
        will put pubinterface on dhcp
        will create bridge linked to pub interface with specified privnet
        gw will be applied
        """
        if not nameserver:
            nameserver=j.application.config.get("lxc.nameserver")

        mgmtnet = netaddr.IPNetwork(j.application.config.get("lxc.management.iprange"))
        mgmtbridge=j.application.config.get("lxc.bridge.management")

        j.system.netconfig.reset(shutdown=True)        
        j.system.netconfig.setNameserver(nameserver)
        j.system.netconfig.enableInterface(pubinterface,start=False,dhcp=False)
        j.system.netconfig.enableInterfaceBridgeDhcp(mgmtbridge,bridgedev=pubinterface,start=True)

        #look for first ip addr of network
        ip=netaddr.IPNetwork(mgmtnet)

        mgmtnetIpAddr=str(netaddr.ip.IPAddress(ip.first+1))

        mgmtnet="%s/%s"%(mgmtnetIpAddr,ip.prefixlen)

        j.system.netconfig.addIpToInterface(mgmtbridge,mgmtnet,aliasnr=1,start=True)    

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
        hrd=self.getConfig(name)
        return hrd.get("ipaddr")

    def getConfig(self,name):
        configpath=j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, name),"jumpscaleconfig.hrd")
        if not j.system.fs.exists(path=configpath):
            content="""
ipaddr=
"""
            j.system.fs.writeFile(configpath,contents=content)
        return j.core.hrd.getHRD( path=configpath)

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
            nameserver = j.application.config.get('lxc.nameserver')        
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

        hrd=self.getConfig(name)
        ipaddrs=j.application.config.getDict("lxc.management.ipaddr")
        if ipaddrs.has_key(name):
            ipaddr=ipaddrs[name]
        else:
            #find free ip addr
            import netaddr
            
            existing=[netaddr.ip.IPAddress(item).value for item in  ipaddrs.itervalues() if item.strip()<>""]
            ip = netaddr.IPNetwork(j.application.config.get("lxc.management.iprange"))
            for i in range(ip.first+2,ip.last-2):
                if i not in existing:
                    ipaddr=str(netaddr.ip.IPAddress(i))
                    break
            ipaddrs[name]=ipaddr
            j.application.config.setDict("lxc.management.ipaddr",ipaddrs)

        mgmtbridge=j.application.config.get("lxc.bridge.management")
        # mgmtiprange=j.application.config.get("lxc.management.iprange")
        self.networkSetPrivateOnBridge( name,netname="mgmt0", bridge=mgmtbridge, ipaddresses=["%s/24"%ipaddr]) #@todo make sure other ranges also supported

        #set ipaddr in hrd file
        hrd.set("ipaddr",ipaddr)

        if start:
            return self.start(name)

        return self.getIp(name)
        
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

    def start(self,name,stdout=True):
        print "start:%s"%name
        cmd="lxc-start -d -n %s%s"%(self._prefix,name)
        resultcode,out=j.system.process.execute(cmd)
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

    def networkSetPublic(self, machinename,netname="pub0",pubips=[],bridge=None,gateway=None):
        print "set pub network %s on %s" %(pubips,machinename)
        machine_cfg_file = j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, machinename), 'config')
        
        if not bridge:
            bridge = j.application.config.get('lxc.bridge.public')
        if not gateway:
            gateway = j.application.config.get('lxc.bridge.public.gw')
            if gateway=="":
                gateway=None

        config = '''
lxc.network.type = veth
lxc.network.flags = up
lxc.network.link = %s
lxc.network.name = %s
'''  % (bridge, netname)

#         notused="""
# #lxc.network.hwaddr = 00:FF:12:34:52:79
# #lxc.network.ipv4 = 192.168.22.1/24
# #lxc.network.ipv4.gateway = 192.168.22.254
# """

        ed=j.codetools.getTextFileEditor(machine_cfg_file)
        ed.setSection(netname,config)        

        #do not do will configure in fs of root of clone
        # for pubip in pubips:
        #     config += '''lxc.network.ipv4 = %s\n''' % pubip

        j.system.netconfig.setRoot(self._get_rootpath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in pubips:        
            j.system.netconfig.enableInterfaceStatic(dev=netname,ipaddr=ipaddr,gw=gateway,start=False)#do never start because is for lxc container, we only want to manipulate config
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

        if not bridge:
            bridge = j.application.config.get('lxc.bridge.public')        

        j.system.netconfig.setRoot(self._get_rootpath(machinename)) #makes sure the network config is done on right spot
        for ipaddr in ipaddresses:        
            j.system.netconfig.enableInterfaceBridgeStatic(dev=netname,ipaddr=ipaddr,bridgedev=bridge,gw=None,start=False)
        j.system.netconfig.root=""#set back to normal


    def networkSetPrivateVXLan(self, name, vxlanid, ipaddresses):
        raise RuntimeError("not implemented")
