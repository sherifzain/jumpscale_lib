import warnings
warnings.filterwarnings('ignore', r'.*sha.*')
import paramiko
from JumpScale import j


class SSHClient:

    client = None  # object of type client

    def __init__(self, host, username, password, timeout):
        self.host = host
        self.port = 22
        self.username = username
        self.password = password
        self.timeout = timeout
        self.client = None
        self._connect()

    def _connect(self):
        """Connect to an SSH server and authenticate to it."""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, self.port, self.username, self.password, timeout=self.timeout)

    def executewait(self, command, dieOnError=True):
        """
        only works for unix
        Execute a command on the SSH server.  Wait till output done.
        @raise SSHException: if the server fails to execute the command
        """
        command = command + " ; if [ $? -ne 0 ] ; then echo ***ERROR*** 1>&2 ; fi ; echo \"***DONE***\""
        j.logger.log("Execute ssh command %s on %s" % (command, self.host))
        stdin, channelFileStdOut, channelFileStdErr = self.client.exec_command(command)
        myOut = ""
        myErr = ""
        while (not channelFileStdOut.channel.eof_received) or (not channelFileStdErr.channel.eof_received):
            if channelFileStdOut.channel.recv_ready():
                tmp = (channelFileStdOut.channel.recv(1024))
                j.logger.log("ssh %s out:%s" % (self.host, tmp), 6)
                myOut += tmp
            if channelFileStdErr.channel.recv_stderr_ready():
                tmp = (channelFileStdErr.channel.recv_stderr(1024))
                j.logger.log("ssh %s err:%s" % (self.host, tmp), 6)
                myErr += tmp
        tmp = channelFileStdOut.read()
        j.logger.log("ssh %s out:%s" % (self.host, tmp), 6)
        myOut += tmp
        tmp = channelFileStdErr.read()
        j.logger.log("ssh %s err:%s" % (self.host, tmp), 6)
        myErr += tmp
        if len(myErr.strip()) > 0 and dieOnError:
            raise RuntimeError("Could not execute %s on %s, output was \n%s\n%s\n" % (command, self.host, myOut, myErr))
        if myOut.find("***DONE***") == -1:
            raise RuntimeError("Did not get all output from executing the SSH command %s" % command)

        return myOut, myErr

    def getSFtpConnection(self):
        j.logger.log("Open SFTP connection to %s" % (self.host))
        #t = paramiko.Transport((self.host, self.port))
        #t.connect(username=self.username , password=self.password)
        sftp = paramiko.SFTPClient.from_transport(self.client.get_transport())
        return sftp

    def _removeRedundantFiles(self, path):
        j.logger.log("removeredundantfiles %s" % (path))
        files = j.system.fs.listFilesInDir(path, True, filter="*.pyc")
        files.extend(j.system.fs.listFilesInDir(path, True, filter="*.pyo"))  # @todo remove other files  (id:6)
        for item in files:
            j.system.fs.remove(item)

    def copyDirTree(self, source, destination="", removeNonRelevantFiles=False):
        """
        Recursively copy an entire directory tree rooted at source.
        The destination directory may already exist; if not, it will be created
    
        Parameters:        
        - source: string (source of directory tree to be copied)
        - destination: string (path directory to be copied to...should not already exist)
          if destination no specified will use same location as source
        """
        if destination == "":
            destination = source
        dirs = {}
        self.executewait("mkdir -p %s" % destination)
        ftp = self.getSFtpConnection()
        if removeNonRelevantFiles:
            self._removeRedundantFiles(source)
        files = j.system.fs.listFilesInDir(source, recursive=True)
        j.logger.log("Coppy %s files from %s to %s" % (len(files), source, destination), 2)
        for filepath in files:
            dest = j.system.fs.joinPaths(destination, j.system.fs.pathRemoveDirPart(filepath, source))
            destdir = j.system.fs.getDirName(dest)
            if destdir not in dirs:
                j.logger.log("Create dir %s" % (destdir))
                # ftp.mkdir(destdir)
                self.executewait("mkdir -p %s" % destdir)
                dirs[destdir] = 1
            j.logger.log("put %s to %s" % (filepath, dest))
            ftp.put(filepath, dest)

    def execute(self, command):
        """
        Execute a command on the SSH server.  A new L{Channel} is opened and
        the requested command is executed.  The command's input and output
        streams are returned as python C{file}-like objects representing
        stdin, stdout, and stderr.

        @param command: the command to execute
        @type command: str
        @return: the stdin, stdout, and stderr of the executing command
        @rtype: tuple(L{ChannelFile}, L{ChannelFile}, L{ChannelFile})

        @raise SSHException: if the server fails to execute the command
        """
        return self.client.exec_command(command)

    def logSSHToFile(self, logFile):
        "send ssh logs to a logfile, if they're not already going somewhere"
        paramiko.util.log_to_file(logFile)

    def getOutPut(self, channelFileStdOut, channelFileStdErr):
        myOut = ""
        myErr = ""
        while not channelFileStdOut.channel.eof_received and not channelFileStdErr.channel.eof_received:
            if channelFileStdOut.channel.recv_ready():
                myOut += (channelFileStdOut.channel.recv(1024))
            if channelFileStdErr.channel.recv_stderr_ready():
                myErr += (channelFileStdErr.channel.recv_stderr(1024))
        return myOut, myErr

    def __del__(self):
        """
        Close this SSHClient.
        """
        self.client.close()
