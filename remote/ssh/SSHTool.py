

class SSHTool:

    def createClient(self,  host, username, password, timeout):
        '''Create a new SSHClient instance.

        @param host: Hostname to connect to
        @type host: string
        @param username: Username to connect as
        @type username: string
        @param password: Password to authenticate with
        @type password: string
        @param timeout: Connection timeout
        @type timeout: number

        @return: SSHClient instance
        @rtype: SSHClient
        '''

        try:
            from remote.ssh.SSHClient import SSHClient
        except:
            from JumpScale import j
            j.system.platformtype.ubuntu.install("python-paramiko")
        from remote.ssh.SSHClient import SSHClient
        return SSHClient(host, username, password, timeout)
