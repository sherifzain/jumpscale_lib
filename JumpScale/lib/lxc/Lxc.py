#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os

class Lxc():

    def __init__(self):
        self._prefix="mach_"

    def _getChildren(self,pid,children):
        process=j.system.process.getProcessObject(pid)
        children.append(process)
        for child in process.get_children():
            children=self._getChildren(child.pid,children)
        return children

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

    def createMachine(self,name="",stdout=True,base="base"):
        """
        @param name if "" then will be an incremental nr
        """
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
        cmd="lxc-start -d -n %s"% lxcname
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
            msg= "could not create new machine, ipaddress not found."
            if stdout:
                print msg
            raise RuntimeError(msg)
        if stdout:
            print "ip:%s"%ip
        return ip

    def destroyAll(self):
        running,stopped=self.list()
        alll=running+stopped
        for item in alll:
            self.destroy(item)

    def destroy(self,name):
        cmd="lxc-destroy -n %s%s -f"%(self._prefix,name)
        resultcode,out=j.system.process.execute(cmd)

    def stop(self,name):
        cmd="lxc-stop -n %s%s"%(self._prefix,name)
        resultcode,out=j.system.process.execute(cmd)

    def start(self,name):
        cmd="lxc-start -d -n %s%s"%(self._prefix,name)
        resultcode,out=j.system.process.execute(cmd)

    def networkSetPublic(self, name, pubips):
        machine_cfg_file = j.system.fs.joinPaths('/var', 'lib', 'lxc', '%s%s' % (self._prefix, name), 'config')
        bridge = j.application.config.get('lxc.bridge.public')
        gateway = j.application.config.get('lxc.gateway.public')
        config = '''
        ### ADDED BY networkSetPublic ###
        lxc.network.type = veth
        lxc.network.flags = up
        lxc.network.link = %s
        '''  % bridge

        for pubip in pubips:
            config += '''lxc.network.ipv4 = %s
            lxc.network.ipv4.gateway = %s
            ''' % (pubip, gateway)

        config += '''
        ### END networkSetPublic ###
        '''

        j.system.fs.writeFile(machine_cfg_file, config, True)

    def networkSetPrivateVXLan(self, name, vxlanid, ipaddresses):
        pass
