#!/usr/bin/env python
from JumpScale import j
import netaddr
import VXNet.vxlan as vxlan
from netaddr import *
import VXNet.netclasses as netcl
from VXNet.utils import *

class NetConfigFactory():

    def __init__(self):
        self._layout=None


    def getConfigFromSystem(self,reload=False):
        """
        walk over system and get configuration, result is dict
        """
        if self._layout==None or reload:
            self._layout=vxlan.NetLayout()
            self._layout.load()
        # add_ips_to(self._layout)  #@todo fix
        return self._layout.nicdetail

    def _exec(self,cmd,failOnError=True):
        print cmd
        rc,out=j.system.process.execute(cmd,dieOnNonZeroExitCode=failOnError)        
        return out
        

    def removeOldConfig(self):
        cmd="brctl show"
        for line in self._exec(cmd).split("\n"):
            if line.strip()=="" or line.find("bridge name")<>-1:
                continue
            name=line.split("\t")[0]
            self._exec("ip link set %s down"%name)
            self._exec("brctl delbr %s"%name)

        for intname,data in self.getConfigFromSystem(reload=True).iteritems():
            if "PHYS" in data["detail"]:
                continue
            if intname =="ovs-system":
                continue
            self._exec("ovs-vsctl del-br %s"%intname,False)

        out=self._exec("virsh net-list")
        state="start"
        for line in out.split("\n"):
            if state=="found":
                if line.strip()=="":
                    continue
                line=line.replace("\t"," ")
                name=line.split(" ")[0]
                self._exec("virsh net-destroy %s"%name,False)
                self._exec("virsh net-undefine %s"%name,False)

            if line.find("----")<>-1:
                state="found"

        j.system.fs.writeFile(filename="/etc/default/lxc-net",contents="USE_LXC_BRIDGE=\"false\"",append=True) #@todo UGLY use editor !!!

        self.getConfigFromSystem(reload=True)

        j.system.fs.writeFile(filename="/etc/network/interfaces",contents="auto lo\n iface lo inet loopback\n\n")

    def printConfigFromSystem(self):
        pprint_dict(self.getConfigFromSystem())

    def newBridge(self,name,interface=None):
        """
        @param interface interface where to connect this bridge to
        """
        br=netcl.Bridge(name)
        br.create()
        if interface is not None:
            br.connect(interface)

    def newVlanBridge(self, name, parentbridge, vlanid):
        br = netcl.Bridge(name)
        br.create()
        addVlanPair(parentbridge, name, vlanid)

    def ensureVXNet(self, networkid):
        vxnet = vxlan.VXNet(netcl.NetID(networkid))
        vxnet.inbridge = True
        vxnet.apply()
        return vxnet
        

    def getType(self,interfaceName):
        layout=self.getConfigFromSystem()
        if not layout.has_key(interfaceName):
            raise RuntimeError("cannot find interface %s"%interfaceName)
        interf=layout[interfaceName]        
        if interf["params"].has_key("type"):
            return interf["params"]["type"]
        return None
        
    def setBackplaneDhcp(self,interfacename="eth0",backplaneId=1):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto Backplane$id
allow-ovs Backplane1
iface Backplane$id inet dhcp
 dns-nameserver 8.8.8.8 8.8.4.4
 ovs_type OVSBridge
 ovs_ports $iname

allow-Backplane$id $iname
iface $iname inet manual
 ovs_bridge Backplane1
 ovs_type OVSPort
"""
        C=C.replace("$id", str(backplaneId))
        C=C.replace("$iname", interfacename)

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(interfacename,C)

    def setBackplane(self,interfacename="eth0",backplaneId=1,ipaddr="192.168.10.10/24",gw=""):
        """
        DANGEROUS, will remove old configuration
        """
        C="""
auto Backplane$id
allow-ovs Backplane1
iface Backplane$id inet static
 address $ipbase 
 netmask $mask
 dns-nameserver 8.8.8.8 8.8.4.4
 ovs_type OVSBridge
 ovs_ports $iname
 $gw

allow-Backplane$id $iname
iface $iname inet manual
 ovs_bridge Backplane1
 ovs_type OVSPort
"""
        n=netaddr.IPNetwork(ipaddr)

        C=C.replace("$id", str(backplaneId))
        C=C.replace("$iname", interfacename)
        C=C.replace("$ipbase", str(n.ip))
        C=C.replace("$mask", str(n.netmask))
        if gw<>"" and gw<>None:
            C=C.replace("$gw", "gateway %s"%gw)
        else:
            C=C.replace("$gw", "")

        ed=j.codetools.getTextFileEditor("/etc/network/interfaces")
        ed.setSection(interfacename,C)
        ed.save()

    def applyconfig(self,interfacenameToExclude=None):
        """
        DANGEROUS, will remove old configuration
        """
        for intname,data in self.getConfigFromSystem(reload=True).iteritems():
            if "PHYS" in data["detail"] and intname<>interfacenameToExclude:
                self._exec("ip link set %s down"%intname,False)
        
        self._exec("ifdown Backplane%s"%backplaneId, failOnError=False)
        self._exec("ifup Backplane%s"%backplaneId, failOnError=True)

        #@todo need to do more checks here that it came up and retry couple of times if it did not
        #@ can do this by investigating self.getConfigFromSystem

        print self._exec("ovs-vsctl show", failOnError=True)


    

