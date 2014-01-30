from JumpScale import j
import JumpScale.baselib.remote
import JumpScale.baselib.serializers

class NginxFactory(object):

    def get(self, host, password):
        return Nginx(host, password)


class Nginx(object):

    def __init__(self, host, password):
        self.configPath = j.system.fs.joinPaths('/etc', 'nginx', 'conf.d')
        self.remoteApi = j.remote.cuisine.api
        j.remote.cuisine.fabric.env['password'] = password
        self.remoteApi.connect(host)

    def list(self):
        configfiles = self.remoteApi.run('ls %s' % self.configPath)
        return configfiles.split('  ')

    def configureLB(self, name, webLBPolicy):
        lbfile = j.system.fs.joinPaths(self.configPath, '%s.conf' % name)
        config = self._policyToConfig(webLBPolicy)
        self.remoteApi.run('touch %s' % lbfile)
        self.remoteApi.file_write(lbfile, config)
        self.reload()

    def configureWS(self, name, webServicePolicy):
        wsfile = j.system.fs.joinPaths(self.configPath, '%s.conf' % name)
        config = self._policyToConfig(webServicePolicy)
        self.remoteApi.run('touch %s' % wsfile)
        self.remoteApi.file_write(wsfile, config)
        self.reload()

    def deleteConfig(self, name):
        configfile = j.system.fs.joinPaths(self.configPath, '%s.conf' % name)
        if self.remoteApi.file_exists(configfile):
            self.remoteApi.run('rm %s' % configfile)
            self.reload()

    def start(self):
        self.remoteApi.run('service nginx start')

    def stop(self):
        self.remoteApi.run('service nginx stop')

    def reload(self):
        self.remoteApi.run('service nginx reload')

    def _policyToConfig(self, policy):
        json = j.db.serializers.getSerializerType('j')
        policydict = json.loads(policy)

        def _printDict(dictval):
            result = ''
            for key, innerval in dictval.iteritems():
                if type(innerval) is str:
                    result += '%s %s;\n' % (key, innerval)
                elif type(innerval) in (list, tuple):
                    result += '%s %s;\n' % (key, ' '.join(map(lambda x: str(x), innerval)))
                elif type(innerval) is dict:
                    result += '%s\n{\n%s}\n' % (key, _printDict(innerval))
            return result

        return _printDict(policydict)
