from JumpScale import j
import os

try:
    import parted
except:
    j.system.platform.ubuntu.install("python-parted")
    import parted

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

    def partitionsFind(self,busy=None,ttype=None,ssd=None,prefix="sd",minsize=30,maxsize=5000):
        """
        looks for disks which are know to be data disks & are formatted ext4
        return [[$partpath,$size,$free,$ssd]]
        @param ssd if None then ssd and other
        """
        result=[]
        import parted
        import psutil
        p=parted.disk.parted
        result=[]
        for dev in parted.getAllDevices():
            path=dev.path
            geom = dev.hardwareGeometry;
            ssize = dev.sectorSize;
            size = (geom[0] * geom[1] * geom[2] * ssize) / 1000 / 1000 / 1000;
            size2=dev.getSize()
            model=dev.model
            ssd0=int(j.system.fs.fileGetContents("/sys/block/%s/queue/rotational"%dev.path).strip())==0
            if ssd==None or ssd0==ssd:
                if busy==None or dev.busy==busy:
                    if path.find("/dev/%s"%prefix)==0:
                        #sata disk                    
                        disk = parted.Disk(dev)
                        primary_partitions = disk.getPrimaryPartitions()
                        for partition in primary_partitions:
                            # print "Partition: %s" % partition.path
                            size=round(partition.getSize(unit="gb"),2)
                            try:
                                fs = parted.probeFileSystem(partition.geometry)
                            except:
                                fs = "unknown"
                            print "PART:%s Size: %s GB, Filesystem: %s" % (path,size,fs)
                            # print "Start: %s End: %s" % (partition.geometry.start,partition.geometry.end)
                            if (ttype==None or fs==ttype) and size>minsize and size<maxsize:
                                stats=os.statvfs(partition.path)
                                free=round(float(stats.f_bfree)/float(stats.f_blocks)*size,2)
                                print "FOUND PART:%s %s %s %s"%(partition.path,size,free,ssd0)
                                result.append((partition.path,size,free,ssd0))

                            
                                cmd="mount %s /mnt/tmp"%path
                                j.system.process.execute(cmd)
                                hrdpath="/mnt/tmp/disk.hrd"
                                if j.system.fs.exists(hrdpath):
                                    hrd=j.core.hrd.getHRD(hrdpath)
                                    partnr=hrd.get("diskinfo.partnr")
                                    gid=hrd.get("diskinfo.gid")
                                    print "found data disk:%s %s %s %s %s %s"%(partition.path,gid,partnr,size,free,ssd)
                                    result.append((partition.path,gid,partnr,size,free))
                                cmd="umount /mnt/tmp"
                                j.system.process.execute(cmd)
                                if os.path.ismount("/mnt/tmp")==True:
                                    raise RuntimeError("/mnt/tmp should not be mounted")

        return result  

    def partitionsFind_Ext4Data(self):
        """
        looks for disks which are know to be data disks & are formatted ext4
        return [[$partpath,$gid,$partid,$size,$free]]
        """
        result=[]
        for path,size,free,ssd in self.partitionsFind(busy=False,ttype="ext4",ssd=False,prefix="sd",minsize=300,maxsize=5000):
            
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
 