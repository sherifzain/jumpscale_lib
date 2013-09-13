from JumpScale import j

from Replicator import Replicator
from Cluster import Cluster

import string
from Replicator import *
from ClusterConfigs import *


class ClusterFactory():

    def __init__(self):
        # self._lastSuperadminPassword=""
        self.clusters = {}
        self.replicator = Replicator()
        j.cluster = self
        config = j.config.getInifile("clusterconfig")
        self.config = ClusterConfigs()
        self.replication = Replicator()
        if len(config.getSections()) == 0:
            return
        for clustername in config.getSections():
            ipaddresses = str(config.getValue(clustername, "ip")).strip()
            domainname = str(config.getValue(clustername, "domain")).strip()
            superadminpassword = config.getValue(clustername, "rootpasswd").strip()
            cl = Cluster(clustername=clustername, domainname=domainname, ipaddresses=ipaddresses.split(","), superadminpassword=superadminpassword)
            self.clusters[clustername] = cl

    def get(self, clustername="", domainname=""):
        """
        return cluster for specified domain or shortname, 
        there needs to be a cluster defined already before otherwise no nodes will be found
        config file which stores this info is at $qbasedir/cfg/jsconfig/clusterconfig.cfg
        only one of th 2 params is required
        """
        if clustername == "" and domainname == "":
            clustername = j.console.askChoice(self.list(), "select cluster")
        if clustername in self.clusters:
            return self.clusters[clustername]
        for clustername in self.clusters.keys():
            cl = self.clusters[clustername]
            if cl.domainname == domainname:
                return cl
        raise RuntimeError("Could not find cluster with domainname %s" % domainname)

    def create(self, clustername="", domainname="", ipaddresses=[], superadminpassword="", superadminpasswords=[]):
        # TODO
        # j.console.echo("*** Ignore master for now, it's not yet implemented yet, just pick any node of the cluster.. ***")
        # j.console.echo("*** After specifying the information for a cluster, the information gets written to disk but is not used by the program, instead it tries to guess the information by probing the network (mostly wrong), in case of problems just restart the shell, your cluster will be there. .. ***")
        """
        domainname needs to be unique
        clustername is only a name which makes it easy for you to remember and used to store in config file
        """
        if superadminpasswords == []:
            superadminpasswords = [superadminpassword]
        if clustername != "":
            # fill in cluster configuration file with information already known
            ipaddresses2 = string.join([str(ipaddr).strip() for ipaddr in ipaddresses], ",")

            if clustername not in j.remote.cluster.config.list():
                i.cluster.config.add(clustername, {'domain': domainname, 'ip': ipaddresses2, 'rootpasswd': superadminpassword})
            else:
                i.cluster.config.configure(clustername, {'domain': domainname, 'ip': ipaddresses2, 'rootpasswd': superadminpassword})
        if j.application.shellconfig.interactive:
            if domainname == "" or ipaddresses == [] or superadminpassword == "":
                if clustername == "":
                    #import pdb
                    # pdb.set_trace()
                    # How do I get the IP adresses?
                    # Get the ip adresses and put them in ipaddresses
                    # so the constructor of Cluster does not use avahi, because its results or wrong!
                    clustername = j.gui.dialog.askString('Name for the cluster', 'myCluster')
                    i.cluster.config.add(itemname=clustername)
                else:
                    i.cluster.config.review(clustername)
                self.__init__()
                return self.clusters[clustername]

        else:
            if ipaddresses == []:
                raise RuntimeError("Please specify ipaddresses of nodes you would like to add to cluster")
            if superadminpasswords == []:
                raise RuntimeError("Please specify password(s) of nodes you would like to add to cluster")
            if domainname == "":
                raise RuntimeError("Please specify domainname for cluster")
            if clustername == "":
                raise RuntimeError("Please specify short name for cluster")

        # at this point we know ipaddresses & possible superadminpasswords
        cl = Cluster(clustername=clustername, domainname=domainname, ipaddresses=ipaddresses,
                     superadminpasswords=superadminpasswords, superadminpassword=superadminpassword)
        self.clusters[clustername] = cl
        return cl

    def delete(self, clustername=""):
        """
        Delete a cluster with clustername from the configuration
        """
        if clustername == "":
            if j.application.shellconfig.interactive:
                ask = True
                if len(self.clusters.keys()) == 1:
                    ask = j.gui.dialog.askYesNo('Are you sure you want to delete cluster %s' % q.cluster.get())
                if ask:
                    clustername = j.gui.dialog.askChoice('Select cluster to remove', self.clusters.keys())
                else:
                    return
            else:
                raise ValueError("In non-interactive mode please specify clustername to be removed")
        if clustername in self.clusters.keys():
            q.cluster.config.remove(clustername)
        else:
            raise ValueError("Cluster %s not found" % clustername)
        self.__init__()

    def listAvahiEnabledMachines(self):
        j.transaction.start("Investigate network, try to find potential nodes (using avahi).")
        services = j.cmdtools.avahi.getServices()
        result = []
        ipaddresses = []
        for service in services.services:
            if service.address not in ipaddresses:
                result.append(service)
                ipaddresses.append(service.address)
        j.transaction.stop()
        return result

    def list(self):
        """
        return list of clusternames
        """
        return self.clusters.keys()

    # def _removeRedundantFiles(self):
        # path="/opt/qbase3"
        ##j.logger.log("removeredundantfiles %s" % (path))
        # files=j.system.fs.listFilesInDir(path,True,filter="*.pyc")
        # files.extend(j.system.fs.listFilesInDir(path,True,filter="*.pyo")) #@todo remove other files
        # for item in files:
            # j.system.fs.removeFile(item)
        # j.system.fs.removeDirTree(j.system.fs.joinPaths(j.dirs.logDir))
        # j.system.fs.removeDirTree(j.system.fs.joinPaths(j.dirs.tmpDir))
        # j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.tmpDir))
        # j.system.fs.createDir(j.system.fs.joinPaths(j.dirs.logDir))
        # j.system.fs.removeDirTree(j.system.fs.joinPaths(j.dirs.varDir,"owpackages"))
