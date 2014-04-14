from JumpScale import j
import os
import errno
import stat


def _is_block(file):
    try:
        st = os.stat(file)
    except OSError, err:
        if err.errno == errno.ENOENT:
            return False
        raise
    return stat.S_ISBLK(st.st_mode)

def get_open_blks(pid):
    retlist = set()
    files = os.listdir("/proc/%s/fd" % pid)
    hit_enoent = False
    for fd in files:
        file = "/proc/%s/fd/%s" % (pid, fd)
        if os.path.islink(file):
            try:
                file = os.readlink(file)
            except OSError, err:
                if err.errno == errno.ENOENT:
                    hit_enoent = True
                    continue
                raise
            else:
                if file.startswith('/') and _is_block(file):
                    retlist.add(int(fd))
    if hit_enoent:
        # raise NSP if the process disappeared on us
        os.stat('/proc/%s' % pid)
    return retlist

try:
    import parted
except:
    j.system.platform.ubuntu.install("python-parted")
    import parted

#patch parted
_orig_getAllDevices = parted.getAllDevices
def _patchedGetAllDevices():
    pid = os.getpid()
    fds = get_open_blks(pid)
    try:
        return _orig_getAllDevices()
    finally:
        afds = get_open_blks(pid)
        for fd in afds.difference(fds):
            os.close(fd)

parted.getAllDevices = _patchedGetAllDevices

class Disk():
    """
    identifies a disk in the grid
    """

    def __init__(self):
        self.id=0
        self.path = ""
        self.size = ""
        self.free = ""
        self.ssd=False
        self.fs=""
        self.mounted=False
        self.mountpoint=""
        self.model=""
        self.description=""
        self.type=[]

    def __str__(self):
        return "%s %s %s free:%s ssd:%s fs:%s model:%s id:%s"%(self.path,self.mountpoint,self.size,self.free,self.ssd,self.fs,self.model,self.id)

    __repr__=__str__

class Diskmanager(): 
    def partitionAdd(self,disk, free, align=None, length=None, fs_type=None, type=parted.PARTITION_NORMAL):
        start = free.start
        if length:
            end = start + length - 1
        else:
            end = free.end
            length = free.end - start + 1
     
        if not align:
            align = disk.partitionAlignment.intersect(disk.device.optimumAlignment)
     
        if not align.isAligned(free, start):
            start = align.alignNearest(free, start)
     
        end_align = parted.Alignment(offset=align.offset - 1, grainSize=align.grainSize)
        if not end_align.isAligned(free, end):
            end = end_align.alignNearest(free, end)
     
        geometry = parted.Geometry(disk.device, start=start, end=end)
        if fs_type:
            fs = parted.FileSystem(type=fs_type, geometry=geometry)
        else:
            fs = None
        partition = parted.Partition(disk, type=type, geometry=geometry, fs=fs)
        constraint = parted.Constraint(exactGeom=partition.geometry)
        disk.addPartition(partition, constraint)
        return partition
     
    def diskGetFreeRegions(self,disk, align):
        """Get a filtered list of free regions, excluding the gaps due to partition alignment"""
        regions = disk.getFreeSpaceRegions()
        new_regions = []
        for region in regions:
            if region.length > align.grainSize:
                new_regions.append(region)
        return new_regions
     
    def _kib_to_sectors(self,device, kib):
        return parted.sizeToSectors(kib, 'KiB', device.sectorSize)

    def mirrorsFind(self):
        cmd="cat /proc/mdstat"
        rcode,out=j.system.process.execute(cmd)
        return out

    def partitionsFind(self,mounted=None,ttype=None,ssd=None,prefix="sd",minsize=5,maxsize=5000,devbusy=None,\
            initialize=False,forceinitialize=False):
        """
        looks for disks which are know to be data disks & are formatted ext4
        return [[$partpath,$size,$free,$ssd]]
        @param ssd if None then ssd and other
        """
        import parted
        import JumpScale.grid.osis
        import psutil
        result=[]
        mounteddevices = psutil.disk_partitions()

        def getpsutilpart(partname):
            for part in mounteddevices:
                if part.device==partname:
                    return part
            return None

        for dev in parted.getAllDevices():
            path=dev.path
            #ssize = dev.sectorSize;
            # size = (geom[0] * geom[1] * geom[2] * ssize) / 1000 / 1000 / 1000;
            # size2=dev.getSize()

            if devbusy==None or dev.busy==devbusy:
                if path.startswith("/dev/%s"%prefix):
                    try:
                        disk = parted.Disk(dev)
                        partitions = disk.partitions
                    except parted.DiskLabelException:
                        partitions = list()
                    for partition in partitions:
                        disko=Disk()
                        disko.model = dev.model
                        disko.path=partition.path if disk.type != 'loop' else disk.device.path
                        disko.size=round(partition.getSize(unit="mb"),2)
                        disko.free = 0
                        print "partition:%s %s"%(disko.path,disko.size)
                        try:
                            fs = parted.probeFileSystem(partition.geometry)
                        except:
                            fs = "unknown"

                        disko.fs=fs
                        partfound=getpsutilpart(disko.path)
                        mountpoint=None
                        if partfound==None and mounted<>True:
                            mountpoint="/mnt/tmp"
                            cmd="mount %s /mnt/tmp"%partition.path
                            rcode,output=j.system.process.execute(cmd,ignoreErrorOutput=False,dieOnNonZeroExitCode=False,)
                            if rcode<>0:
                                #mount did not work
                                mountpoint==None

                            disko.mountpoint=None
                            disko.mounted=False
                        elif partfound:
                            mountpoint=partfound.mountpoint
                            disko.mountpoint=mountpoint
                            disko.mounted=True

                        pathssdcheck="/sys/block/%s/queue/rotational"%dev.path.replace("/dev/","").strip()
                        ssd0=int(j.system.fs.fileGetContents(pathssdcheck))==0
                        disko.ssd=ssd0   
                        result.append(disko)

                        if mountpoint<>None:
                            print "mountpoint:%s"%mountpoint
                            size, used, free, percent=psutil.disk_usage(mountpoint)
                            disko.free=disko.size*float(1-percent/100)

                            size=disko.size / 1024
                            disko.free=int(disko.free)

                            if (ttype==None or fs==ttype) and size>minsize and (maxsize is None or size<maxsize):
                                if ssd==None or disko.ssd==ssd:
                                    # print disko
                                    hrdpath="%s/disk.hrd"%mountpoint

                                    if j.system.fs.exists(hrdpath):
                                        hrd=j.core.hrd.getHRD(hrdpath)
                                        partnr=hrd.getInt("diskinfo.partnr")
                                        if partnr==0 or forceinitialize:
                                            j.system.fs.remove(hrdpath)

                                    if not j.system.fs.exists(hrdpath) and initialize:
                                        C="""
diskinfo.partnr=
diskinfo.gid=
diskinfo.nid=
diskinfo.type=
diskinfo.epoch=
diskinfo.description=
"""
                                        j.system.fs.writeFile(filename=hrdpath,contents=C)
                                        hrd=j.core.hrd.getHRD(hrdpath)
                                        hrd.set("diskinfo.description",j.console.askString("please give description for disk"))
                                        hrd.set("diskinfo.type",",".join(j.console.askChoiceMultiple(["BOOT","CACHE","TMP","DATA","OTHER"])))
                                        hrd.set("diskinfo.gid",j.application.whoAmI.gid)
                                        hrd.set("diskinfo.nid",j.application.whoAmI.nid)
                                        hrd.set("diskinfo.epoch",j.base.time.getTimeEpoch())


                                        masterip=j.application.config.get("grid.master.ip")
                                        client = j.core.osis.getClient(masterip,user="root")
                                        client_disk=j.core.osis.getClientForCategory(client,"system","disk")

                                        disk=client_disk.new()
                                        for key,val in disko.__dict__.iteritems():
                                            disk.__dict__[key]=val

                                        disk.description=hrd.get("diskinfo.description")
                                        disk.type=hrd.get("diskinfo.type").split(",")
                                        disk.type.sort()
                                        disk.nid=j.application.whoAmI.nid
                                        disk.gid=j.application.whoAmI.gid


                                        guid,new,changed=client_disk.set(disk)
                                        disk=client_disk.get(guid)
                                        diskid=disk.id
                                        hrd.set("diskinfo.partnr",diskid)
                                    if j.system.fs.exists(hrdpath):
                                        # hrd=j.core.hrd.getHRD(hrdpath)
                                        disko.id=hrd.get("diskinfo.partnr")
                                        disko.type=hrd.get("diskinfo.type").split(",")
                                        disko.type.sort()
                                        disko.description=hrd.get("diskinfo.description")
                                        print "found disk:\n%s"%(disko)
                                    cmd="umount /mnt/tmp"
                                    j.system.process.execute(cmd,dieOnNonZeroExitCode=False)
                                    if os.path.ismount("/mnt/tmp")==True:
                                        raise RuntimeError("/mnt/tmp should not be mounted")

        return result

    def partitionsFind_Ext4Data(self):
        """
        looks for disks which are know to be data disks & are formatted ext4
        return [[$partpath,$gid,$partid,$size,$free]]
        """
        result=[item for item in self.partitionsFind(busy=False,ttype="ext4",ssd=False,prefix="sd",minsize=300,maxsize=5000)]
        return result       

    def partitionsMount_Ext4Data(self):
        for path,gid,partnr,size,free,ssd in self.partitionsFind_Ext4Data():
            mntdir="/mnt/datadisks/%s"%partnr
            j.system.fs.createDir(mntdir)
            cmd="mount %s %s"%(path,mntdir)
            j.system.process.execute(cmd)

    def partitionsUnmount_Ext4Data(self):
        partitions=self.partitionsGet_Ext4Data()
        for partid,size,free in partitions:
            mntdir="/mnt/datadisks/%s"%partnr
            cmd="umount %s"%(mntdir)
            j.system.process.execute(cmd)

    def partitionsGetMounted_Ext4Data(self):
        """
        find disks which are mounted
        @return [[$partid,$size,$free]]
        """
        from IPython import embed
        print "DEBUG NOW iiiiii"
        embed()
        


        from IPython import embed
        print "DEBUG NOW partitionsGet_Ext4Data"
        embed()
 
