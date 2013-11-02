from JumpScale import j
from ClusterSSHClient import ClusterSSHClient
import random


class ClusterNode():

    def __init__(self, cluster):
        self.hostname = ""
        self.ipaddr = ""
        self.cluster = cluster
        self.isPreparedForSSODebug = False
        self.ubuntuPackagesUpdated = False
        self.ubuntuPackagesInstalled = []
        self.sshclient = ClusterSSHClient(cluster, self)

    def execute(self, commands, dieOnError=True, silent=False, timeout=60):
        j.transaction.start("Execute %s on node %s %s" % (commands, self.hostname, self.ipaddr), silent=silent)
        exitcode, output, error = self.sshclient.execute(commands, dieOnError=False, timeout=timeout)
        j.transaction.stop()
        return [exitcode, output, error]

    def executeQshell(self, commands, dieOnError=True, silent=False, timeout=60):
        if not commands:
            raise RuntimeError('Commands is empty!')
        print 'COMMANDS: ' + commands
        j.transaction.start("Execute qshellcmd %s on node %s %s" % (commands, self.hostname, self.ipaddr), silent=silent)
        tmpfilepath = j.system.fs.getTmpFilePath()

        #
        # p = """ some texts %s blabla """ % 'insert me'
        # does not work so we do a replace.
        template = """
from JumpScale.core.InitBase import *

j.application.start("qshellexecute")

j.logger.maxlevel=6 #to make sure we see output from SSH sessions 
j.logger.consoleloglevel=2
j.application.shellconfig.interactive=False
$COMMANDS
j.application.stop()
"""
        commands = template.replace('$COMMANDS', commands)

        j.system.fs.writeFile(tmpfilepath, commands)
        self.sendfile(tmpfilepath, tmpfilepath)
        result = self.sshclient.execute("/opt/qbase6/qshell -f %s" % tmpfilepath, dieOnError, timeout=timeout)
        j.system.fs.remove(tmpfilepath)
        j.transaction.stop()
        return [0, result, ""]

    def sendfile(self, source, dest):
        j.transaction.start("send file %s to %s on %s" % (source, dest, self.ipaddr))
        ftp = self.getSftpConnection()
        if not j.system.fs.exists(source):
            raise RuntimeError("Could not find source file %s" % source)

        # If source == dest and we are on localhost and we do a put, the end result will be that the source files has been emptied
        # we we check here and do nothing in that case
        if source == dest and j.system.net.checkIpAddressIsLocal(self.ipaddr):
            pass  # do nothing
        else:
            ftp.put(source, dest)
        # trying to fix problem paramico wait_for_event() SSHException: Channel closed.
        # ftp.close() # Closing the connecrions did not work, now trying to keep the same connection open
        j.transaction.stop()
        return [0, "", ""]

    def ping(self):
        return [0, j.system.net.pingMachine(self.ipaddr, 5), ""]

    def sshtest(self):
        return [0, self.sshclient.sshtest(), ""]

    def connect(self):
        return [0, self.sshclient.connect(), ""]

    def activateAvahi(self):
        self.prepare(avahiInstallOnly=True)

    def prepare(self, avahiInstallOnly=False, ignoreUpgradeError=False):
        """
        prepare a node for cluster operation
        uses ssh
        only works for ubuntu        
        """
        return
        content = """<?xml version=\"1.0\" standalone=\'no\'?>
<!--*-nxml-*-->
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<!-- $Id$ -->
<service-group>
<name replace-wildcards="yes">daascluster %h</name>

<service>
<type>_daascluster._tcp</type>
<port>9999</port>
</service>

<service>
<type>_ssh._tcp</type>
<port>22</port>
</service>

</service-group>
"""
        content = content.replace("daascluster", self.cluster.domainname.replace(".", "__"))
        tmpfile = j.system.fs.joinPaths(j.dirs.tmpDir, "avahi")
        j.system.fs.writeFile(tmpfile, content)

        j.transaction.start("Try to configure nodes for cluster usage (will use SSH to do so).")
        j.transaction.start("Ping machine %s" % self.ipaddr)
        if not j.system.net.pingMachine(self.ipaddr, 5):
            j.console.echo("ERROR: Could not ping to machine %s, please check machine is reacheable." % self.ipaddr)
            j.transaction.stop()
        else:
            j.transaction.stop()  # ping
            ##j.transaction.start("Open SSH connection to %s" %self.ipaddr)
            # sshclient=j.clients.ssh.createClient(ipaddr,"root",rootpasswd,60)
            if avahiInstallOnly == False:
                j.transaction.start("Upgrade ubuntu on %s to newest packages, this can take a long time (apt-get update & upgrade)." % self.ipaddr)
                self.execute("apt-get update", False)
                #returncode,stdout,stderr=self.execute("apt-get upgrade -y",False)
                # if returncode>0:
                    # if not ignoreUpgradeError or j.application.shellconfig.interactive==False or not j.console.askYesNo("Could not upgrade system, do you want to ignore and continue?"):
                        #raise "Could not upgrade system (apt-get upgrade), probably because there was interactivity required."
                j.transaction.start("Install mc on %s" % self.ipaddr)
                self.execute("apt-get install mc -y")
                j.transaction.stop()
                j.transaction.stop()
            else:
                j.transaction.start("Update ubuntu package metadata on %s (apt-get update)." % self.ipaddr)
                self.execute("apt-get update", False)
                j.transaction.stop()

            j.transaction.start("Install avahi on %s" % self.ipaddr)
            self.execute("apt-get install avahi-daemon avahi-utils -y", False)
            self.execute("mkdir -p /etc/avahi/services")
            ftp = self.getSftpConnection()
            j.logger.log("put %s to /etc/avahi/services/daascluster.service" % tmpfile)
            ftp.put(tmpfile, "/etc/avahi/services/daascluster.service")
            j.transaction.stop()  # reload avahi
            j.transaction.start("Reload Avahi Config")
            self.execute("avahi-daemon --reload")
            j.transaction.stop()  # end of avahi
            j.transaction.start("Disable ssh name resolution")
            self.execute("echo 'UseDNS no' >> /etc/ssh/sshd_config", silent=True)
            self.execute("/etc/init.d/ssh restart", silent=True)
            j.transaction.stop()

        j.transaction.stop()  # end of ssh connection

            # if j.application.shellconfig.interactive:
                # if copyqbase or j.console.askYesNo("Do you want to copy qbasedir to remote node over ssh?"):
                    # self._removeRedundantFiles()
                    # if rsync==False:
                        # sshclient.copyDirTree("/opt/qbase3/")
                        # sshclient.copyDirTree("/opt/code/")
                    # else:
                        #j.system.process.executeWithoutPipe("rsync -avzEp -e ssh /opt/qbase3/ root@%s:/opt/qbase3/ " %self.ipaddr)
                        #j.system.process.executeWithoutPipe("rsync -avzEp -e ssh /opt/qbase3/ root@%s:/opt/code/ " %self.ipaddr)
    def halt(self):
        j.transaction.start("Halt node %s %s" % (self.hostname, self.ipaddr))
        self.execute("halt")
        j.transaction.stop()

    def copyQbase(self, sandboxname="", deletesandbox=True):
        raise RuntimeError("Not implemented, check code and adjust for qbase6")
        sandboxdir = j.system.fs.joinPaths(j.dirs.baseDir, "..", "sandboxes")
        if not j.system.fs.exists(sandboxdir):
            raise RuntimeError("Cannot find sandbox in %s" % sandboxdir)
        if sandboxname == "":
            sandboxes = j.system.fs.listFilesInDir(sandboxdir)
            sandboxname = j.console.askChoice(sandboxes, "Select sandbox to copy", True)
        sandboxpath = j.system.fs.joinPaths(sandboxdir, sandboxname)
        j.transaction.start("Connect over ssh to %s" % self.ipaddr)
        j.transaction.start("Copy sandbox %s over sftp to remote /tmp dir" % sandboxpath)
        ftp = self.getSftpConnection()
        ftp.put(sandboxpath, "/tmp/qbase3.tgz")
        j.transaction.stop()  # sftp
        j.transaction.start("Expand remote sandbox /tmp/qbase3.tgz to /opt/qbase3")
        if deletesandbox:
            self.execute("rm -rf /opt/qbase3", timeout=10)
        self.execute("mkdir -p opt ; cd /opt ; tar xvfz /tmp/qbase3.tgz", timeout=60)  # tar xvfz /tmp/qbase3.tgz #@todo complete
        j.transaction.stop()  # expand
        j.transaction.stop()  # sshconnection
        j.console.echo("Qbase copied and expanded into %s" % self.ipaddr)

    def sendQbaseDebug(self):
        raise RuntimeError("Not implemented, check code and adjust for qbase6")
        sandboxdir = "/opt/qbase3debug_*"
        tarfile = "/tmp/qbase3debug.tgz"
        j.transaction.start("Copy tgz sandbox %s over sftp to remote /tmp dir %s" % (sandboxdir, self.ipaddr))
        ftp = self.getSftpConnection()
        ftp.put(tarfile, tarfile)
        j.transaction.stop()  # sftp
        j.transaction.start("Expand remote sandbox /tmp/qbase3debug.tgz to /opt/qbase3")
        self.execute("cd /opt ; tar xvfz /tmp/qbase3debug.tgz", timeout=10)
        j.transaction.stop()

    def sendExportedQbase(self, sandboxname):
        j.transaction.start("Copy tgz sandbox %s over sftp to remote /tmp dir %s" % (sandboxname, self.ipaddr))
        ftp = self.getSftpConnection()
        tarfile = j.system.fs.joinPaths(j.dirs.baseDir, "..", "sandboxes", "%s.tgz" % sandboxname)
        tarfiledest = "/tmp/qbase3debug.tgz"
        ftp.put(tarfile, tarfiledest)
        j.transaction.stop()  # sftp
        j.transaction.start("Expand remote sandbox /tmp/qbase3debug.tgz to /opt/qbase3")
        self.execute("cd /opt ; tar xvfz /tmp/qbase3debug.tgz", timeout=10)
        j.transaction.stop()

    def getSftpConnection(self):
        return self.sshclient.getSFtpConnection()

    def mkdir(self, destpath, silent=False):
        j.transaction.start("mkdir %s on %s" % (destpath, self.ipaddr), silent=silent)
        self.execute("mkdir -p %s" % destpath, silent=True, dieOnError=False, timeout=2)
        j.transaction.stop()

    def writeFile(self, destpath, fileContent, silent=False):
        j.transaction.start("writefile %s on %s" % (destpath, self.ipaddr), silent=silent)
        self.mkdir(j.system.fs.getDirName(destpath), silent=False)
        tmpfile = j.system.fs.joinPaths(j.dirs.tmpDir, str(random.randint(0, 10000)))
        j.system.fs.writeFile(tmpfile, fileContent)
        ftp = self.getSftpConnection()
        j.logger.log("ftpput: %s to %s" % (tmpfile, destpath))
        ftp.put(tmpfile, destpath)
        j.transaction.stop()
        return True

    def writeTemplate(self, destpath, templatepath, replace=[], silent=False):
        """
        @param destpath: path of node where writing to is starting from root
            if destpath=="" will be same as templatepath but in qbase in other words destpath=/opt/qbase3/$templatepath
        @param templatepath : /opt/qbase3/utils/defaults/$templatepath
        @param replace  [[find,replacewith],[find2,replace2]]
        """
        j.transaction.start("write file %s from template utils/defaults/%s" % (destpath, templatepath), silent=silent)
        if destpath == "":
            destpath = j.system.fs.joinPaths(j.dirs.baseDir, templatepath)
        j.logger.log("clusternode.writetemplate: templatepath=%s destpath=%s" % (templatepath, destpath)), 5
        templatepath = j.system.fs.joinPaths(j.dirs.baseDir, "utils", "defaults", templatepath)
        if not j.system.fs.exists(templatepath):
            raise RuntimeError("Cannot find template on %s" % templatepath)
        fileContent = j.system.fs.fileGetContents(templatepath)
        for replaceitem in replace:
            fileContent = fileContent.replace(replaceitem[0], replaceitem[1])
        self.writeFile(destpath, fileContent, silent=False)
        j.transaction.stop()

    def changeRootPassword(self, newPassword, silent=False):
        j.transaction.start("Change root passwd ", silent=False)
        self.writeTemplate("", "utils/sysadminscripts/changePassword.sh", [["$passwd$", newPassword]])
        try:
            self.execute(j.system.fs.joinPaths(j.dirs.baseDir, "utils", "sysadminscripts", "changePassword.sh"))
        except:
            self.install("expect")
            self.execute("expect " + j.system.fs.joinPaths(j.dirs.baseDir, "utils", "sysadminscripts", "changePassword.sh"))
        j.transaction.stop()

    def setHostname(self, newhostname, silent=False):
        j.transaction.start("Set hostname to %" % newhostname, silent=silent)
        self.execute("echo %s > /etc/hostname" % newhostname, silent=True)
        self.execute("hostname %s" % newhostname, silent=True)
        j.transaction.stop()

    def install(self, packagename, silent=False):
        if self.ubuntuPackagesUpdated == False:
            j.transaction.start("Upgrade ubuntu package metadata")
            self.execute("apt-get update", False)
            j.transaction.stop()
        j.transaction.start("Install ubuntu package %s" % packagename, silent=silent)
        if packagename not in self.ubuntuPackagesInstalled:
            self.execute("apt-get install %s -y" % packagename, True)
            self.ubuntuPackagesInstalled.append(packagename)
        j.transaction.stop()

    def createCifsShare(self, sharename="opt", sharepath="/opt", rootpasswd="rooter"):
        """
        only creates 1 cifs share, other shares will be lost
        """
        self.install("samba")
        self.writeTemplate("/etc/samba/smb.conf", j.system.fs.joinPaths(
            j.dirs.baseDir, "utils", "defaults", "etc", "smb.conf"), [["$sharename$", sharename], ["$sharepath$", sharepath]])
        self.execute("echo -ne \"%s\\n%s\\n\" | smbpasswd -a -s root" % (rootpasswd, rootpasswd))
        self.execute("/etc/init.d/samba restart")

    def createPublicNfsShare(self, sharepath="/opt"):
        """
        only creates 1 nfs share, no passwords for now!!!!
        """
        self.prepareForSSODebug()
        self.install("nfs-kernel-server")
        self.writeFile("/etc/exports", "/opt *(rw,sync,no_root_squash,no_subtree_check)")
        self.execute("echo '' > /etc/hosts.allow", dieOnError=True)
        self.execute("echo '' > /etc/hosts.deny", dieOnError=True)
        self.execute("exportfs -rav")

    def connectCodedir(self, ipaddr):
        """
        mount /opt/code to /opt/code of the specified node (ipaddr)
        """
        dirpath = "/opt/code"
        self.connectToNFSServer(dirpath, ipaddr)

    def connectJpackagedir(self, ipaddr, delete=False):
        """
        mount /opt/code to /opt/code of the specified node (ipaddr)
        """
        raise RuntimeError("Not implemented, check code and adjust for qbase6")
        dirpath = "/opt/qbase6/var/owpackages"
        self.connectToNFSServer(dirpath, ipaddr, delete)

    def installJPackage(self, name):
        """
        install owpackage name, domain, version onto cluster node
        """
        qshellscript = """
jp=i.jp.findByName("$name")
jp.install()
"""
        qshellscript.replace("$name", name)
        self.executeQshell([qshellscript])

    def connectToNFSServer(self, dirpath, ipaddr, delete=False):
        """
        e.g. if dirpath=/opt/code
        then: this code will mount /opt/code to /opt/code of the specified node (ipaddr)
        """
        j.transaction.start("mount %s to %s:%s" % (dirpath, ipaddr, dirpath))
        self.install("nfs-common")
        self.execute("umount %s" % dirpath, dieOnError=False)
        # if delete:
        outp = self.execute("mount | grep %s" % dirpath, dieOnError=False)
        if len(outp) > 5:
            raise RuntimeError("There is still a mount on the directory %s, could not umount")
        self.execute("rm -rf %s" % dirpath)
        self.execute("mkdir -p %s" % dirpath)
        self.execute("mount %s:%s/ %s" % (ipaddr, dirpath, dirpath))
        j.transaction.stop()

    def symlink(self, target, linkname):
        # @type linkname
#        if linkname.find('//') != -1:
#            print 'Raising exception////////////////////////////'
#            raise
        # replace double //
        target = target.replace('//', '/')
        linkname = linkname.replace('//', '/')
        if len(linkname) < 3:
            raise RuntimeError("Linkname should be more than 2 chars to be valid, is check to make sure we don't remove / of system")
        j.transaction.start("Creating symlink %s -> %s on %s" % (target, linkname, self.ipaddr))
        # It the file exists remove it
        # if self.execute("test -e '%s'" % (linkname), False)[0] == 0: # the file exists
            # if linkname == '/': # just to be sure we don't delete the harddrive!
                # raise
        self.execute("rm  -Rf '%s'" % (linkname), False)
        # if the directory does not exist create it
        dir = j.system.fs.getDirName(linkname)
        self.execute("mkdir -p '%s'" % (dir), True)

            # make the directory
            #self.execute("rm '%s'" % (linkname), True)
        # Make the link
        self.execute("ln -s %s %s" % (target, linkname), False)
        j.transaction.stop()

    def backupQbase(self):
        j.transaction.start("Backup opt/qbase6 on %s" % self.ipaddr)
        path = "/opt/backups/qbase6_%s.tgz" % j.base.time.getLocalTimeHRForFilesystem()
        self.execute("mkdir -p /opt/backups", False)
        self.execute("tar zcvfh %s /opt/qbase6" % path, False)
        self.execute("echo '%s' >  /opt/backups/path_to_last_backup.txt" % path, True)
        j.transaction.stop()

    def restoreQbase(self):
        j.transaction.start("Restoring opt/qbase6 on %s" % self.ipaddr)
        exitcode, path = self.execute("cat '/opt/backups/path_to_last_backup.txt'", True)
        self.execute("rm -Rf /opt/qbase6", False)
        # cd /; is redundant, don't know why it wont work without it?
        self.execute("cd /; tar vxzf %s -C /" % path, False)
        j.transaction.stop()

    def backupQbaseCode(self):
        """
        backup only the small files, excludes the 30 biggest files, iso's, .so's and stuff ..
        """
        j.transaction.start("Backup /opt/qbase6 jumpscale code on %s" % self.ipaddr)
        self.execute("mkdir -p /opt/backups", False)
        path = "/opt/backups/jumpscalecore_%s.tgz" % j.base.time.getLocalTimeHRForFilesystem()
        pathstobackup = '/opt/qbase3/lib/jumpscale/extensions /opt/code/jumpscale-core/code/utils /opt/code/jumpscale-core/code/packages/jumpscale/core'
        # compress them
        self.execute("tar zcvfh %s %s " % (path, pathstobackup), False)
        # remember last compressed
        self.execute("echo '%s' >  /opt/backups/path_to_last_jumpscalecode_backup.txt" % path, True)
        j.transaction.stop()

    def restoreQbaseCode(self):
        j.transaction.start("Restore partial /opt/qbase/ jumpscalecode on %s" % self.ipaddr)
        exitcode, path = self.execute("cat '/opt/backups/path_to_last_jumpscalecode_backup.txt'")
        # remove all files in the tar, cd is needed or wont work!
        self.execute("cd /; tar zft '%s' | grep -v ^d | awk {'print $6'} | xargs rm" % path, False)
        # extract all files in the tar
        self.execute("echo 'cd /; tar xzf '%s' -C /' > /tmp/out.tmp" % path, False)
        print self.execute("cd /; tar xzf '%s' -C /" % path, False)
        j.transaction.stop()

    def prepareForSSODebug(self):
        if self.isPreparedForSSODebug == False:
            j.transaction.start("Prepare for debug on %s" % self.ipaddr)
            self.execute("cp /etc/apt/sources.list.disabled /etc/apt/sources.list", False)
            self.execute("apt-get update", False)
            self.install("mc")
            j.transaction.stop()
            self.isPreparedForSSODebug = True

    def __str__(self):
        return "%s %s" % (self.hostname, self.ipaddr)

    __repr__ = __str__
