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
from JumpScale.core.baseclasses.ManagementConfiguration import ManagementConfiguration
from JumpScale.core.baseclasses.ManagementApplication import CMDBLockMixin

import time
import re

from Device import Device
from Nic import Nic
from Disk import Disk
from Partition import Partition
from PartitionRaid import PartitionRaid
import ZFS
import ZPool
import ISCSIInitiator
import ISCSITarget
import ZPoolMirror
import ZPoolDisk
import DeviceHypervisor


class InventoryManager(ManagementConfiguration, CMDBLockMixin):

    """
    Exposes methods to retrieve machine info (CPU, mem, zfs, iscsi, ...)

    Methods return references to cmdb object/subObjects, it is the responsibility of the caller code to make sure to create copies of those collection in case the caller code would alter them.
    """

    cmdb = Device()
    name = "InventoryManager"

    def save(self):
        """
        If configuration not dirty (i.e. configuration is in sync with cmdb), then
        return. Otherwise save the configuration in the cmdb and clear the dirty flag
        """
        if self.cmdb.isDirty:
            self.cmdb.dirtyProperties.clear()
            self.cmdb.save()

    def scanDeviceResources(self):
        """
        Runs a full device resource scanning, update cmdb
        """
        self.startChanges()
        self.getCPUInfo()
        self.getDisks()
        self.getMemoryInfo()
        self.getNics()
        self.getZFSs()
        self.getZPools()
        self.getISCSIInitiators()
        self.getISCSITargets()
        self.getPCIBusComponents()
        self.getPerformanceInfo()
        self.getOperatingSystemInfo()
        self.getZPoolMirrorInfo()
        try:
            self.getHypervisorType()
        except RuntimeError as ex:
            pass  # that exception is already logged and most probably means there is no hypervisor installed on machine
        self.getVMachinesStatistics()
        self.getNetworkStatistics()
        self.getVMachinesNetworkStatistics()
        self.save()

    def printDeviceResources(self):
        """
        If a scan is already done, just pretty prints the resources, otherwise print empty section headers and log an error
        """
        print self.cmdb

    def getDisks(self):
        """
        Enumerate all the disks present on the system, updating the cmdb object accordingly

        Create a disk instance for each disk on the system, populate the attributes and add it to the cmdb's hardDisks collection
        @return: cmdb.hardDisks
        """
        disks = j.cloud.cmdtools.inventoryScan.getDisks()
        currentAvailableDisks = list()
        for name, value in disks.iteritems():
            size = int(float(value['size']) * 1024) if value['unit'] == 'GB' else int(float(value['size']))
            partitions = value['partitions']
            currentAvailableDisks.append(name)
            if name in self.cmdb.disks.keys():
                self.cmdb.disks[name].name = name
                self.cmdb.disks[name].size = size
            else:
                disk = Disk()
                disk.name = name
                disk.size = size
                self.cmdb.disks[name] = disk
            if partitions:
                disk = self.cmdb.disks[name]
                disk.partitions = list()
                for part in partitions:
                    partition = Partition(part['Type'],
                                          part['number'],
                                          part['start'],
                                          part['end'],
                                          int(float(part['size'][0:-3])),
                                          part['mountpoint'] if 'mountpoint' in part else '',
                                          part['used'] if 'used' in part else 0.0,
                                          part['name'] if 'name' in part else '',
                                          part['flag'] if 'flag' in part else '')
                    if 'devices' in part:
                        partition.raid = PartitionRaid(part['level'], part['state'], part['devices'], part['activeDevices'],
                                                       part['failedDevices'], part['totalDevices'], part['raidDevices'],
                                                       part['spareDevices'], part['backendsize'])
                    disk.partitions.append(partition)

        for disk in self.cmdb.disks.keys():
            if disk not in currentAvailableDisks:
                del self.cmdb.disks[disk]
        self.cmdb.dirtyProperties.add('disks')
        return disks

    def getNics(self):
        """
        Enumerate all the NICs present on the system, updating the cmdb object accordingly

        Create a Nic instance for each NIC on the system, populate the attributes and add it to the cmdb's networkInterfaceCards collection
        @return: cmdb.networkInterfaceCards
        """
        nICs = j.cloud.cmdtools.inventoryScan.getNics()
        currentAvailableNICs = list()
        # append added NICs to cmdb object
        for interface, mAC, nICType in nICs:
            currentAvailableNICs.append(interface)
            if interface in self.cmdb.nics.keys():
                self.cmdb.nics[interface].name = interface
                self.cmdb.nics[interface].macAddress = mAC
                self.cmdb.nics[interface].nicType = nICType
            else:
                nIC = Nic()
                nIC.name = interface
                nIC.macAddress = mAC
                nIC.nicType = nICType
                self.cmdb.nics[interface] = nIC
        # remove removed Nics from cmdb object
        for nIC in self.cmdb.nics.keys():
            if nIC not in currentAvailableNICs:
                del self.cmdb.nics[nIC]
        self.cmdb.dirtyProperties.add('nics')
        return tuple(self.cmdb.nics)

    def getMemoryInfo(self):
        """
        Calculates total mb of RAM present in the device, updating the cmdb object accordingly

        @return cmdb.totalMemoryInMB
        """
        memory = j.cloud.cmdtools.inventoryScan.getMemoryInfo()
        self.cmdb.totalMemoryInMB = memory
        return memory

    def getCPUInfo(self):
        """
        Calculates numberOfCpus, numberOfCpuCores, totalCpuFrequency processing power present in the device, updating the cmdb object accordingly

        @rtype: tuple
        @return (numberOfCpus, numberOfCpuCores, totalCpuFrequency)
        """
        output = j.cloud.cmdtools.inventoryScan.getCPUInfo()
        self.cmdb.numberOfCPUs, self.cmdb.numberOfCPUCores, self.cmdb.totalCPUFrequency = output
        return output

    def getZFSs(self):
        """
        Retrieve ZFilesystems installed on the system
        """

        result = dict()
        try:
            result = j.cloud.cmdtools.inventoryScan.getZFS()
            self.cmdb.zFSList = list()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            # do not interrupt the call flow, simply log the exception as it can be Operation Not Supported on this platform
        else:
            for key in result.keys():
                zfs = ZFS.ZFS()
                data = result[key]
                zfs.name = key
                zfs.mountPoint = data['mountpoint']
                zfs.availableSize = data['avail']
                zfs.used = data['used']
                zfs.refer = data['refer']
                self.cmdb.zFSList.append(zfs)
            return tuple(self.cmdb.zFSList)

    def getZPools(self):
        """
        Retrieves Zpools installed on the system
        """
        result = dict()
        try:
            result = j.cloud.cmdtools.inventoryScan.getZPoolsInfo()
            self.cmdb.zPoolList = list()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
        else:
            for key in result.keys():
                zPool = ZPool.ZPool()
                data = result[key]
                zPool.name = key
                zPool.CAP = data['CAP']
                zPool.availableSize = data['avialableSize']
                zPool.used = data['used']
                zPool.size = data['size']
                zPool.health = data['health']
                self.cmdb.zPoolList.append(zPool)
            return tuple(self.cmdb.zPoolList)

    def getISCSIInitiators(self):
        """
        Retreives ISCSI initiators
        """
        result = dict()
        try:
            result = j.cloud.cmdtools.inventoryScan.getISCSIInitiators()
            self.cmdb.iSCSIInitiators = list()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
        else:
            for iSCSIInitiatorFields in result:
                iSCSIInitiator = ISCSIInitiator.ISCSIInitiator()
                iSCSIInitiator.name = iSCSIInitiatorFields['name']
                iSCSIInitiator.target = iSCSIInitiatorFields['target']
                self.cmdb.iSCSIInitiators.append(iSCSIInitiator)
            return tuple(self.cmdb.iSCSIInitiators)

    def getISCSITargets(self):
        """
        Retrieves ISCSI targets
        """
        result = dict()
        try:
            result = j.cloud.cmdtools.inventoryScan.getISCSITargets()
            self.cmdb.iSCSITargets = list()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
        else:
            for iSCSITargetFields in result:
                iSCSITarget = ISCSITarget.ISCSITarget()
                iSCSITarget.name = iSCSITargetFields['name']
                iSCSITarget.target = iSCSITargetFields['target']
                iSCSITarget.connections = int(iSCSITargetFields['connections'])
                self.cmdb.iSCSITargets.append(iSCSITarget)
            return tuple(self.cmdb.iSCSITargets)

    def getCPUUsage(self):
        """
        Retrieves CPU usage
        """
        try:
            self.cmdb.performance.cpuUsage = j.cloud.cmdtools.inventoryScan.getCPUUsage()
            return self.cmdb.performance.cpuUsage
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve CPU usage. Reason: [%s]" % ex.message)

    def getMemoryUsage(self):
        """
        Retrieves memory usage
        """
        try:
            data = j.cloud.cmdtools.inventoryScan.getFreeMemory()
            self.cmdb.performance.freeMemory = float(data['freeMemory'])
            self.cmdb.performance.swapMemorySize = data['freeSwapMemory']
            return data
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve memory usage. Reason: [%s]" % ex.message)

    def getPerformanceInfo(self):
        """
        Retrieves performance related data
        """
        self.getCPUUsage()
        self.getMemoryUsage()
        self.getNetworkStatistics()
        self.cmdb.performance.timeStamp = self._getCurrentTime()
        return self.cmdb.performance

    def getPCIBusComponents(self):
        """
        Retrieves PCI bus components
        """
        try:
            self.cmdb.pCIBusComponents = list(j.cloud.cmdtools.inventoryScan.getPCIBusComponents())
            return tuple(self.cmdb.pCIBusComponents)
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)

    def getRunningProcesses(self):
        """
        Retrieves currently running processes
        """
        try:
            self.cmdb.os.runningProcesses = j.cloud.cmdtools.inventoryScan.getRunningProcesses()
            self.cmdb.os.timeStamp = self._getCurrentTime()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve running processes. Reason: [%s]" % ex.message)
        return tuple(self.cmdb.os.runningProcesses)

    def _getCurrentTime(self):
        """
        Return current time as string
        """
        return time.strftime("%Y/%m/%d %H:%M:%S")

    def getInterfacesAddresses(self):
        """
        Retrieves interface address, subnetMask, and defaultRoute for each interface
        """

        for interface in self.cmdb.nics.keys():
            try:
                data = j.cloud.cmdtools.inventoryScan.getIPAddress(interface)
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve interface %(interface)s address. Reason: [%(reason)s]" % {'interface': interface, 'reason': ex.message})
            else:
                self.cmdb.os.nicAddresses[interface] = data
                self.cmdb.os.timeStamp = self._getCurrentTime()
        return self.cmdb.os.nicAddresses

    def getOperatingSystemInfo(self):
        """
        Retrieves OS related data, e.g. running processes, nics addresses
        """
        self.getRunningProcesses()
        self.getInterfacesAddresses()
        return self.cmdb.os

    def getZPoolMirrorInfo(self):
        """
        Retrieves ZPool mirror, disks info and status, update self.Device

        ZPools must have been populated before this method is called, ZPools are initialized by a call to getZPools
        """
        for zpool in self.cmdb.zPoolList:
            try:
                status = j.cloud.cmdtools.inventoryScan.getZPoolStatus(zpool.name)
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError('Failed to retrieve ZPool mirrors info for ZPool %(zPool)s. Reason: [%(reason)s]' % {'zPool': zpool, 'reason': ex.message})
            else:
                mirrors = status['mirrors']
                for mirrorStatus in mirrors:
                    mirror = ZPoolMirror.ZPoolMirror()
                    zpool.mirrors.append(mirror)
                    mirror.status = mirrorStatus['status']
                    for diskStatus in mirrorStatus['disks']:
                        disk = ZPoolDisk.ZPoolDisk()
                        disk.name = diskStatus['name']
                        disk.status = diskStatus['status']
                        mirror.disks.append(disk)
                        zpool.disks.append(disk)

                disks = status['disks']
                for diskStatus in disks:
                    disk = ZPoolDisk.ZPoolDisk()
                    disk.name = diskStatus['name']
                    disk.status = diskStatus['status']
                    zpool.disks.append(disk)

                zpool.errors = status['errors']
                return tuple(self.cmdb.zPoolList)

    def getHypervisorType(self):
        """
        Retrieves hypervisor type if any hypervisor was installed on this machine
        """
        try:
            self.cmdb.hypervisor.type = j.cloud.cmdtools.inventoryScan.getHypervisorType()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError('Failed to retrieve Hypervisor type. Reason: [%(reason)s]' % {'reason': ex.message})
        return self.cmdb.hypervisor.type

    def getVMachinesStatistics(self):
        """
        Retrieves VMachines, cpu memory usage for each machine
        """
        try:
            self.cmdb.hypervisor.vmSatistics = j.cloud.cmdtools.inventoryScan.getVMachines()
            self.cmdb.hypervisor.timeStamp = self._getCurrentTime()
            return self.cmdb.hypervisor.vmSatistics
        except RuntimeError as ex:
            j.logger.log('Failed to retrieve VMachines statistics. Reason: [%(reason)s]' % {'reason': ex.message}, 3)
        except AttributeError as ex:
            j.logger.log('Failed to retrieve VMachines statistics. Reason: [%(reason)s]' % {'reason': ex.message}, 3)

    def getVMachinesNetworkStatistics(self, delay=2):
        """
        Retrieves VMachines nic Usage
        """
        try:
            self.cmdb.hypervisor.vmNicSatistics = j.cloud.cmdtools.inventoryScan.getVMachinesNetworkStatistics(delay)
            self.cmdb.hypervisor.timeStamp = self._getCurrentTime()
            return self.cmdb.hypervisor.vmNicSatistics
        except RuntimeError as ex:
            j.logger.log('Failed to retrieve VMachines Nics statistics. Reason: [%(reason)s]' % {'reason': ex.message}, 3)
        except AttributeError as ex:
            j.logger.log('Failed to retrieve VMachines Nics statistics. Reason: [%(reason)s]' % {'reason': ex.message}, 3)

    def getNetworkStatistics(self, delay=2):
        """
        Retrieves network statistics for each real nic
        """
        try:
            self.cmdb.performance.networkStatistics = j.cloud.cmdtools.inventoryScan.getNetworkStatistics(delay)
            self.cmdb.performance.timeStamp = self._getCurrentTime()
            return self.cmdb.performance.networkStatistics
        except RuntimeError as ex:
            j.logger.log("Failed to retrieve network statistics. Reason: [%s]" % ex.message, 3)
