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

    def configure(self, fwObject):
        json = j.db.serializers.getSerializerType('j')
        fwDict = json.loads(fwObject)
        wsForwardRules = fwDict.get('wsForwardRules')
        configfile = j.system.fs.joinPaths(self.configPath, '%s.conf' % fwDict['name'])
        config = ''
        for rule in wsForwardRules:
            if len(rule['toUrls']) == 1:
                config += '''server {
    listen 80;
    server_name _;
    location %s {
        proxy_pass       %s;
        proxy_set_header Host      $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}''' % (rule['url'], rule['toUrls'][0])
            else:
                config += '''
upstream %s {
''' % fwDict['name']
                for toUrl in rule['toUrls']:
                    config += '    server %s;\n' % toUrl
                config += '}\n'
                config += '''
server {
    listen 80;
    server_name _;
    location %s {
        proxy_pass  http://%s;
    }
}''' % (rule['url'], fwDict['name'])

        if config:
            self.remoteApi.run('touch %s' % configfile)
            self.remoteApi.file_write(configfile, config)
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

    def restart(self):
        self.remoteApi.run('service nginx restart')