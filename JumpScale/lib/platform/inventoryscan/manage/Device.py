# <License type="Sun Cloud BSD" version="2.2">
#
# Copyright (c) 2005-2009, Sun Microsystems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name Sun Microsystems, Inc. nor the names of other
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SUN MICROSYSTEMS, INC. "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SUN MICROSYSTEMS, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

from JumpScale import j
from JumpScale.core.baseclasses.CMDBObject import CMDBObject

import DevicePerformance
import DeviceOperatingSystem
import DeviceHypervisor


class Device(CMDBObject):

    """
    Simplified database representation of a hardware inventory of a device
    """

    cmdbtypename = 'deviceInventory'

    name = j.basetype.string(doc="device host name", flag_dirty=True)
    disks = j.basetype.dictionary(doc="list of hard disks present in the device", allow_none=True)
    nics = j.basetype.dictionary(doc="list of network interface cards present in the device", allow_none=True)
    totalMemoryInMB = j.basetype.integer(doc="total mb of RAM present in the device", allow_none=False, default=0)
    numberOfCPUs = j.basetype.integer(doc="number of cpu's present in the device", allow_none=False, default=0)
    numberOfCPUCores = j.basetype.integer(doc="number of cpu cores present in the device", allow_none=False, default=0)
    totalCPUFrequency = j.basetype.integer(doc="sum of cpu frequencies provided by all cpu cores present in the device", allow_none=False, default=0)
    pCIBusComponents = j.basetype.list(doc="List of PCI bus components", flag_dirty=True, allow_none=True, default=list())
    iSCSIInitiators = j.basetype.list(doc="List of ISCSI initiators", flag_dirty=True, allow_none=True, default=list())
    iSCSITargets = j.basetype.list(doc="List of ISCSI targets", flag_dirty=True, allow_none=True, default=list())
    zFSList = j.basetype.list(doc="List of ZFileSystems", flag_dirty=True, allow_none=True, default=list())
    zPoolList = j.basetype.list(doc="List of ZPools", flag_dirty=True, allow_none=True, default=list())
    performance = j.basetype.object(
        DevicePerformance.DevicePerformance, doc="Device Performance data", flag_dirty=True, allow_none=True, default=None)
    os = j.basetype.object(
        DeviceOperatingSystem.DeviceOperatingSystem, doc="Device operating system data", flag_dirty=True, allow_none=True, default=None)
    hypervisor = j.basetype.object(
        DeviceHypervisor.DeviceHypervisor, doc="Device hypervisor type, vmachines data", flag_dirty=True, allow_none=True, default=None)
    # cpu addressing 32bit <-> 64 bit?

    def __init__(self):
        CMDBObject.__init__(self)
        if not self.performance:
            self.performance = DevicePerformance.DevicePerformance()
        if not self.os:
            self.os = DeviceOperatingSystem.DeviceOperatingSystem()
        if not self.hypervisor:
            self.hypervisor = DeviceHypervisor.DeviceHypervisor()

    def __repr__(self):
        variables = ('name', 'disks', 'nics', 'totalMemoryInMB', 'numberOfCPUs', 'numberOfCPUCores', 'totalCPUFrequency', 'performance', 'os')
        return str(dict((key, getattr(self, key)) for key in variables))

    def __str__(self):
        return self.__repr__()
