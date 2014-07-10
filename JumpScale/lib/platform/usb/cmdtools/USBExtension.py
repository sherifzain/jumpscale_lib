import cPickle as pickle
from JumpScale import j


class logger:
    _LOG_STATEMENT = ""

    def __init__(self, logStatement):
        self._LOG_STATEMENT = logStatement

    def log(self, msg):
        """
        Function to log errors, messages

        @param msg: message to log
        @type  msg: string
        """
        msg = self._LOG_STATEMENT + " " + str(msg)
        j.logger.log(msg)


class USB:
    _USB_DEVICE_PATH = '/tmp/.usb'
    _EXTENSION = '.p'
    _LOGGER = logger("USB Extension (USB):")
    _PREFIX = 'CLOUDDISK_'
    model = ""
    serial = ""
    devicename = ""
    label = ""
    part_table_type = ""
    partitionName = ""
    size = ""
    speed = ""
    vendor = ""
    _filename = ""
    filesystem = ""
    mountpoint = ""

    def _prereq(self):
        if not j.system.fs.exists(self._USB_DEVICE_PATH):
            j.system.fs.createDir(self._USB_DEVICE_PATH)

    def __init__(self, *args, **kwargs):
        self._prereq()
        filename = kwargs.get('filename', "")
        model = kwargs.get('model', "")
        serial = kwargs.get('serial', "")
        devicename = kwargs.get('devicename', "")
        label = kwargs.get('label', "")
        size = kwargs.get('size', "")
        speed = kwargs.get('speed', "")
        vendor = kwargs.get('vendor', "")
        part_table_type = kwargs.get('part_table_type', "")
        if filename:
            if filename.find("/") != -1:
                filename = j.system.fs.getBaseName(filename)
            if filename.find(self._PREFIX) == -1:
                filename = self._PREFIX + filename
            if filename[-2:] != self._EXTENSION:
                filename = filename + self._EXTENSION
            filename = self._USB_DEVICE_PATH + "/" + filename
            if not j.system.fs.exists(filename):
                self._LOGGER.log('File %s does not exist.' % filename)
                return None
            try:
                usbDeviceInfo = pickle.load(open(filename, 'rb'))
            except Exception as ex:
                self._LOGGER.log("Opening of file %s failed with exception %s" % (filename, ex))
                return None
            self.model = usbDeviceInfo.get("model", "")
            self.serial = usbDeviceInfo.get("serial", "")
            self.devicename = usbDeviceInfo.get("devicename", "")
            self.label = usbDeviceInfo.get("label", "")
            self.size = usbDeviceInfo.get("size", "")
            self.speed = usbDeviceInfo.get("speed", "")
            self.vendor = usbDeviceInfo.get("vendor", "")
            self.part_table_type = usbDeviceInfo.get("part_table_type", "")
            self.mountpoint = usbDeviceInfo.get("mountpoint", "")
            self._filename = filename
        elif devicename:
            if label.find(self._PREFIX) is -1:
                label = self._PREFIX + label
            if not j.system.fs.exists(devicename):
                self._LOGGER.log('Device %s does not exist' % devicename)
                return
            self.model = model
            self.serial = serial
            self.devicename = devicename
            self.label = label
            self.size = size
            self.speed = speed
            self.vendor = vendor
            self.part_table_type = part_table_type
            self._filename = self._USB_DEVICE_PATH + "/" + self.label + self._EXTENSION
            self.save()

    def save(self):
        try:
            usbInfo = {'model':   self.model,
                       'serial':   self.serial,
                       'devicename':   self.devicename,
                       'label':   self.label,
                       'size':   self.size,
                       'speed':   self.speed,
                       'vendor':   self.vendor,
                       'part_table_type':   self.part_table_type,
                       'mountpoint':   self.mountpoint
                       }
            pickle.dump(usbInfo, open(self._filename, 'wb'))
            return True
        except Exception as ex:
            self._LOGGER.log('Saving USB device failed for {0} with exception {1} '.format(self.label, ex))
        return False

    def remove(self):
        try:
            j.system.fs.remove(self._filename)
        except Exception as ex:
            self._LOGGER.log('USB device removal for {0} failed with exception {1}'.format(self.label, ex))
            return False
        return True


class USBExtension:

    """
    Class that holds commands for USB devices (command-line like)

    @attention : _add and _removeUSBdevice add/remove information
                 about USB devices into a binary-pickle file under /tmp/.usb,
                 which will be REMOVED when the system is REBOOTED!!!
    """
    _LOGGER = logger('USB Extension:')
    _USB_DEVICE_PATH = '/tmp/.usb/{0}'
    _EXTENSION = '.p'
    _MOUNTPOINT = '/mnt/usb/{0}'

    def _parseDF(self, usb):
        """
        Function to parse the output of the df command on UNIX platforms.
        @param usb            : The usb device object
        @type  usb            : USB

        @return           : a dictionary of used, available, total space of the usb
        @rtype            : dictionary
        """
        try:
            spaceInfo = []
            partitions = self.getPartitionInfo(usb)
            for partition in partitions:
                pmountpoint = j.system.fs.joinPaths(usb.mountpoint, "%s%s" % (j.system.fs.getBaseName(usb.devicename), partition['number']))
                command = 'df -m {0}'.format(pmountpoint)
                exitcode, output = j.system.process.execute(command)
                dictOfSpace = {}
                if output:
                    data = output.splitlines()[1]
                    dev, size, used, available, percentage, mountpoint = data.split()
                    dictOfSpace.setdefault("device", dev)
                    dictOfSpace.setdefault("size", int(size))
                    dictOfSpace.setdefault("used", int(used))
                    dictOfSpace.setdefault("available", int(available))
                    dictOfSpace.setdefault("percentage", percentage)
                    dictOfSpace.setdefault("mountpoint", mountpoint)
                    spaceInfj.append(dictOfSpace)
        except Exception as ex:
            self._LOGGER.log('USB device not mounted, failed with exception {0}'.format(ex))
            print ex
            return []
        return spaceInfo

    def _add(self, model, serial, devicename, label, size, speed, vendor, part_table_type=""):
        """
        Adds a new USB device object.
        Auto-receives arguments when you plug in an USB device .

        @param model           : model of the USB device;
        @type  model           : string
        @param serial          : short serial of USB device
        @type  serial          : string
        @param devicename      : device name as specified in /dev (eg. /dev/sdf)
        @type  devicename      : string
        @param label           : label of the USB device (eg. 'CLOUDDISK_'); if not specified
        @type  label           : string
        @param part_table_type : partition table type as listed by the kernel
        @type  part_table_type : string
        @param size            : size of the USB device in blocks
        @type  size            : string
        @param speed           : speed of the USB device;
        @type  speed           : string
        @param vendor          : vendor name
        @type  vendor          : string

        @return                : Will return True in case of success, False otherwise.
        @rtype                 : boolean
        """
        try:
            usbSize = int(size) / 2 / 1000
            if devicename.find('dev') == -1:
                self._LOGGER.log('Could not add device %s expected a dev path. Please unplug and plug it back in again' % devicename)
                return False
            usbArgs = {'vendor': vendor,
                       'model': model,
                       'serial': serial,
                       'devicename': devicename,
                       'label': label,
                       'mountpoint': "",
                       'size': usbSize,           # in megabytes
                       'speed': speed,
                       'partitiontabletype': part_table_type,
                       'partitionname': devicename + '1',
                       'filesystem': ""
                       }
            USB(**usbArgs)
            return True
        except Exception as ex:
            self._LOGGER.log('New USB device failed for {0} with exception {1} '.format(label, ex))
            return False

    def _remove(self, usbdevice):
        """
        Remove the USB device object and corresponding resources.
        @param usbdevice : usb string reference holding the label e.g. sdi
        @type  usbdevice : string
        @return          : Success or failure in form of True or False
        @rtype           : boolean
        """
        usb = USB(filename=usbdevice)
        if not usb:
            self._LOGGER.log("Remove failed")
            return False
        try:
            if self.isMounted(usb):
                self.umount(usb)
        except Exception:
            pass
        try:
            result = usb.remove()
        except Exception as ex:
            self._LOGGER.log('USB device removal for {0} failed with exception {1}'.format(usb.devicename, ex))
            result = False
        return result

    def getSpaceInfo(self, usb):
        """"
        Retrieve information regarding space availability of the USB device.
        @param usb            : The usb device object
        @type  usb            : USB

        @return               : A dictionary with the amount of space in megabytes on the device
        @rtype                : dictionary
        """
        if self.isMounted(usb) or self.mount(usb):
            return self._parseDF(usb)

    def getFreeSpace(self, usb):
        """
        Get the amount of free space on an USB device.
        @param usb            : The usb device object
        @type  usb            : USB

        @return               : The amount of free space in megabytes for each partition
        @rtype                : dictionary
        """
        if not self.isMounted(usb):
            self._LOGGER.log('Cannot get spatial information when the device is not mounted')
            return {}
        spaceInfo = self.getSpaceInfo(usb)
        if spaceInfo:
            availableSpace = {}
            for partition in spaceInfo:
                partitionName = j.system.fs.getBaseName(partition.get('device', ""))
                availableSpace[partitionName] = partition['available']
            return availableSpace
        else:
            return {}

    def format(self, usb, partitionnr=1, fstype='ntfs', label=None, compression=False):
        """
        Format USB device.
        Be careful when using this function, as it deletes EVERYTHING. (e.g data, partitions)
        @param usb            : The usb device object
        @type  usb            : USB
        @param partitionnr    : The number of the partition to format (1, 2, 3 ..)
        @type partitionnr     : int
        @param fstype         : File system to use when formatting (ext4, ntfs)
        @type fstype          : string
        @param label          : Identifier for the file system used in formatting
        @string label         : string
        @param compression    : Flag to determine if the file system should use compression
        @type compression     : boolean
        @param quick          : Flag to determine if the file system should be quickly formatted.
        @type quick           : boolean

        @return               : Success of failure in form of True or False respectively
        @rtype                : boolean
        """

        device = j.system.fs.getBaseName(usb.devicename)

        if not j.cmdtools.disktools.parted.getPartitions(device):
            shellError = 'No partition on device {0}'.format(usb.devicename)
            message = 'Formatting {0} failed with exception: {1}'.format(usb.devicename, shellError)
            self._LOGGER.log(message)
            return False

        device = usb.devicename + str(partitionnr)
        if not j.system.fs.exists(device):
            self._LOGGER.log('Device %s does not exists. Format cannot be performed.' % device)
            return False

        command = 'mkfs -t {0} {1} {2} {3}'.format(fstype,
                                                   '-C' if compression else '',
                                                   '-L "%s"' % label if label else '',
                                                   device)
        try:
            exCode, out = j.system.process.execute(command=command)
            usb.filesystem = fstype.upper()
            return usb.save()
        except Exception as ex:
            self._LOGGER.log('Formating of {0} failed with exception {1}'.format(usb.devicename, ex))
        return False

    def partition(self, usb, size=None, fsType='NTFS'):
        """
        Create partition on USB device; by default only one partition per USB device.
        @param usb            : The usb device object
        @type  usb            : USB
        @param size           : Size of the new partition in MB. Using the default value, a partition of all available size will be created.
        @type size            : int
        @return               : True / False
        @rtype                : boolean
        """
        valid_fstype = ['fat16',
                        'fat32',
                        'ext2',
                        'HFS',
                        'NTFS',
                        'reiserfs',
                        'ufs']
        if fsType not in valid_fstype:
            self._LOGGER.log("Invalid fsType argument given valid  types are %s" % valid_fstype)
            return False
        try:
            if self._verifyDevice(usb):
                device = j.system.fs.getBaseName(usb.devicename)
                partitions = j.cmdtools.disktools.parted.getPartitions(device)
                size = int(size) * 1024 if size else None

                freeSpace = j.cmdtools.disktools.parted.getFreeSpace(device)
                freeSpaceValues = map(lambda val: self._convertToKB(val), freeSpace) if freeSpace else []

                if not freeSpaceValues or freeSpaceValues[2] <= 1024:
                    self._LOGGER.log("No more space available on device %s" % usb.devicename)
                    return False
                if size and size > freeSpaceValues[2]:
                    self._LOGGER.log("The size of the new partition exceeds the space available on device %s" % usb.devicename)
                    return False
                begin = freeSpaceValues[0] / 1024
                end = freeSpaceValues[1] / 1024 if not size else (freeSpaceValues[0] + size) / 1024
                command = "parted %s -s mklabel gpt;" % usb.devicename if not partitions else ""
                command += "parted %s -s unit compact mkpart primary %s %s %s" % (usb.devicename, fsType, begin, end)
                exCode, output = j.system.process.execute(command)
                usb.part_table_type = fsType
                return usb.save()
        except Exception as ex:
            self._LOGGER.log('Partitioning of {0} failed with exception: {1}'.format(usb.devicename,
                                                                                     ex))
        return False

    def getFilesystem(self, usb):
        """
        Return the file system of the USB device as seen set in the partition type (e.g. NTFS, ext4, etc.).
        @param usb            : The usb device object
        @type  usb            : USB

        @return : the type of the file system for each partition of the USB device
        @rtype  : dictionary
        """
        partitions = self.getPartitionInfo(usb)
        fsInfo = {}
        if not partitions:
            return fsInfo
        for partition in partitions:
            partitionName = "%s%s" % (j.system.fs.getBaseName(usb.devicename), partition['number'])
            fsInfo[partitionName] = partition.get('Type', "")
        return fsInfo

    def list(self):
        """
        List the USB devices present in the system

        @return  : Returns a list of USB devices detected by udev rule
        @rtype   : list
        """
        def dirlister(arg, path):
            if path[-2:] == self._EXTENSION:
                arg.append(path)

        paths = []
        usbs = []
        try:
            j.system.fswalker.walk(self._USB_DEVICE_PATH.format(''), dirlister, paths, recursive=False)
        except Exception as ex:
            self._LOGGER.log('While trying to list the devices encountered exception: %s' % ex)
        for path in paths:
            args = {'filename': path}
            usbs.append(USB(**args))
        return usbs

    def mount(self, usb):
        """
        Mount the device under /mnt/usb/ on a folder with the device label
        @param usb            : The usb device object
        @type  usb            : USB

        @return              : returns True if successfully mounted or False if problems
        @rtype               : boolean
        """
        if not self.isMounted(usb):
            try:
                if not j.system.fs.exists(self._MOUNTPOINT.format("")):
                    j.system.fs.createDir(self._MOUNTPOINT.format(""))
                mountpoint = self._MOUNTPOINT.format(usb.label)
                partitions = self.getPartitionInfo(usb)
                if not len(partitions):
                    self._LOGGER.log("The usb device has no partitions. Cannot continue.")
                    return False
                for partition in partitions:
                    device = usb.devicename + partition['number']
                    pmountpoint = j.system.fs.joinPaths(mountpoint, "%s%s" % (j.system.fs.getBaseName(usb.devicename), partition['number']))
                    fsType = partition.get('Type', "")
                    if fsType in ("fat16", "fat32"):
                        fsType = "vfat"
                    if not j.system.fs.exists(device):
                        self._LOGGER.log("Device %s is not preset. Cannot continue. Mount will fail." % device)
                        return False
                    if not pmountpoint in j.system.fs.listDirsInDir(self._MOUNTPOINT.format('')):
                        j.system.fs.createDir(pmountpoint)
                    if fsType:
                        j.cmdtools.disktools.mount(device, pmountpoint, fsType)
                    else:
                        j.cmdtools.disktools.mount(device, pmountpoint)
                usb.mountpoint = mountpoint
                return usb.save()
            except Exception as ex:
                self._LOGGER.log("Mount of device {0} failed with exception {1}".format(device, ex))
        else:
            self._LOGGER.log('USB {0} device already mounted!'.format(usb.devicename))
        return False

    def umount(self, usb):
        """
        Unmount the device named
        @param usb            : The usb device object
        @type  usb            : USB

        @return              : returns True if successfully unmounted or False if problems
        @rtype               : boolean
        """
        if not self.isMounted(usb):
            self._LOGGER.log('Device {0} not mounted!'.format(usb.label))
            return False
        partitions = self.getPartitionInfo(usb)
        mountpoint = usb.mountpoint if usb.mountpoint else self._MOUNTPOINT.format(usb.label)
        for partition in partitions:
            pmountpoint = j.system.fs.joinPaths(mountpoint, "%s%s" % (j.system.fs.getBaseName(usb.devicename), partition['number']))
            if not j.system.fs.isMount(pmountpoint):
                continue
            try:
                j.cmdtools.disktools.umount(pmountpoint)
            except Exception as ex:
                self._LOGGER.log(
                    "Unmount of device {0}, partition {1} failed with exception {2}. Trying a lazy and forced unmount".format(usb.label, partition['number'], ex))
                try:
                    j.cmdtools.disktools.umount(pmountpoint, '-l -f')
                except Exception as ex2:
                    self._LOGGER.log(
                        "Unmount of device {0} partition {1} failed with exception {2} while trying a lazy forced unmount".format(usb.label, partition['number'], ex2))
                    return False
            try:
                j.system.fs.removeDir(pmountpoint)
            except Exception as ex:
                self._LOGGER.log('Removing mount point directory %s failed.' % pmountpoint)
        usb.mountpoint = ""
        return usb.save()

    def isMounted(self, usb):
        """
        Check if USB Mass Storage Device is mounted
        @param usb            : The usb device object
        @type  usb            : USB

        @return              : True/False if device is mounted
        @rtype               : boolean
        """
        partitions = self.getPartitionInfo(usb)
        mountpoint = usb.mountpoint if usb.mountpoint else self._MOUNTPOINT.format(usb.label)
        for partition in partitions:
            pmountpoint = j.system.fs.joinPaths(mountpoint, "%s%s" % (j.system.fs.getBaseName(usb.devicename), partition['number']))
            if j.system.fs.isMount(pmountpoint):
                return True
        return False

    def getPartitionInfo(self, usb):
        """
        Returns a dictionary of the partitions on the USB device selected
        @param usb            : The usb device object
        @type  usb            : USB

        @return               : information about partitions found on the selected device
        @rtype                : list
        """
        return j.cmdtools.partitioninfo.infoParted(usb.devicename[5:])

    def _parseSerial(self, usb):
        """
        Get the serial for the devices as recorded by udev. In case this is not possible it will return 0
        @param usb            : The usb device object
        @type  usb            : USB

        @return               : serial of usb device
        @rtype                : string
        """
        command = "udevadm info --query=property --name %s | awk -F '=' '/ID_SERIAL_SHORT/{print $2}'" % usb.devicename
        exitCode, serial = j.system.process.execute(command=command,
                                                    dieOnNonZeroExitCode=False)
        if exitCode != 0:
            self._LOGGER.log('Parse serial failed, could not retrieve information from the udevadm command.')
            return 0
        return serial.strip("\n")

    def _verifyDevice(self, usb, strict=False):
        """
        Verify device is often called to assure that actions can run on devices
        When there is something wrong false is returned
        @param usb            : The usb device object
        @type  usb            : USB

        @return               : Success or failure in form of True or False respectively
        @rtype                : boolean
        """
        serial = self._parseSerial(usb)
        if serial != usb.serial:
            self._LOGGER.log('Could not retrieve serial of the device or the device is not the same!')
            if strict:
                return false
        return j.system.fs.exists(usb.devicename)

    def _convertToKB(self, size):
        """
        Convert given size to KB
        @param size           : Size to convert e.g '1000MB', '10GB'...
        @type size            : string

        @return               : Size in KB
        @rtype                : int
        """
        try:
            sizeValue = int(filter(lambda c: c.isdigit(), size))
            unit = size.split(str(sizeValue))[1]
            if unit == 'GB':
                sizeValue = sizeValue * 1024 * 1024
            elif unit == 'MB':
                sizeValue = sizeValue * 1024
            elif unit == 'kb':
                sizeValue = (sizeValue / 1032) * 1024
        except Exception as ex:
            self._LOGGER.log('Invalid size provided !')
            return 0
        return sizeValue
