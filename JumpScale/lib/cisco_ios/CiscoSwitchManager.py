from JumpScale import j
# import JumpScale.baselib.remote

class CiscoSwitchManager(object):

    def get(self, host, login,password):
        return CiscoSwitch(host, login,password)
#!/usr/bin/python

from Router import Router

class CiscoSwitch(object):

    def __init__(self, host, login,password):

        hostname = 'R1'
        R1 = Router(hostname, logfile='')
        login_cmd = 'telnet ' + host
        login_expect = '{0}#|{0}>'.format(hostname)  #@TODO NEEDS TO BE ADJUSTED
        out = R1.login(login_cmd, username, password, login_expect)
        if out != R1._LOGIN_USERNAME_PROMPTS:
            R1.logout()
            time.sleep(60)
            R1 = Router(hostname, logfile='C:\\Barik\\MyPythonWinProject\\SyslogAutomation\\TEST\\Log1.log')
            password = Localhost1.get_rsa_token()
            out = R1.login(login_cmd, login, password, login_expect)
        
        self._client=R1

        self.host=host
        self.login=login
        self.password=password
        if res<>True: #adjust to check @TODO
            raise RuntimeError("Could not login into cisco switch: %s"%host)

        inputsentence = []

    def logout(self):
        self._client.logout()
        
    def do(self,cmd):
        return self._client.exec_cmd(cmd)


    def interface_getvlanconfig(self,interfaceName):
        """
        return vlan config of interface
        """

    def interface_setvlan(self,interfaceName,fromVlanId,toVlanId,reset=False):
        """
        configure set of vlan's on interface
        @param reset when True older info is deleted and only this vlanrange is added
        """
    def interface_getArpMAC(self):
        """
        returns mac addresses an interface knows about (can be used to detect connected ports from servers)
        return dict as follows
        {$interfacename:[$macaddr1,$macaddr2,...]}
        """


    def interface_getall(self):
        """
        return info about interfaces on switch (name, macaddresses, types, ...)
        """
        raise RuntimeError("implement")
        return r

    def interface_getnames(self):
        raise RuntimeError("implement")
        return r

    def backup(self,name,destinationdir):
        raise RuntimeError("implement")
        return r        
        self.do("/system/backup/save", args={"name":name})
        path="%s.backup"%name
        self.download(path, j.system.fs.joinPaths(destinationdir,path))
        self.do("/export", args={"file":name})
        path="%s.rsc"%name
        self.download(path, j.system.fs.joinPaths(destinationdir,path))

    def download(self,path,dest):
        #@todo now sure how that works on cisco sw
        from ftplib import FTP
        ftp=FTP(host=self.host, user=self.login, passwd=self.password)
        ftp.retrbinary('RETR %s'%path, open(dest, 'wb').write)
        ftp.close()
