from JumpScale import j
import JumpScale.baselib.remote
import JumpScale.baselib.serializers

class ShorewallFactory(object):

    def get(self, host, password):
        return Shorewall(host, password)


class Shorewall(object):

    def __init__(self, host, password):
        self.configPath = j.system.fs.joinPaths('/etc', 'shorewall')
        self.remoteApi = j.remote.cuisine.api
        j.remote.cuisine.fabric.env['password'] = password
        self.remoteApi.connect(host)

    def configure(self, fwObject):
        policyfile = j.system.fs.joinPaths(self.configPath, 'rules')
        json = j.db.serializers.getSerializerType('j')
        tcpForwardRules = json.loads(fwObject).get('tcpForwardRules')
        config = ''
        for rule in tcpForwardRules:
            config += 'DNAT net $FW:%s:%s tcp %s\n' % (rule['toAddr'], rule['toPort'], rule['fromPort'])

        self.remoteApi.run('touch %s' % policyfile)
        self.remoteApi.file_write(policyfile, config)
        self.remoteApi.run('shorewall restart')

    def start(self):
        self.remoteApi.run('shorewall start')

    def stop(self):
        self.remoteApi.run('shorewall stop')

    def restart(self):
        self.remoteApi.run('shorewall restart')

    def status(self):
        return 'stopped' not in self.remoteApi.run('shorewall status', warn_only=True)
