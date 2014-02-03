from JumpScale import j
import JumpScale.baselib.remote

class DhcpFactory(object):

    def get(self, host, password):
        return DHCP(host, password)

class DHCP(object):
    
    def __init__(self, host, password):
        self.configPath = j.system.fs.joinPaths('/etc', 'dhcp3', 'dhcpd.conf')
        self.remoteApi = j.remote.cuisine.api
        j.remote.cuisine.fabric.env['password'] = password
        self.remoteApi.connect(host)

    def configure(self, ipFrom, ipTo):
        config = '''default-lease-time 600;
max-lease-time 7200;
option subnet-mask 255.255.255.0;

subnet 192.168.1.0 netmask 255.255.255.0 {
range %s %s;
}''' % (ipFrom, ipTo)
        self.remoteApi.run('touch %s' % self.configPath)
        self.remoteApi.file_write(self.configPath, config)
        self.restart()

    def start(self):
        self.remoteApi.run('service isc-dhcp-server start')

    def stop(self):
        self.remoteApi.run('service isc-dhcp-server stop')

    def restart(self):
        self.remoteApi.run('service isc-dhcp-server restart')