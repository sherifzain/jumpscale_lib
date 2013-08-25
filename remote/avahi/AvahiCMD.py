from JumpScale import j
from JumpScale.core.Shell import *


class AvahiCMD():

    def __init__(self):
        pass

    def getServices(self):
        cmd = "avahi-browse -a -r -t"
        result, output = j.system.process.execute(cmd, False, False)
        if result > 0:
            raise RuntimeError(
                "cannot use avahi command line to find services, please check avahi is installed on system (ubunutu apt-get install avahi-utils)\nCmd Used:%s" % cmd)
        items = j.codetools.regex.extractBlocks(output, ["^= .*"])
        avahiservices = AvahiServices()
        for item in items:
            s = AvahiService()
            lineitems = item.split("\n")[0][1:].strip().split("  ")
            lineitemsout = []
            for lineitem in lineitems:
                if lineitem.strip() != "":
                    lineitemsout.append(lineitem.strip())
            if len(lineitemsout) == 3:
                s.description, s.servicename, s.domain = lineitemsout
            if len(lineitemsout) == 2:
                s.description, s.servicename = lineitemsout
                s.domain = ""
            if len(lineitemsout) < 2 or len(lineitemsout) > 3:
                s.servicename = lineitemsout[0]

            s.hostname = j.codetools.regex.getINIAlikeVariableFromText(" *hostname *", item).replace("[", "").replace("]", "").strip()
            s.address = j.codetools.regex.getINIAlikeVariableFromText(" *address *", item).replace("[", "").replace("]", "").strip()
            s.port = j.codetools.regex.getINIAlikeVariableFromText(" *port *", item).replace("[", "").replace("]", "").strip()
            s.txt = j.codetools.regex.getINIAlikeVariableFromText(" *txt *", item).replace("[", "").replace("]", "").strip()
            avahiservices._add(s)
        return avahiservices

    def resolveAddress(self, ipAddress):
        """
        Resolve the ip address to its hostname
        
        @param ipAddress: the ip address to resolve
        @type ipAddress: string
        
        @return: the hostname attached to the ip address
        """
        # do some validation
        if not j.system.net.validateIpAddress(ipAddress):
            raise ValueError('Invalid Ip Address')
        cmd = 'avahi-resolve-address %s'
        exitCode, output = j.system.process.execute(cmd % ipAddress, dieOnNonZeroExitCode=False, outputToStdout=False)
        if exitCode or not output:  # if the ouput string is '' then something is wrong
            raise RuntimeError('Cannot resolve the hostname of ipaddress: %s' % ipAddress)
        output = output.strip()
        hostname = output.split('\t')[-1]
        # remove the trailing .local
        hostname = hostname.replace('.local', '')
        return hostname


class AvahiServices():

    def __init__(self):
        self.services = []

    def _add(self, service):
        self.services.append(service)

    def find(self, hostname="", partofname="", partofdescription="", port=0):
        def check1(service, hostname):
            if hostname != "" and service.hostname.lower().strip() == hostname.lower().strip():
                return True
            if hostname == "":
                return True
            return False

        def check4(service, partofname):
            if partofname != "" and service.servicename.find(partofname) > -1:
                return True
            if partofname == "":
                return True
            return False

        def check2(service, partofdescription):
            if partofdescription != "" and service.description.find(partofdescription) > -1:
                return True
            if partofdescription == "":
                return True
            return False

        def check3(service, port):
            if int(port) != 0 and int(service.port) == int(port):
                return True
            if int(port) == 0:
                return True
            return False
        result = []
        for service in self.services:
            if check1(service, hostname) and check2(service, partofdescription) and check3(service, port) and check4(service, partofname):
                result.append(service)
        return result

    def __str__(self):
        txt = ""
        for item in self.services:
            txt = "%s%s\n" % (txt, item)
        return txt

    def __repr__(self):
        return self.__str__()


class AvahiService():

    def __init__(self):
        self.servicename = ""
        self.hostname = ""
        self.address = ""
        self.port = 0
        self.txt = ""
        self.description = ""
        self.domain = ""

    def __str__(self):
        return "descr:%s name:%s hostname:%s address:%s port:%s" % (self.description, self.servicename, self.hostname, self.address, self.port)

    def __repr__(self):
        return self.__str__()
