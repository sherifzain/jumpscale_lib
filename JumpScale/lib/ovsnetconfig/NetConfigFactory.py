#!/usr/bin/env python
from JumpScale import j

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

    def newVXlan(self,networkid):
        vxlan = netcl.VXlan(netcl.NetID(networkid))
        vxlan.create()
        return vxlan.name

    def getType(self,interfaceName):
        layout=self.getConfigFromSystem()
        if not layout.has_key(interfaceName):
            raise RuntimeError("cannot find interface %s"%interfaceName)
        interf=layout[interfaceName]        
        if interf["params"].has_key("type"):
            return interf["params"]["type"]
        return None
        





    

