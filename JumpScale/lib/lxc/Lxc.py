#!/usr/bin/env python
from JumpScale import j
import sys,time
import JumpScale.lib.diskmanager
import os

class Lxc():

    def __init__(self):
        self.prefix="mach_"

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
        cmd="lxc-list"
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
            if name.find(self.prefix)==0:
                name=name.replace(self.prefix,"")
                current.append(int(name))
        running.sort()
        stopped.sort()
        return (running,stopped)

    def getip(self,name,fail=True):
        cmd="lxc-list"
        resultcode,out=j.system.process.execute(cmd)
        name="%s%s"%(self.prefix,name)
        stopped = []
        running = []
        current = None
        for line in out.split("\n"):
            line = line.strip()
            if line.find(name)==0:
                print "machine found"
                if line.find("RUNNING")==-1:                
                    if fail:
                        print "machine not running,so ip could not be found"
                        j.application.stop(1)
                    else:
                        return ""
                print "machine running"
                line=line.split("RUNNING")[1]
                ip=line.split("-")[0].strip()
                return ip
        if fail:
            print "machine %s not found"%name
            j.application.stop(1)
        else:
            return ""

    def getpid(self,name,fail=True):
        resultcode,out=j.system.process.execute("lxc-info -n %s%s"%(self.prefix,name))
        state=None
        pid=0
        for line in out.split("\n"):
            line=line.strip().lower()
            if line=="":
                continue
            if line.find("state")==0:
                state=line.split(":")[1].strip()
            if state=="running" and line.find("pid")==0:
                pid=int(line.split(":")[1].strip())
        if pid==0:
            print "machine:%s is not running"%name
            if fail:
                j.application.stop(1)
            else:
                return 0
        return pid

    def getProcessList(self,name,stdout = True):
        """
        @return [["$name",$pid,$mem,$parent],....,[$mem,$cpu]]
        last one is sum of mem & cpu
        """
        pid = self.getpid(name)
        children=[]
        children=self._getChildren(pid,children)
        result=[]
        pre=""
        mem=0.0
        cpu=0.0
        cpu0=0.0
        prevparent=""
        for child in children:
            if child.parent.name<>prevparent:
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
            m=0#max
            for nr in machines:
                if j.basetype.integer.check(nr):
                    if nr>m:
                        m=nr
            m=m+1
            name=m
        name="%s%s"%(self.prefix,name)
        cmd="lxc-clone --snapshot -B overlayfs -o %s -n %s"%(base,name)
        resultcode,out=j.system.process.execute(cmd)
        cmd="lxc-start -d -n %s"%name
        resultcode,out=j.system.process.execute(cmd)
        start=time.time()
        now=start
        while now<start+10:    
            ip=self.getip(m,fail=False)
            if ip<>"":
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

    def destroyall(self):
        running,stopped=self.list()
        alll=running+stopped
        for item in alll:
            cmd="lxc-destroy -n %s%s -f"%(self.prefix,item)
            resultcode,out=j.system.process.execute(cmd)

    def destroy(self,name):
        cmd="lxc-destroy -n %s%s -f"%(self.prefix,name)
        resultcode,out=j.system.process.execute(cmd)

    def stop(self,name):
        cmd="lxc-stop -n %s%s"%(self.prefix,name)
        resultcode,out=j.system.process.execute(cmd)

    def start(self,name):
        cmd="lxc-start -n %s%s"%(self.prefix,name)
        resultcode,out=j.system.process.execute(cmd)



            

                    



        