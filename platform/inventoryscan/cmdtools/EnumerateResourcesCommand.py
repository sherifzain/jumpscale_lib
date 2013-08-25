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

import re
import os
import re
import time

from JumpScale import j
from JumpScale.core.baseclasses.CommandWrapper import CommandWrapper
from collections import defaultdict

from InventoryScanEnums import *


class NetworkCounterResetException(Exception):
    pass


class EnumerateResourcesCommand(CommandWrapper):

    def getCFCards(self):
        cfCards = list()
        cfDevices = j.system.fs.find('/dev/', 'fstl*')
        for cfDevice in cfDevices:
            cfCards.append(cfDevice.replace('fstl', ''))
        return cfCards

    def getDisks(self):
        """
        Enumerate all the disks present on the system

        Parses the command output into a list of record entries
        On Linux user must have root privileges
        @return: list of text entries (or tuples)
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            try:
                exitCode, output = j.cmdtools.disktools.fdisk.listDisks()
            except RuntimeError as ex:
                if ex.message.find("fdisk: command not found") > -1:
                    j.logger.log("Unable to list Disks. Reason fdisk command not found.", 3)
                    raise RuntimeError("Unable to list Disks. Reason fdisk command not found; make sure you are running Qshell using root user.")
                else:
                    j.logger.log("Unable to list Disks. Reason %s" % ex.message, 3)
                    raise RuntimeError("Unable to list Disks. Reason %s" % ex.message)
            partionInfo = j.cmdtools.partitioninfo.info()

            pattern = re.compile("Disk [^identifier].*\n")

            partionParams = {'fileSystemType': 'fstype',
                             'Label': 'label',
                             'usedGB': 'used',
                             'mountpoint': 'mountpoint',
                             'devices': 'devices',
                             'Active Devices': 'activeDevices',
                             'Raid Devices': 'raidDevices',
                             'Raid Level': 'level',
                             'Spare Devices': 'spareDevices',
                             'Total Devices': 'totalDevices',
                             'Failed Devices': 'failedDevices',
                             'State': 'state'}

            entries = pattern.findall(output)
            disks = dict()

            # Get list of cfcard devices
            cfCards = self.getCFCards()
            dssBlkDevices = self._getDssBlkDevices()
            for entry in entries:
                # Filter out dssblk devices
                if not [device for device in dssBlkDevices if device in entry]:
                    disk = entry.split(',')[0].split(' ')
                    if entry.find(':') > 0:
                        name = disk[1].replace(':', '').strip()
                        # Filter out the CFCARDS here??
                        if not name.split('/')[-1] in cfCards:
                            partitions = self.getPartitions(name)
                            for partition in partitions:
                                partionName = name.split('/')[2]
                                if not name.startswith('/dev/md'):
                                    partionName += partition['number']
                                if partionName in partionInfo:
                                    for key, value in partionParams.iteritems():
                                        if key in partionInfo[partionName]:
                                            partition[value] = partionInfo[partionName][key]
                                    if 'devices' in partition:
                                        partition['backendsize'] = self._calculatePhysicalSizeOfRaid(partition['devices'])
                        else:
                            partitions = []
                        disks[name] = {'size': disk[2],
                                       'unit': disk[3],
                                       'partitions': partitions}
                    else:
                        name = disk[1].strip()
                        disks[name] = {}

            return disks
        elif j.system.platformtype.isSolaris():
            root = '/dev/rdsk/'
            try:
                # here using os.listdir instead of j.system.fs.Walker because j.system.fs.Walker returns only files or directories and filters out links
                # Here, I want to list link files that are filtered out by j.system.fs.Walker

                devLinks = os.listdir(root)
            except os.error as ex:
                j.logger.log("Unable to list Disks. Reason %s" % ex.message, 3)
                raise RuntimeError("Unable to list Disks. Reason %s" % ex.message)
            diskNames = list(j.system.fs.joinPaths(root, diskName) for diskName in devLinks if diskName.endswith('p0'))
            disks = list()
            for name in diskNames:
                if not self._isIscsi(name):  # ignore iscsi disks
                    try:
                        size = j.cmdtools.disktools.fdisk.getSize(name)
                        disks.append((name, "%s GB" % (size / (1024 * 1024 * 1024))))
                    except RuntimeError:
                        pass
                else:
                    j.logger.log("Ignoring iscsi  disk %s while scanning device disks" % name, 4)
#                except RuntimeError, ex:
#                    j.logger.log("Unable to list Disks. Reason %s"%ex.message, 3)
#                    raise RuntimeError("Unable to list Disks. Reason %s"%ex.message)
            return tuple(disks)
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getPartitions(self, deviceName):
        """
        List partitions on specified devicename
        
        @param devicename: name of devive (sda or /dev/sda)
        @type devicename: string
        @return: list of partition dict
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            pattern = re.compile('^/dev/(?P<dev>\w*)$')
            match = pattern.match(deviceName)
            if match:
                deviceName = match.groups()[0]
            try:
                partitions = j.cmdtools.partitioninfo.infoParted(deviceName, 'miB')
            except RuntimeError as e:
                if 'unrecognised disk label' in e.message:
                    j.cmdtools.disktools.parted.createLabel(deviceName, 'gpt')
                    partitions = j.cmdtools.partitioninfo.infoParted(deviceName, 'miB')
                else:
                    raise
            return partitions
        elif j.system.platformtype.isSolaris():
            raise NotImplementedError()

    def _isIscsi(self, deviceName):
        """
        Find out if the Device is an iscsi device using ls -lsa
        
        @param deviceName: name of the device
        @return: is iscsi
        @rtype: boolean
        """
        exitCode, output = j.system.process.execute('ls -lsa %s' % deviceName, outputToStdout=False)
        return output.find('iscsi') > -1

    def getNics(self):
        """
        Enumerate all the NICs present on the system

        Parses the command output into a list of record entries
        @return: list of text entries (or tuples)
        """
        nicNames = j.system.net.getNics()
        nics = list()
        for name in nicNames:
            nics.append((name, j.system.net.getMacAddress(name), self._getNicType(name)))
        return tuple(nics)

    def _getNicType(self, interface):
        """
        Retrieves the NicType of a network interface
        This is an alternative implementation for j.system.net.getNicType() cause it doesn't get the interface speed it only tells if this Nic is virtual, ethernet_GB

        @param interface: Interface to determine Nic type on
        @rtype: NicTypes
        @return: the type of the Nic, one of the values of j.enumerators.NicTypes
        """
        type = ''
        # infiniband cards start always with IBx naming convention,
        # ethtool/ndd can't query a IB interface
        if interface.lower().startswith('ib'):
            type = 'IB'
        elif j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            try:
                output = j.cmdtools.ethtool.getInterfaceType(interface)
            except RuntimeError as ex:
                j.logger.log("Failed to retrieve NicType of interface[%s]. Reason: %s" % (interface, ex.message), 3)
                type = ''
            else:
                out = output.get('Supported link modes', None)
                if out:
                    type = out[-1].split('baseT')[0]

        elif j.system.platformtype.isSolaris():
            try:
                exitCode, output = j.cmdtools.ndd.getInterfaceLinkSpeed(interface)
                type = output.strip()
            except RuntimeError as ex:
                if ex.message.find('No such file or directory') < 0:
                    j.logger.log("Failed to retrieve NicType of interface[%s]. Reason: %s" % (interface, ex.message), 3)
                    type = ''
        else:
            raise RuntimeError("Operation not supported on this platform")

        if type == '10':
            return NicTypes.TENBASET
        elif type == '100':
            return NicTypes.HUNDREDBASET
        elif type == '1000':
            return NicTypes.THOUSANDBASET
        elif type == 'IB':
            return NicTypes.INFINIBAND
        else:
            return NicTypes.UNKNOWN

    def getMemoryInfo(self):
        """
        Calculates total MB of RAM present in the device

        @return total memory in MB
        """
        # Handle Xen dom0 - DAL-1986
        try:
            import xen.xend.XendClient
            info = dict(xen.xend.XendClient.server.xend.node.info())
            tot_ram = info['total_memory']
            j.logger.log('Got total amount of memory through xend: %d' %
                         tot_ram, 5)
            return tot_ram
        except KeyError:
            #'total_memory' is not defined, was there some API change?
            raise
        except:
            j.logger.log(
                'Unable to request memory using xend, this is most likely not an issue', 8)

        if j.system.platformtype.isLinux() or j.system.platformtype.isESX() or j.system.platformtype.isSolaris():
            #@REMARK (memory size - kernel size) : didn't give full size of memory
            return j.system.unix.getMachineInfo()[0]
        else:
            raise RuntimeError("Operation not supported on this platform.")

    def getCPUInfo(self):
        """
        Calculates numberOfCpus, numberOfCpuCores, totalCpuFrequency processing power present in the device
        This method provides alternative implementation for j.system.unix.getMachineInfo() since the later does not provide numberOfCpus

        @rtype: tuple
        @return (numberOfCpus, numberOfCpuCores, totalCpuFrequency)
        """

        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            processorInfoText = j.system.fs.fileGetContents('/proc/cpuinfo')
            processorInfo = self._extractProcessorInfo(processorInfoText)
            numberOfCpus = 0
            coreNumbers = 0
            totalCpuFrequency = 0
            info = defaultdict(dict)
            for entry in processorInfo:
                phId = entry['physicalId']
                if phId not in info.keys():
                    info[phId]['ncores'] = entry['cpucores']
                coreId = entry['coreId']
                try:
                    info[phId]['cores']
                except KeyError:
                    info[phId]['cores'] = set()
                if coreId not in info[phId]['cores']:
                    try:
                        info[phId]['freq']
                    except KeyError:
                        info[phId]['freq'] = 0
                    coreFreq = float(entry['frequency'])
                    info[phId]['freq'] += coreFreq
                    totalCpuFrequency += coreFreq
                    info[phId]['cores'].add(coreId)
                    coreNumbers += 1
            return (len(info), coreNumbers, int(totalCpuFrequency))
        elif j.system.platformtype.isSolaris():
            try:
                exitCode, output = j.cmdtools.psrinfo.getProcessorCoresInfo()
            except RuntimeError as ex:
                j.logger.log("Unable to list CPUs. Reason %s" % ex.message, 3)
                raise RuntimeError("Unable to list CPUs. Reason %s" % ex.message)
            pattern = re.compile("operates at.*")
            entries = pattern.findall(output)
            numberOfCores = 0
            totalCpuFrequency = 0
            for entry in entries:
                numberOfCores += 1
                totalCpuFrequency += int(entry.split(' ')[2])
            try:
                exitCode, output = j.cmdtools.psrinfo.getNumberOfProcessors()
            except RuntimeError as ex:
                j.logger.log("Unable to list CPUs. Reason %s" % ex.message, 3)
                raise RuntimeError("Unable to list CPUs. Reason %s" % ex.message)
            numberOfCpus = int(output)
            return(numberOfCpus, numberOfCores, int(totalCpuFrequency))
        else:
            raise RuntimeError("Operation not supported on this platform")

    def _extractProcessorInfo(self, processorInfo):
        """
        Retrieves processorId, frequency, coreId, physicalId, cpucores Info for each processor in processorInfo

        @param processorInfo: content of /proc/cpuinfo file
        @rtype: tuple of maps
        @return: processorId, frequency, coreId, physicalId of each processor
        """
        recordPattern = '.*?\\n\\n'
        fieldPattern = '.*?\\n'
        toReturn = list()
        records = list(record.replace('\n\n', '') for record in re.findall(recordPattern, processorInfo, re.DOTALL))
        for record in records:
            fields = list(field.replace('\n', '').split(':')[1].strip() for field in re.findall(fieldPattern, record))
            recordList = {'processorId': fields[0], 'frequency': fields[6], 'physicalId': fields[8], 'coreId': fields[10], 'cpucores': fields[11]}
            toReturn.append(recordList)
        return tuple(toReturn)

    def getPCIBusComponents(self):
        """
        Retrieves all the available components of PCI Bus on a machine

        @rtype: List  of dictionaries [{componentName:<>, manufacturer:<>, model:<>}]
        @return: Component name, manufacturer, and model for each PCI component
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            try:
                componentString = j.cmdtools.lspci.listComponents()
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve PCI Bus components. Reason: [%s]" % ex.message)
            componentEntries = componentString.split('\n')
            components = list()
            for component in componentEntries:
                if component:
                    componentFields = component.replace('" "', '"').replace(' "', '"').split('"')
                    components.append({'componentName': componentFields[1], 'manufacturer': componentFields[2], 'model': componentFields[3]})
            return tuple(components)
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getRunningProcesses(self):
        """
        Retrieves all the running processes on a machine

        @rtype: List  of dictionaries [{PID:<>, processName:<>}]
        @return: PID, and processName for each running process
        @raise RuntimeError:
        """
        j.logger.log("Retrieving the current running processes", 3)
        try:
            output = j.cmdtools.ps.getRunningProcesses()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve running processes. Reason: [%s]" % ex.message)
        output = output[output.find('\n') + 1:]
        lines = output.split('\n')
        result = list()
        for line in lines:
            record = dict()
            attributs = line.split()
            if not attributs:
                continue
            record["PID"] = int(attributs[0])
            record["processName"] = attributs[3]
            result.append(record)
        return result

    def getIPAddress(self, nicName):
        """
        Retrieves IPAdress, subnet mask, and default route of an interface

        @rtype: dict {'ip':<>, 'subnetMask':<>, 'defaultRoute':<>}
        @return: IPAdress, subnet mask, and default route of an interface
        """
        addresses = j.system.net.getIpAddress(nicName)
        ip, subnetMask, defaultRoute = '', '', ''
        if addresses:
            ip, subnetMask, defaultRoute = addresses[0]
        return {'ip': ip, 'subnetMask': subnetMask, 'defaultRoute': defaultRoute}

    def getFreeMemory(self):
        """
        Retrieves used memory, and used swap memory in k-byte

        @rtype: dict
        @return: freeMemory, freeSwapMemory
        """
        j.logger.log("Retrieving free Memory on the system", 3)
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            try:
                output = j.cmdtools.free.getFreeMemory()
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve used Memory on the system. Reason: [%s]" % ex.message)
            output = output[output.find('\n') + 1:]
            lines = output.split('\n')
            memRecord = lines[0]
            swapRecord = lines[2]
            mem = int(memRecord.split()[3])
            swap = int(swapRecord.split()[3])
            result = dict()
            result["freeMemory"] = mem
            result["freeSwapMemory"] = swap
            return result
        elif j.system.platformtype.isSolaris():
            try:
                output = j.cmdtools.vmstat.getFreeMemory()
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve used Memory on the system. Reason: [%s]" % ex.message)

            output = output.strip()
            lines = output.split('\n')
            memRecord = lines[3]
            swap = int(memRecord.split()[3])
            mem = int(memRecord.split()[4])
            result = dict()
            result["freeMemory"] = mem
            result["freeSwapMemory"] = swap
            return result

    def getISCSITargets(self):
        """
        Retrieves target, name, and connections information for each ISCSI target

        @rtype: list of dict{target:<>, name:<>, connections:<>}
        @return: target, name, and connections for each ISCSI target
        """
        # Only supported on Solaris as iscsitadm vapp was only supported on Solaris (there is a dummy vapp version supported on all platforms)
        if j.system.platformtype.isSolaris():
            targets = j.cmdtools.iscsitadm.listTarget()
            toReturn = list()
            for count in range(len(targets) / 3):
                target = targets[count * 3]
                name = targets[count * 3 + 1]
                connections = targets[count * 3 + 2]
                toReturn.append({'target': target.split(': ')[1], 'name': name.split(': ')[1], 'connections': connections.split(': ')[1]})
            return tuple(toReturn)
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getISCSIInitiators(self):
        """
        Retrieves target and deviceName information for each ISCSI initiator

        @rtype: list of dict{target:<>, deviceName:<>}
        @return: target and deviceName for each ISCSI initiator
        """
        # Only supported on Solaris as iscsiadm vapp was only supported on Solaris (there is a dummy vapp version supported on all platforms)
        if j.system.platformtype.isSolaris():
            initiators = j.cmdtools.iscsiadm.listTarget(None, True)
            toReturn = list()
            for initiator in initiators.split('\n\n'):
                if initiator:
                    initiatorFields = initiator.split('\n')
                    toReturn.append({
                                    'target': initiatorFields[0].split(': ')[1],
                                    'name': initiatorFields[8].split(': ')[1]})
            return toReturn
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getZPoolsInfo(self):
        """
        Retrieves zpool info for available zpools

        @rtype: dict of dict's
        @return: name, size, used, availableSize, cap, and health for each zpool available on machine
        """
        j.logger.log("Retrieving zpools information", 3)
        if j.system.platformtype.isSolaris():
            columns = ['name', 'size', 'used', 'avialableSize', 'CAP', 'health']
            records = dict()
            exitCode, output = j.cmdtools.zfs.zpool.getZpoolInfo()
            lines = output.split('\n')
            for line in lines:
                record = line.split('\t')
                record.pop(len(record) - 1)
                dRecord = dict(zip(columns, record))
                try:
                    records[dRecord['name']] = dRecord
                except KeyError as ex:
                    j.logger.log(ex.message, 3)
            return records
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getZFS(self):
        """
        Retrieves current zfs file systems installed on system

        @rtype: dict
        @return: zfs info
        """

        j.logger.log("Retrieving available zfs file systems installed on the system", 3)
        if j.system.platformtype.isSolaris():
            try:
                output = j.cmdtools.zfs.zfs.list()
            except Exception as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve ZFS filesystems installed on the system. Resaon: [%s]" % ex.message)
            return output
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getZPoolStatus(self, zPool):
        """
        Retrieves status fields for given ZPool

        @param zPool: Name for the zpool e.g. storagepoola
        """
        if j.system.platformtype.isSolaris():
            j.logger.log("Retrieving ZPool %s status" % zPool, 3)
            try:
                output = j.cmdtools.zfs.zpool.getStatus(zPool)
            except Exception as ex:
                j.logger.log(ex.message.message, 3)
                raise RuntimeError("Failed to retrieve ZPool %(zPool)s status. Resaon: [%(reason)s]" % {'zPool': zPool, 'reason': ex.message})
            inp = output[:-1]
            mirrors = list()
            disks = list()
            currentMirror = None
            for i in range(6, len(inp)):
                fields = inp[i].split()
                if inp[i].find('mirror') > 0:
                    currentMirror = dict()
                    mirrors.append(currentMirror)
                    currentMirror['status'] = fields[1]
                    currentMirror['disks'] = list()
                else:
                    disk = dict()
                    if currentMirror is not None:
                        currentMirror['disks'].append(disk)
                        disk['name'] = fields[0]
                        disk['status'] = fields[1]
                    else:
                        disks.append({'name': fields[0], 'status': fields[1]})
            return {'mirrors': mirrors, 'disks': disks, 'errors': output[-1].split(':')[1]}
        else:
            raise RuntimeError("Operation not supported on this platform")

    def checkFreeDiskStatus(self, fileSystemPath='/', availablePercentage=25, availableSizeLimit=3):
        """
        Retrieves free spaces for fileSystems, if percentage of free space below availablePercentage param raise RuntimeWarning, if free size less than availableSizeLimit param raise RuntimeWarning

        @param fileSystemPath: file system path for the file system to be checked
        @param availablePercentage: percentage to use as reference to compare with free space on file system
        @param availableSizeLimit: size to use as reference to compare with free space on file system in GB
        """
        diskStatus = self.getFreeDiskStatus(fileSystemPath)
        j.logger.log("Checking if more than %s disk space is available:" % availablePercentage, 3)
        if int(diskStatus['deviceUsedPercentage']) > (100 - availablePercentage):  # -1 to remove unit
            raise RuntimeWarning('Less than %(availablePercentage)s percentage of disk space available on %(fileSystemPath)s' %
                                 {'availablePercentage': availablePercentage, 'fileSystemPath': fileSystemPath})
        else:
            j.logger.log("OK", 3)
        j.logger.log("Checking if more than %sGB disk space is available:" % availableSizeLimit, 3)
        sizeavailable = float(diskStatus['deviceSize']) - float(diskStatus['deviceUsed'])
        if sizeavailable < availableSizeLimit:
            raise RuntimeWarning('Less than %(availableSizeLimit)s disk space available on %(fileSystemPath)s' %
                                 {'availableSizeLimit': availableSizeLimit, 'fileSystemPath': fileSystemPath})
        else:
            j.logger.log("OK", 3)

    def getFreeDiskStatus(self, fileSystemPath='/'):
        """
        Retrieves device size, percentage memory used, available size, device capacity

        @param fileSystemPath: file system path for the file system
        """
        diskpattern = re.compile(
            '^(?P<devicepath>[a-z0-9/]+)\s+(?P<devicesize>[\w.]+)\s+(?P<deviceused>[\w.]+)\s+(?P<deviceavailable>[\w.]+)\s+(?P<deviceusagepercentage>[\w.%]+)\s+.*$')
        j.logger.log("Retrieving disk status", 3)
        try:
            output = j.cmdtools.df.getFreeDiskSpace()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to get free disk space for filesystem %s" % fileSystemPath)
        diskstate = output.splitlines()[1]
        match = diskpattern.match(diskstate)
        if match:
            return {'totalSize': match.group('devicesize')[:-1],
                    'usedPercentage': match.group('deviceusagepercentage')[:-1],
                    'usedSize': match.group('deviceused')[:-1],
                    'availableSize': match.group('deviceavailable')[:-1]}

    def getCPUsProcessState(self):
        """
        Retrieves current process info

        @rtype: dict
        @return: user process time, low system priority process time, high system priority process time, idle process time
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            cpusInfo = dict()
            cpusStatus = j.cmdtools.proc.getCPUSpecifications()
            pattern = re.compile('^(?P<cpuId>cpu[\d]*)\s+(?P<user>[\d]*)\s+(?P<systemLow>[\d]*)\s+(?P<systemHigh>[\d]*)\s+(?P<idle>[\d]*).*')
            for field in cpusStatus.split('\n'):
                match = pattern.match(field)
                if match:
                    cpusInfo[match.group('cpuId')] = {'user': int(match.group('user')),
                                                      'systemLow': int(match.group('systemLow')),
                                                      'systemHigh': int(match.group('systemHigh')),
                                                      'idle': int(match.group('idle'))}
            return cpusInfo
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getCPUUsage(self, delay=3):
        """
        Retrieves CPU usage percentage for all CPUs, and for each CPU

        @param delay: delay between the two readings to calculate CPU usage in that time (more accurate when increased)
        @rtype: dict
        @return: CPU usage percentage
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
            try:
                # take two reading to calculate CPU usage in that period
                cpusInfo1 = self.getCPUsProcessState()
                time.sleep(delay)
                cpusInfo2 = self.getCPUsProcessState()
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve CPU usage on the system. Reason: [%s]" % ex.message)
            cpusPercentage = dict()
            for cpuId in cpusInfo1.keys():
                if cpuId == 'cpu':
                    cpuIdName = 'average'
                else:
                    cpuIdName = cpuId
                busyTime = cpusInfo2[cpuId]['user'] + cpusInfo2[cpuId]['systemLow'] + cpusInfo2[cpuId][
                    'systemHigh'] - (cpusInfo1[cpuId]['user'] + cpusInfo1[cpuId]['systemLow'] + cpusInfo1[cpuId]['systemHigh'])
                idleTime = cpusInfo2[cpuId]['idle'] - cpusInfo1[cpuId]['idle']
                if not busyTime and not idleTime:
                    cpusPercentage[cpuIdName] = 0.0
                    continue
                cpusPercentage[cpuIdName] = round(100 * busyTime / (busyTime + idleTime))
            return cpusPercentage
        elif j.system.platformtype.isSolaris():
            try:
                cpusInfo = j.cmdtools.mpstat.getCPUsInfo()
            except RuntimeError as ex:
                j.logger.log(ex.message, 3)
                raise RuntimeError("Failed to retrieve CPU usage on the system. Reason: [%s]" % ex.message)
            cpusPercentage = dict()
            total = 0.0
            cpuInfoEntries = cpusInfo.split('\n')[1:]
            cpuCount = 0
            for cpuEntry in cpuInfoEntries:
                if cpuEntry:
                    cpuFields = cpuEntry.split()
                    cpuId = 'cpu' + str(cpuFields[0])
                    cpusPercentage[cpuId] = 100 - round(float(cpuFields[15]))
                    total += cpusPercentage[cpuId]
                    cpuCount += 1
            if not cpuCount:
                cpusPercentage['average'] = 0.0
            else:
                cpusPercentage['average'] = round(total / cpuCount)
            return cpusPercentage
        else:
            raise RuntimeError("Operation not supported on this platform")

    def getHypervisorType(self):
        """
        Retrieves the type of hypervisor available on this machine (if exists)

        @rtype: InventoryScanEnums.HypervisorsType
        @return: Hypervisor type
        """
        hypervisorType = HypervisorsType.NOHYPERVISOR
        #kernelName = j.cmdtools.uname.getKernelName()
        if j.system.platformtype.isXen():
            hypervisorType = HypervisorsType.XEN
        else:
            if j.system.platformtype.isSolaris():
                systemModules = j.cmdtools.modinfo.listModules()
            elif j.system.platformtype.isVirtualBox():
                hypervisorType = HypervisorsType.VBOX
            elif j.system.platformtype.isESX():
                hypervisorType = HypervisorsType.VMWARE
        return hypervisorType

    def getVMachines(self):
        """
        Retrieves available VMachines on machine

        @rtype: list of dict
        @return: available virtual machines
        """
        type = self.getHypervisorType()
        if type is HypervisorsType.XEN:
            return self._getXenVMachinesUtilization()
        if type is HypervisorsType.VBOX:
            return self._getVBoxMachinesUtilization()
        else:
            return dict()

    def _getXenVMachinesUtilization(self):
        """
        Retrieves CPU, memory Utilization for each machine in VMachines

        @rtype: dictionary of dictionaries e.g {'vmachineName': {'cpuUsage':<value>, 'memUsage':< value>, 'status':<value>}
        """
        vmachines = dict()
        try:
            status = j.cmdtools.xentop.getVMStatus()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve vmachines utilization statistics for Xen. Reason: [%s]" % ex.message)
        except AttributeError as ex:
            j.logger.log(ex.message, 3)
            raise AttributeError("Unsupported platform or proper extension not installed. Reason: [%s]" % ex.message)
        machineStatus = self._getXenVMachinesStatus()
        pattern = re.compile(
            '\s*(?P<domainName>[\w.]+)\s+(?P<state>.{6})\s+(?P<cpuTime>[\d.]+)\s+(?P<cpuPercentage>[\d.]+)\s+(?P<memory>[\d.]+)\s+(?P<memoryPercentage>[\d.]+)\s+.*')
        for vmField in status.split('\n'):
            match = pattern.match(vmField)
            if match:
                name = match.group('domainName')
                vmachines[name] = {'cpuUsage': match.group('cpuPercentage'), 'memUsage': match.group('memoryPercentage'), 'status': machineStatus[name]}
        return vmachines

    def _getXenVMachinesStatus(self):
        """
        Retrieves status for vmachines returning name and status

        @rtype: dict e.g {'vmachineName': <status>}
        """
        vMachinesStatus = dict()
        vmachines = q.hypervisors.cmdtools.xen.machineConfiguration.listMachines()
        for machine in vmachines.values():
            vMachinesStatus[machine['name_label']] = machine['power_state']
        return vMachinesStatus

    def _getVBoxMachinesUtilization(self):
        """
        Retrieves Vbox vmachines cpu and memory usage

        @rtype: dictionary of dictionaries e.g {'vmachineName': {'cpuUsage':<value>, 'memUsage':< value>, 'status':<value>}
        @return: cpu and memorty usage of each vmachine currentlly running on vbox
        """
        result = dict()
        if j.system.platformtype.isLinux():
            options = 'aux'
        elif j.system.platformtype.isSolaris():
            options = 'af -o pid,pcpu,pmem,comm'
        try:
            output = j.cmdtools.ps.getVBoxRunningMachinesStat(options)
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve vmachines statistics. Reason: [%s]" % ex.message)
        lines = output.split('\n')[:-1]
        for line in lines:
            vmachineInfo, vmachineName = self._processVboxOutput(line)
            status = 'unknown'
            try:
                status = q.hypervisors.manage.virtualbox.getMachineStatus(vmachineName).value
            except (ValueError, AttributeError) as ex:
                j.logger.log(ex.message, 3)
            vmachineInfo['status'] = status
            result[vmachineName] = vmachineInfo
        return result

    def _processVboxOutput(self, output):
            """
            Process a line of vbox machine porcess output and extract the cpu and memory usage from it.

            @rtype: tuple
            @return: dictionary of cpu and mem usage, and the name of the vmachine
            """
            vmachineInfo = dict()
            parts = output.split()
            if j.system.platformtype.isSolaris():
                # This code was never tested on solaris machine since the setup of
                # PMachine with solaris os and Virtualbox hypervisor is not avialable at the moment
                vmachineName = parts[5]
                vmachineInfo['cpuUsage'] = parts[1]
                vmachineInfo['memUsage'] = parts[2]
            elif j.system.platformtype.isLinux():
                vmachineName = parts[12]
                vmachineInfo['cpuUsage'] = parts[2]
                vmachineInfo['memUsage'] = parts[3]
            return vmachineInfo, vmachineName

    def getNetworkStatistics(self, delay=2):
        """
        Retrieves network statistics, tx, rx, bw... for each real nic

        @param delay: period between any two consecutive network statistcs retreivals
        @return: dict {'nicName' : <nic statistics fields>}
        """
        stats = dict()
        retryCount = 0

        while(retryCount < 5):
            try:
                # this method is only supported on Linux as all CPUNodes have Linux as platform
                if j.system.platformtype.isLinux() or j.system.platformtype.isESX():
                    networkStatistic = dict()
                    for nicFields in self.getNics():
                        nicName = nicFields[0]
                        nicStatistics = self._getNicStatistics(nicName, delay)
                        if nicStatistics:
                            networkStatistic[nicName] = nicStatistics
                    stats = networkStatistic
                    break
                else:
                    raise RuntimeError("Operation not supported on this platform")
            except NetworkCounterResetException as ex:
                retryCount += 1
        else:
            raise RuntimeError('Unable to retrieve VMachines network statistics')  # this condition should never be reached

        return stats

    def getVMachinesNetworkStatistics(self, delay=2):
        """
        Retrieves network statistics, tx, rx, bw, ... for all vMachines

        @param delay: period between any two consecutive network statistcs retreivalss
        """
        type = self.getHypervisorType()
        stats = dict()
        retryCount = 0

        while(retryCount < 5):
            try:
                if type is HypervisorsType.XEN:
                    stats = self._getXenVMachinesNetworkStatistics(delay)
                if type is HypervisorsType.VBOX:
                    stats = self._getVBoxVMachinesNetworkStatistics(delay)
                break
            except NetworkCounterResetException as ex:
                retryCount += 1
        else:
            raise RuntimeError('Unable to retrieve VMachines network statistics')  # this condition should never be reached

        return stats

    def _getXenVMachinesNetworkStatistics(self, delay=2):
        """
        Retrieves current network statistics, tx, rx, bw... for XEN vMachine

        @param delay: period between any two consecutive network statistcs retreivals
        @return: dict{'machine': {<'interface'>:{statistics}}}
        """
        if delay < 1:
            delay = 1
        firstReading = self._getXenVmachineNetworkInfo()
        time.sleep(delay)
        secondReading = self._getXenVmachineNetworkInfo()

        return self._getAllNicRatesfromTwoReadings(firstReading, secondReading, delay)

    def _getAllNicRatesfromTwoReadings(self, firstReading, secondReading, delay=2):
        """
        Get the rate of Nics fields from Total readings( include severla machines and several Nics)
        """
        average = dict()
        for domain, nics in firstReading.items():
            average[domain] = dict()
            for nicName, nicStat in nics.items():
                average[domain][nicName] = self._getNicRatefromTwoReadings(firstReading[domain][nicName], secondReading[domain][nicName], delay)
        return average

    def _getNicRatefromTwoReadings(self, firstReading, secondReading, delay=2):
        """
        Get the rate of Nics fields from two nic info readings
        """
        average = {'rxBytes': self._getRate(firstReading['rxBytes'], secondReading['rxBytes'], 'bytes', delay),
                   'rxPackets': self._getRate(firstReading['rxPackets'], secondReading['rxPackets'], 'pkts', delay),
                   'rxErrors': self._getRate(firstReading['rxErrors'], secondReading['rxErrors'], 'err', delay),
                   'rxDrop': self._getRate(firstReading['rxDrop'], secondReading['rxDrop'], 'drop', delay),
                   'txBytes': self._getRate(firstReading['txBytes'], secondReading['txBytes'], 'bytes', delay),
                   'txPackets': self._getRate(firstReading['txPackets'], secondReading['txPackets'], 'pkts', delay),
                   'txErrors': self._getRate(firstReading['txErrors'], secondReading['txErrors'], 'err', delay),
                   'txDrop': self._getRate(firstReading['txDrop'], secondReading['txDrop'], 'drop', delay)}
        return average

    def _getRate(self, firstValue, secondValue, unit, delay=2):
        """
        Get the rate by taking the difference of two readings having units appended to them; for example 45error, 23error would result 37error
        """
        firstValue = float(firstValue.split(unit)[0])
        secondValue = float(secondValue.split(unit)[0])

        if secondValue < firstValue:
            raise NetworkCounterResetException('Network interface counter has been reset, retrying')
        if delay == 0:
            raise ValueError('Delay value must be higher than 0')
        return str(round((secondValue - firstValue) / delay)) + unit

    def _getXenVmachineNetworkInfo(self):
        """
        Retrieves network statistics from system uptime, tx, rx, bw... for XEN vMachine

        @param iterations: number of iteration to take nics statistics average at
        @return: dict{'machine': {<'interface'>:{statistics}}}
        """
        networkStatistics = dict()
        try:
            vMNicsStatus = j.cmdtools.xentop.getVMNicsStatus()
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve vmachines network statistics for Xen. Reason: [%s]" % ex.message)
        except AttributeError as ex:
            j.logger.log(ex.message, 3)
            raise AttributeError("Unsupported platform or proper extension not installed. Reason: [%s]" % ex.message)
        nicPattern = re.compile(
            '\s*(?P<interfaceName>[\w.]+)\s+(?P<rx>[\w.:]+)\s+(?P<rxBytes>[\w.]+)\s+(?P<rxPackets>[\w.]+)\s+(?P<rxErrors>[\w.]+)\s+(?P<rxDrop>[\w.]+)\s+(?P<tx>[\w.:]+)\s+(?P<txBytes>[\w.]+)\s+(?P<txPackets>[\w.]+)\s+(?P<txErrors>[\w.]+)\s+(?P<txDrop>[\w.]+)\s*')
        domainPattern = re.compile(
            '\s*(?P<domainName>[\w.]+)\s+(?P<state>.{6})\s+(?P<cpuTime>[\d.]+)\s+(?P<cpuPercentage>[\d.]+)\s+(?P<memory>[\d.]+)\s+(?P<memoryPercentage>[\d.]+)\s+.*')
        currentDomain = None
        for line in vMNicsStatus.split('\n'):
            domainMatch = domainPattern.match(line)
            if domainMatch:
                currentDomain = domainMatch.group('domainName')
                networkStatistics[currentDomain] = dict()
            else:
                if not currentDomain:
                    continue  # neglect Domain-0 nics statistics to retrieve nics for each domain seperatly
                nicMatch = nicPattern.match(line)
                if nicMatch:
                    networkStatistics[currentDomain][nicMatch.group(
                        'interfaceName')] = {'rxBytes': nicMatch.group('rxBytes'), 'rxPackets': nicMatch.group('rxPackets'),
                                             'rxErrors': nicMatch.group('rxErrors'), 'rxDrop': nicMatch.group('rxDrop'),
                                             'txBytes': nicMatch.group('txBytes'), 'txPackets': nicMatch.group('txPackets'),
                                             'txErrors': nicMatch.group('txErrors'), 'txDrop': nicMatch.group('txDrop')}
        return networkStatistics

    def _getNicStatistics(self, interfaceName, delay=2):
        """
        Retrieve nic statistic for given interface name

        @param interfaceName: name of the interface
        @param delay: period in seconds between any two consecutive network statistcs retreivals
        """
        if j.system.platformtype.isLinux() or j.system.platformtype.isESX():  # this method is only supported on Linux as all CPUNodes have Linux as platform
            nicStatistics = dict()
            if self._isRealNic(interfaceName):
                try:
                    nicInfo = j.cmdtools.ifconfig.getInterfaceInfo(interfaceName)
                    firstReading = self._parseInterfaceInfo(nicInfo)
                    time.sleep(delay)
                    nicInfo = j.cmdtools.ifconfig.getInterfaceInfo(interfaceName)
                    secondReading = self._parseInterfaceInfo(nicInfo)
                    nicStatistics = self._getNicRatefromTwoReadings(firstReading, secondReading, delay)
                except RuntimeError as ex:
                    j.logger.log(ex.message, 3)
                    raise RuntimeError("Failed to retrieve network statistics for nic %(nic)s. Reason: [%(reason)s]" % {
                                       'nic': interfaceName, 'reason': ex.message})

            return nicStatistics
        else:
            raise RuntimeError("Operation not supported on this platform")

    def _isRealNic(self, interfaceName):
        """
        Checks if the nic is real, or virtual interface

        @param interfaceName: name of the interface
        @return: is real
        """
        isReal = False
        try:
            interfaceDriver = j.cmdtools.ethtool.getInterfaceDriver(interfaceName)
            driverMatch = re.match('\s*driver:\s(?P<driver>[\w]*)\n.*', interfaceDriver)
            if driverMatch:
                driver = driverMatch.group('driver')
                isReal = driver not in ('bridge', 'tun')
        except RuntimeError as ex:
            pass  # in some cases of virtual interfaces ethtools raises an error

        return isReal

    def _getVBoxVMNetworkInterfaces(self, machineName):
        """
        Retrieves the attached network interface to a virtual machine

        @param machineName: name of the machine whose network interfaces will be retrieved

        @rtype: list
        @return: network interface names
        """
        try:
            machineInfo = q.hypervisors.cmdtools.virtualbox.machineConfig.showvminfo(machineName)
        except RuntimeError as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieve the attached network interface to machine %(machine)s. Reason: [%(reason)s]" % {
                               'machine': machineName, 'reason': ex.message})
        interfaces = list()
        for adapter in machineInfo['networkAdapters']:
            if adapter['enabled']:
                interfaces.append(adapter['hostInterface'])
        j.logger.log("Found network interfaces [%s] on machine [%s]" % (interfaces, machineName), 3)
        return interfaces

    def _parseInterfaceInfo(self, interfaceInfoString):
        """
        Retrieves rxBytes, rxPackets, rxErrors, rxDrop, txBytes, txPackets, txErrors, txDrop for ifconfig nic output
        """

        nicPattern = re.compile(
            '\s*(?P<interfaceName>[\w.]+)\s+.*RX\s+packets:(?P<rxpackets>[0-9]+)\s+errors:(?P<rxerrors>[0-9]+)\s+dropped:(?P<rxdropped>[0-9]+).*TX\s+packets:(?P<txpackets>[0-9]+)\s+errors:(?P<txerrors>[0-9]+)\s+dropped:(?P<txdropped>[0-9]+).*RX\s+bytes:(?P<rxbytes>[0-9]+).*TX\s+bytes:(?P<txbytes>[0-9]+)\s+.*', re.DOTALL)
        nicMatch = nicPattern.match(interfaceInfoString)
        statistics = dict()
        if nicMatch:
            statistics = {'rxBytes': nicMatch.group('rxbytes'), 'rxPackets': nicMatch.group('rxpackets'),
                          'rxErrors': nicMatch.group('rxerrors'), 'rxDrop': nicMatch.group('rxdropped'),
                          'txBytes': nicMatch.group('txbytes'), 'txPackets': nicMatch.group('txpackets'),
                          'txErrors': nicMatch.group('txerrors'), 'txDrop': nicMatch.group('txdropped')}
        return statistics

    def _getVBoxVMachinesNetworkInfo(self):
        """
        Retrieves network statistics, tx, rx, bw... for VBox vMachine

        @return: dict{'machine': {<'interface'>:{statistics}}
        """

        # The returned rx bytes and tx bytes are reversed due to VBOX networking tunneling used to virtualized networking facilities for VBox machines e.g:
        # 'rxBytes': '1000bytes' means that the transmitted bytes rate are 1000 bytes
        networkStatistics = dict()
        try:
            machines = q.hypervisors.manage.virtualbox.cmdb.machines.keys()
        except (AttributeError, RuntimeError) as ex:
            j.logger.log(ex.message, 3)
            raise RuntimeError("Failed to retrieves network statistics for VBox. Reason: [%(reason)s]" % {'reason': ex.message})
        for machine in machines:
            interfaces = self._getVBoxVMNetworkInterfaces(machine)
            interfaceDict = dict()
            for interface in interfaces:
                interfaceInfo = j.cmdtools.ifconfig.getInterfaceInfo(interface)
                statistics = self._parseInterfaceInfo(interfaceInfo)
                interfaceDict[interface] = statistics
            networkStatistics[machine] = interfaceDict
        return networkStatistics

    def _getVBoxVMachinesNetworkStatistics(self, delay=2):
        """
        Retrieves current network statistics, tx, rx, bw... for VBox vMachine

        @param delay: period in seconds between any two consecutive network statistcs retreivals
        @return: dict{'machine': {<'interface'>:{statistics}}}
        """
        if delay < 1:
            delay = 1
        firstReading = self._getVBoxVMachinesNetworkInfo()
        time.sleep(delay)
        secondReading = self._getVBoxVMachinesNetworkInfo()
        return self._getAllNicRatesfromTwoReadings(firstReading, secondReading, delay)

    def _calculatePhysicalSizeOfRaid(self, devices):
        """
        Calculate the RAID physical size of total used partitions
        
        @param devices: list of devices
        @return: int
        """
        size = 0.0
        for dev in devices:
            dev = dev.split('/')[-1]
            dev, number = dev[:-1], dev[-1]
            for part in [part for part in j.cmdtools.partitioninfo.infoParted(dev) if part['number'] == number]:
                unit = part['size'][-2:]
                partSize = float(part['size'][:-2])
                if unit == 'MB':
                    partSize = partSize / 1024
                size += partSize
        return size * 1024

    def _getDssBlkDevices(self, path='/dev/dssblk'):
        dssBlkDevices = []
        if j.system.fs.exists(path):
            _, devices = j.system.process.execute('ls %s' % path)
            dssBlkDevices = devices.splitlines()
        return dssBlkDevices
