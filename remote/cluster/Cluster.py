from OpenWizzy import o
from ClusterNode import ClusterNode
from OpenWizzy.core.baseclasses import BaseType
import os
import threading
import copy

class Executor(object):

    def __init__(self,nodes=[]):
        self.nodes = nodes
        self.result={}

        # Lock object to keep track the threads in loops, where it can potentially be race conditions.
        self.lock = threading.Lock()
        self.debug=False

    
    def pop_queue(self):
        ip = None
        self.lock.acquire() # Grab or wait+grab the lock.

        node = self.nodes.pop()

        self.lock.release() # Release the lock, so another thread could grab it.

        return node

    def dequeue(self,**args):
        node = self.pop_queue()

        if not node:
            return None

        method=args.pop("method")
        exec("method2=node.%s"%method)
        print "execute method:%s"% method
        print "args:%s"%args

        try:
            self.result[node.hostname]=method2(**args)
        except Exception,e:
            print "ERROR:%s"%e
            from OpenWizzy.core.Shell import ipshellDebug,ipshell
            print "DEBUG NOW in cluster executor in thread"
            ipshell()        
        
        #print "result:%s"%self.result[node.hostname]
            
    def execute(self,method,**args):
        threads = []
        l=len(self.nodes)
        for i in range(l):
            args["method"]=method
            if self.debug:
                self.dequeue(**args)
            else:
                t = threading.Thread(target=self.dequeue,kwargs=args)            
                t.start()
                threads.append(t)

        # Wait until all the threads are done. .join() is blocking.
        if not self.debug:
            [ t.join() for t in threads ]        

        return self.result

class Cluster(BaseType):
    domainname=o.basetype.string(doc="domain name of cluster")
    superadminpassword=o.basetype.string(doc="superadmin password of cluster")
    _superadminpasswords=o.basetype.list()
    nodes=o.basetype.list()

    def __init__(self,clustername,domainname,ipaddresses,superadminpassword,superadminpasswords=[]):
        self.domainname=domainname
        self.superadminpassword=superadminpassword
        self._superadminpasswords=superadminpasswords
        self.nodes=[]

        self.localip=""

        #import pdb
        #pdb.set_trace()

        if ipaddresses==[]:
            services=o.cmdtools.avahi.getServices()
            sshservices=services.find(port=22,partofdescription=domainname.replace(".","__"))
            for sshservice in sshservices:
                node=ClusterNode(self)
                node.hostname=sshservice.hostname
                node.ipaddr=sshservice.address
                self.nodes.append(node)
        else:
            for ipaddr in ipaddresses:
                node=ClusterNode(self)
                node.hostname=ipaddr
                node.ipaddr=ipaddr
                self.nodes.append(node)

        self.threading=True

    #def getSuperadminPassword(self):
        #if len(self.superadminpasswords)>1:
            #raise RuntimeError("There can only be one superadmin password specified, use cluster.setSuperadminPassword(), which will make sure password has been set on all nodes")
        #if len(self.superadminpasswords)<1:
            #raise RuntimeError("No superadmin password specified")
        #return self.superadminpasswords[0]


    def listnodes(self):
        return [ node.hostname for node in self.nodes]

    def copyQbase(self,sandboxname="",hostnames=[],deletesandbox=None):
        """
        sandboxes are $sandboxname.tgz in /opt/sandboxes
        @param sandboxname is name of a sandbox in that directory
        """
        nodes=self.selectNodes("Select which nodes",hostnames)
        o.transaction.start("Copy qbase onto cluster.")
        sandboxdir=o.system.fs.joinPaths(o.dirs.baseDir,"..","sandboxes")
        sandboxes=o.system.fs.listFilesInDir(sandboxdir)
        if sandboxname=="":
            sandboxname=o.console.askChoice(sandboxes,"Select sandbox to copy",True)
        if deletesandbox==None:
            deletesandbox=o.console.askYesNo("    Do you want to remove remote qbase6 directory (if it exists?)")
        for node in nodes:
            node.copyQbase(sandboxname=sandboxname,deletesandbox=deletesandbox)
        o.transaction.stop()


    def sendExportedQbase(self,sandboxname=None,hostnames=[]):
        nodes=self.selectNodes("Select which nodes",hostnames)
        o.transaction.start("Copy exported qbase6 onto cluster.")
        sandboxdir=o.system.fs.joinPaths(o.dirs.baseDir,"..","sandboxes")
        choices=[o.system.fs.getBaseName(item).replace(".tgz","") for item in o.system.fs.listFilesInDir(sandboxdir)]
        o.console.echo("Select sandbox to sent to cluster")
        sandboxname=o.console.askChoice(choices)
        for node in nodes:
            node.sendExportedQbase(sandboxname)
        o.transaction.stop()


    def do(self,method,hostnames=[],all=False,dieOnError=True,**args):
        """
        execute a method on the nodes as specified
        """
        if not o.application.shellconfig.interactive:
            all=True
        if all:
            nodes=copy.copy(self.nodes)
        else:
            nodes=copy.copy(self.selectNodes("Select which nodes",hostnames))
        
        e=Executor(nodes)        
        result=e.execute(method,**args)
        for key in result.keys():
            exitcode, output, error=result[key]
            if exitcode<>0 and dieOnError:
                raise RuntimeError("Cannot execute method%s on node:%s. Error:\n%s\n\n"%(method,key,error))
        return result

    def sshtest(self):
        # o.transaction.start("SSH STATUS TEST:")
        return self.do("sshtest")

    def connect(self):
        return self.do("connect")
        # o.transaction.start("cluster connect")
        # for node in self.nodes:
        #     result=node.connect()
        # o.transaction.stop()

    def ping(self):
        return self.do("ping")
        # o.transaction.start("PING STATUS TEST:")
        # results={}
        # for node in self.nodes:
        #     result=node.ping()
        #     if o.application.shellconfig.interactive:
        #         o.console.echo("ping %s %s %s" % (node.hostname,node.ipaddr,result))
        #     results[node.hostname]=result
        # o.transaction.stop()
        # return results


    def getConsoles(self,all=False):
        if not o.application.shellconfig.interactive:
            all=True
        if all:
            nodes=copy.copy(self.nodes)
        else:
            nodes=copy.copy(self.selectNodes("Select which nodes",hostnames))

        for node in nodes:
            if node.cluster.superadminpassword=="":
                node.cluster.superadminpassword= o.console.askString("superasdminpasswd:")
            if o.system.platformtype.isWindows():
                cmd=o.system.fs.joinPaths(o.dirs.baseDir,"appsbin","putty","putty.exe")
                if o.system.fs.exists(cmd):
                    cmd="%s -ssh root@%s -pw %s"%(cmd,node.ipaddr,node.cluster.superadminpassword)
                    o.system.process.executeAsync(cmd)
                    
                else:
                    raise RuntimeError("Cannot find putty in sandbox, looking on %s"%cmd)
            else:
                raise RuntimeError("getConsoles not implemented for linux yet, please use byobu to do so, there is an ext")


    def execute(self,command,hostnames=[],dieOnError=True,all=True,recoveryaction=""):
        """
        execute a command on every node of the cluster, only output the result
        """
        if command.strip()=="":
            return {}
        result=self.do("execute",all=all,commands=command,hostnames=hostnames,dieOnError=False)
        if result=={}:
            raise RuntimeError("Could not execute %s on cluster %s"%(command,hostnames))

        for key in result.keys():
            exitcode, output, error=result[key]
            if exitcode<>0:
                if recoveryaction<>"":
                    self.execute(recoveryaction,hostnames=[key])
                    result.update(self.execute(command,hostnames=[key]))
                    exitcode, output, error=result[key]
                    if exitcode==0:
                        continue
                if dieOnError:
                    raise RuntimeError("Cannot execute command%s on node:%s. Error:\n%s\n\n"%(command,key,error))
        return result

    def writeFile(self,destpath,fileContent,hostnames=[],silent=False):
        """
        send file to node
        """
        o.transaction.start("Write file to cluster")
        nodes=self.selectNodes("Select which nodes",hostnames)
        results={}
        for node in nodes:
            node.writeFile(destpath,fileContent,silent)
        o.transaction.stop()

    def ubuntuPackageUpdateUpgrade(self):
        result=self.execute("apt-get update",recoveryaction='dpkg --configure -a --force-all')
        result=self.execute("apt-get upgrade -y -f --force-yes")

    # def qbaseInstallReset(self,devel=False):
    #     """
    #     will install & reset qbase
    #     """
    #     self.ubuntuPackageUpdateUpgrade()
    #     result=self.execute("rm -rf /opt/qbase6")
    #     result=self.execute("apt-get install nginx curl mc ssh mercurial byobu python-gevent python-simplejson python-numpy redis-server python-pycryptopp -y")
    #     result=self.execute("apt-get install msgpack-python python-pip python-dev python-zmq -y")
    #     result=self.execute("pip install ujson") #will do compile, should make precompiled version 
    #     result=self.execute("pip install blosc")
    #     self.execute("cd /tmp;curl https://bitbucket.org/incubaid/openwizzy-core-6.0/raw/default/installers/installerbase.py > installerbase.py")
    #     # result=self.execute("ls /tmp/installerbase.py")
    #     if devel:
    #         result=self.execute("cd /tmp;curl https://bitbucket.org/incubaid/openwizzy-core-6.0/raw/default/installers/installDevelSilent.py | python")
    #     else:
    #         result=self.execute("cd /tmp;curl https://bitbucket.org/incubaid/openwizzy-core-6.0/raw/default/installers/installSilent.py | python")

    #     # def ccopy(ffrom,tto):
    #     #     self.execute("rm -rf %s;cp -rf %s %s"%(ffrom,ffrom,tto))    

    #     # ccopy ("/opt/code/incubaid/openwizzy-core-6.0/apps/worker/","/opt/qbase6/apps/worker/") 


    def syncQbase(self,hostnames=[]):
        o.transaction.start("Sync Qbase")
        nodes=self.selectNodes("Select which nodes you want to sync qbase to",hostnames)
        for node in nodes:
            node.syncQbase()
        o.transaction.stop()


    def executeQshell(self,command,hostnames=[],dieOnError=True):
        """
        execute a command on every node of the cluster, only output the result
        """
        o.transaction.start("Execute qshell cmd %s on cluster."%command)
        nodes=self.selectNodes("Select which nodes",hostnames)
        results={}
        for node in nodes:
            returncode,stdout=node.executeQshell(command,dieOnError)
            ##stdout=o.console.formatMessage(stdout,prefix="stdout")
            results[node.hostname]=[returncode,stdout]
            if o.application.shellconfig.interactive:
                o.console.echo(stdout)
        o.transaction.stop()
        return results

    def syncRootPasswords(self, newPasswd):
        '''
        Reset all root passwords of nodes in this cluster to the specified value.
        Remark: requires that cluster is created with correct root passwords provided.

        @param newPasswd The root password to set on the nodes
        @type newPasswd String
        '''
        for node in self.nodes:
            node.changeRootPassword(newPasswd)

    def get(self,name):
        for node in self.nodes:
            if node.hostname==name:
                return node
        raise RuntimeError("Could not find node %s in cluster." % name)

    def __str__(self):
        msg="domain:%s\n"% self.domainname
        for node in self.nodes:
            msg+=" * %s\n" % str(node)
        return msg

    __repr__=__str__

    def selectNodes(self,message="",hostnames=[]):
        """
        only for interactive usage
        """
        if hostnames<>[]:
            return [self.get(name) for name in hostnames]
        choices=hostnames
        if choices==[] and o.application.shellconfig.interactive==False:
            raise RuntimeError("cluster.selectNodes() can only be used in interactive mode")
        if choices==[]:
            choices=[str(node.hostname) for node in self.nodes]
            choices.append("ALL")
            choices=o.console.askChoiceMultiple(choices,message or "select nodes",True)
            if "ALL"==choices[0]:
                choices=[str(node.hostname) for node in self.nodes]
        result=[self.get(name) for name in choices]
        return result

    def halt(self,hostnames=[]):
        o.transaction.start("Stop nodes over ssh")
        nodes=self.selectNodes("Select which nodes you want to halt",hostnames)
        for node in nodes:
            node.halt()
        o.transaction.stop()

    def sendfile(self,source,dest="",hostnames=[]):
        if dest=="":
            dest=source
        o.transaction.start("Send file %s to dest %s on nodes over ssh" % (source,dest))
        nodes=self.selectNodes("Select which nodes you want to halt",hostnames)
        for node in nodes:
            node.sendfile(source,dest)
        o.transaction.stop()

    def activateAvahi(self,hostnames=[]):
        o.transaction.start("Activate avahi on nodes for cluster")
        nodes=self.selectNodes("Select which nodes you want to activate",hostnames)
        for node in nodes:
            node.activateAvahi()
        o.transaction.stop()

    # def prepare(self,hostnames=[]):
    #     o.transaction.start("Prepare nodes for cluster")
    #     nodes=self.selectNodes("Select which nodes you want to prepare",hostnames)
    #     for node in nodes:
    #         node.prepare()
    #     o.transaction.stop()

    def createCifsShare(self,sharename="opt",sharepath="/opt",rootpasswd="rooter",hostnames=[]):
        """
        per node only creates 1 cifs share, other shares will be lost
        carefull will overwrite previous shares
        """
        o.transaction.start("Create cifs share on selected cluster nodes")
        nodes=self.selectNodes("Select which nodes you want to create a cifs share upon",hostnames)
        for node in nodes:
            node.createCifsShare(sharename,sharepath,rootpasswd)
        o.transaction.stop()

    def createPublicNfsShare(self,sharepath="/opt",hostnames=[]):
        """
        per node only creates 1 nfs share, no passwords for now!!!!
        carefull will overwrite previous shares
        """
        o.transaction.start("Create nfs share on selected cluster nodes")
        nodes=self.selectNodes("Select which nodes you want to create a nfs share upon",hostnames)
        for node in nodes:
            node.createPublicNfsShare(sharepath)
        o.transaction.stop()

    def connectMeToNfsShares(self,sharepath="/opt",hostnames=[]):
        """
        make connections between me and the nodes in the cluster
        will be mounted on, /mnt/$hostname/$sharepath e.g. /mnt/node1/opt
        """
        o.transaction.start("Create nfs connection to selected cluster nodes, will be mounted on, /mnt/$hostname/$sharepath e.g. /mnt/node1/opt ")
        nodes=self.selectNodes("Select which nodes you want to create a nfs share upon",hostnames)
        if not o.system.fs.exists("/usr/sbin/nfsstat"):
            o.transaction.start("install nfs client")
            o.system.process.execute("apt-get update",dieOnNonZeroExitCode=False)
            o.system.process.execute("apt-get install nfs-common -y",dieOnNonZeroExitCode=False)
            o.transaction.stop()
        for node in nodes:
            o.transaction.start("mount to %s" % node.hostname)
            mntpath=o.system.fs.joinPaths("/mnt",node.hostname,sharepath.replace("/",""))
            o.system.process.execute("umount %s" % mntpath,dieOnNonZeroExitCode=False)
            o.system.fs.createDir(mntpath)
            o.system.process.execute("mount %s:%s/ %s" % (node.ipaddr,sharepath,mntpath),dieOnNonZeroExitCode=False)#@todo make code better, should check if mount is the right mount
            o.transaction.stop()
        o.transaction.stop()

    def shareMyNodeToCluster(self):
        """
        over NFS & CIFS
        CAREFULL: will overwrite existing config
        will export /opt
        for cifs passwd is root/rooter
        """
        o.system.process.execute("apt-get update",dieOnNonZeroExitCode=False)
        o.system.process.execute("apt-get install samba nfs-kernel-server -y",dieOnNonZeroExitCode=False)
        replace=[["$sharename$","opt"],["$sharepath$","/opt"]]
        fileContent=o.system.fs.fileGetContents(o.system.fs.joinPaths(o.dirs.baseDir,"utils","defaults","etc","smb.conf"))
        for replaceitem in replace:
            fileContent=fileContent.replace(replaceitem[0],replaceitem[1])
        o.system.fs.writeFile("/etc/samba/smb.conf",fileContent)
        o.system.fs.writeFile("/etc/exports","/opt *(rw,sync,no_root_squash,no_subtree_check)")
        #if o.console.askYesNo('Allow me to overwrite /etc/hosts.allow and /etc/hosts.deny?'):
        o.system.fs.writeFile('/etc/hosts.allow', '')
        o.system.fs.writeFile('/etc/hosts.deny', '')
        #else:
        #    o.console.echo('Please ensure you /etc/hosts.allow and /etc/hosts.deny are configured to allow sharing of you /opt folder!')
        o.system.process.execute("exportfs -rav")

        # o.system.process.execute("echo -ne \"%s\\n%s\\n\" | smbpasswd -a -s root" %("rooter","rooter"))
        # -> does not work, reported bug in jira, this is a workaround
        o.system.fs.writeFile('/tmp/smbpasswdset', 'rooter\nrooter\n')           # workaround
        o.system.process.execute('cat /tmp/smbpasswdset | smbpasswd -a -s root') # workaround

        o.system.process.execute("/etc/init.d/samba restart")

    def getMyClusterIp(self):
        if self.localip<>"":
            return self.localip
        interfaces=["eth0","eth1","br0","br1","br2","wlan0","wlan1"]
        ipaddresses=[]
        localip=""
        for interface in interfaces:
            ipaddr=o.system.net.getIpAddress(interface)
            if ipaddr<>[]:
                ipaddr=ipaddr[0][0]
                ipaddresses.append(ipaddr)
        knownips=[node.ipaddr for node in self.nodes]
        for ip in knownips:
            if ip in ipaddresses:
                localip=ip
                break
        if localip=="":
            localip=o.console.askString("Give ipaddress of localmachine")
        self.localip=localip
        return localip

    def connectClusterToMyCode(self,hostnames=[]):
        """
        will connect mount /opt/code on each node to my /opt/code over nfs
        """
        o.transaction.start("Connect cluster to my /opt/code")
        nodes=self.selectNodes("Select which nodes ",hostnames)
        localip=self.getMyClusterIp()
        for node in nodes:
            node.connectCodedir(localip)
        o.transaction.stop()

    def connectClusterToMyQpackages(self,hostnames=[]):
        """
        connect the nodes of the cluster to my /opt/qbase6/var/owpackages directory
        also push my owpackages configuration to the other clusternodes
        allows the cluster to install from my local owpackages (not from the central repo)
        """
        o.transaction.start("Connect cluster to my owpackages 4 directory")
        nodes=self.selectNodes("Select which nodes ",hostnames)
        localip=self.getMyClusterIp()
        for node in nodes:
            node.connectQpackagedir(localip)
        o.transaction.stop()

    def installQPackage(self, name, domain, version, reconfigure, hostnames=[]):
        """
        install a owpackage on the specified nodes in the cluster
        """
        o.transaction.start("Install package on cluster")
        nodes = self.selectNodes("Select which on which nodes you want to install this owpackage", hostnames)
        for node in nodes:
            node.installQPackage(name, domain, version, reconfigure)
        o.transaction.stop()

    def symlink(self,target,linkname, hostnames=[]):
        """
        symlink a source to a dest using a symlink

        """
#        print "ln -s %s %s" % (target,linkname)
#        self.execute("ln -s %s %s" % (target,linkname))
        nodes=self.selectNodes("Select which nodes ",hostnames)
        for node in nodes:
            node.symlink(target, linkname)

    def backupQbase(self,hostnames=[]):
        nodes=self.selectNodes("Select which nodes ",hostnames)
        for node in nodes:
            node.backupQbase()

    def restoreQbase(self,hostnames=[]):
        nodes=self.selectNodes("Select which nodes ",hostnames)
        for node in nodes:
            node.restoreQbase()

    def backupQbaseCode(self,hostnames=[]):
        nodes=self.selectNodes("Select which nodes ",hostnames)
        for node in nodes:
            node.backupQbaseCode()

    def restoreQbaseCode(self,hostnames=[]):
        nodes=self.selectNodes("Select which nodes ",hostnames)
        for node in nodes:
            node.restoreQbaseCode()

    def mkdir(self,path,hostnames=[]):
        nodes=self.selectNodes("Select which nodes you want to create a dir on",hostnames)
        for node in nodes:
            node.mkdir(path)



    #def activateSSODebugMode(self):
        #"""
        #will checkout openwizzy and many required repo's for SSO
        #will share the local sandbox over nfs
        #will create links between repo's and local sandbox
        #will link log directories from cluster node to local log dir
        #"""

