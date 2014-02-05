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

    def configure(self, nicNamePub, nicNameDMZ, SecurityPolicyObject):
        policyfile = j.system.fs.joinPaths(self.configPath, 'policy')
        config = self._policyToConfig(SecurityPolicyObject)
        self.remoteApi.run('touch %s' % policyfile)
        self.remoteApi.file_write(policyfile, config)

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
