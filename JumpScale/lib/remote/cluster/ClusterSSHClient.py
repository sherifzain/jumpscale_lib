from JumpScale import j
try:
    import warnings
    warnings.filterwarnings('ignore', r'.*sha.*')
    import paramiko
except:
    pass


class ClusterSSHClient():

    def __init__(self, cluster, node):
        self.isconnected = False
        self.node = node
        self.cluster = cluster
        self.passwd = ""
        self._sshclient = None
        self.sftp = None

    def sshtest(self):
        return self.connect(force=True, testonly=True)

    def connect(self, force=False, testonly=False):
        """
        return True when connected, raise error when not possible
        """
        if self.isconnected == True and force == False:
            return True
        if not j.system.net.pingMachine(self.node.ipaddr, 5):
            raise RuntimeError("Could not connect to machine %s to create an SSH connection, please check if the machine is reachable. Could not ping it.")
        j.logger.log("connect %s" % self.node.ipaddr)
        state = "start"
        passwdworking = None
        if self.passwd != "":
            # means node has been checked before and has good passwd
            passwords2try = [self.passwd]
        else:
            passwords2try = [self.cluster.superadminpassword]
            passwords2try.extend(self.cluster._superadminpasswords)
        for passwd in passwords2try:
            if state == "start" or state == "autherror":
                try:
                    # We need to package jshell remote for this
                    #j.logger.log("clustersshclient: try to login with passwd %s on %s" %(passwd,self.node.ipaddr),2)
                    self._sshclient = j.remote.system.connect(self.node.ipaddr, "root", passwd, timeout=10)
                    state = "done"
                    j.logger.log("cluster node %s connected over ssh" % self.node.ipaddr, 5)
                    passwdworking = passwd

                except j.remote.system.exceptions.RemoteSystemAuthenticationError:  # :AuthenticationException,e:
                    state = "autherror"
                    j.logger.log("Could not sshlogin into %s with login %s, passwd %s" % (self.node.ipaddr, "root", passwd))
                # except Exception, e:
                    # if str(e.message).lower().find("authentication failed")>-1:
                        # could not login
                        # state="autherror"
                        #j.logger.log("Could not sshlogin into %s with login %s, passwd %s" % (self.node.ipaddr,"root",passwd))
                except Exception as e:
                    if testonly:
                        return False
                    raise RuntimeError("%s\nCannot connect over SSH to %s" % (e, self.node.ipaddr))

        self.isconnected = True
        return True

    def execute(self, command, dieOnError=True, timeout=None, tostdout=True):
        self.connect()
        #returncode,stdout,stderr=self._sshclient.process.executeUnix(command, dieOnError, timeout)
        # Todo is this correct?
        stderr = ""
        if not self._sshclient:
            raise RuntimeError('Can\'t execute process, there is no connection initialized.\n' +
                               'Make sure nodes are up and running and cluster passwords are correct.')
        returncode, stdout, stderr = self._sshclient.process.execute(command, dieOnNonZeroExitCode=dieOnError, timeout=timeout, outputToStdout=tostdout)
        return returncode, stdout, stderr

    def getSFtpConnection(self):
        j.logger.log("Open SFTP connection to %s" % (self.node.ipaddr))
        #t = paramiko.Transport((self.host, self.port))
        #t.connect(username=self.username , password=self.password)

        # Keep the connection open or we get the follwing exception
        # paramico wait_for_event() SSHException: Channel closed.
        # when making to many connections, closing the generated connections did not work
        if self.sftp == None:
            if self._sshclient == None:
                self.sshtest()
            if self._sshclient == None:
                raise RuntimeError("Could not establish ssh connection")
            transport = self._sshclient.process._connection.get_transport()
            self.sftp = paramiko.SFTPClient.from_transport(transport)
        return self.sftp
