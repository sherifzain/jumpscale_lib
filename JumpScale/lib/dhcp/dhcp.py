from JumpScale import j
import netifaces
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

    def configure(self, ipFrom, ipTo, interface):
        interface = netifaces.ifaddresses(interface)[2]
        if j.remote.cuisine.api.file_exists(self.configPath):
            header = '''default-lease-time 600;
max-lease-time 7200;
'''
            self.remoteApi.run('touch %s' % self.configPath)
            self.remoteApi.file_write(self.configPath, header)

        config = '''
subnet %s netmask %s {
    option subnet-mask 255.255.255.0;
    option routers 10.0.0.1;
    range %s %s;
}''' % (interface['addr'], interface['netmask'], ipFrom, ipTo)

        self.remoteApi.file_append(self.configPath, config)
        self.restart()

    def start(self):
        self.remoteApi.run('service isc-dhcp-server start')

    def stop(self):
        self.remoteApi.run('service isc-dhcp-server stop')

    def restart(self):
        self.remoteApi.run('service isc-dhcp-server restart')