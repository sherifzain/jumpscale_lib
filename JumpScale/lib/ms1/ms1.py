import requests
import time
from JumpScale import j
import JumpScale.portal
import JumpScale.baselib.remote

class MS1(object):

    def __init__(self):
        self.secret = ''
        self.IMAGE_NAME = 'Ubuntu 14.04 (JumpScale)'

    def getSecret(self, login, password, remember=False):
        params = {'username': login, 'password': password, 'authkey': ''}
        request = requests.post('https://www.mothership1.com/restmachine/cloudapi/users/authenticate', params)
        if request.status_code == 200:
            self.secret = request.json()
            if remember:
                self.rememberSecret()
        else:
            raise RuntimeError('Invalid username and/or password')

    def rememberSecret(self):
        hrd_path = j.system.fs.joinPaths(j.dirs.hrdDir, 'ms1.hrd')
        j.system.fs.writeFile(hrd_path, 'ms1.secret=%s' % self.secret)

    def getApiConnection(self, location):
        host = 'www.mothership1.com' if location == 'ca1' else '%s.mothership1.com' % location
        return j.core.portal.getClient(host, 443, self.secret)

    def deployAppDeck(self, location, name, memsize=1024, ssdsize=40, vsansize=0, jpdomain='', jpname='', config='', description=''):
        machine_id = self.deployMachineDeck(location, name, memsize, ssdsize, vsansize, description)
        api = self.getApiConnection(location)
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        machines_actor = api.getActor('cloudapi', 'machines')
        # create ssh port-forward rule
        for _ in range(30):
            machine = machines_actor.get(machine_id)
            if j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
                break
            else:
                time.sleep(2)
        cloudspace_forward_rules = portforwarding_actor.list(machine['cloudspaceid'])
        public_ports = [rule['publicPort'] for rule in cloudspace_forward_rules]
        ssh_port = '2222'
        cloudspace = cloudspaces_actor.get(machine['cloudspaceid'])
        while True:
            if ssh_port not in public_ports:
                portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], ssh_port, machine['id'], '22')
                break
            else:
                ssh_port = str(int(ssh_port) + 1)

        # do an ssh connection to the machine
        ssh_connection = j.remote.cuisine.api
        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
        ssh_connection.fabric.api.env['password'] = password
        ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], ssh_port), username)

        # install jpackages there
        ssh_connection.sudo('jpackage mdupdate')
        if config:
            jpackage_hrd_file = j.system.fs.joinPaths(j.dirs.hrdDir, '%s_%s' % (jpdomain, jpname))
            ssh_connection.file_write(jpackage_hrd_file, config, sudo=True)
        if jpdomain and jpname:
            ssh_connection.sudo('jpackage install -n %s -d %s' % (jpname, jpdomain))

        #cleanup 
        ssh_rule_id = [rule['id'] for rule in cloudspace_forward_rules if rule['publicPort'] == ssh_port][0]
        portforwarding_actor.delete(machine['cloudspaceid'], ssh_rule_id)
        if config:
            hrd = j.core.hrd.getHRD(config)
            if hrd.exists('services_ports'):
                ports = hrd.getList('services_ports')
                for port in ports:
                    portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], str(port), machine['id'], str(port))

    def deployMachineDeck(self, location, name, memsize=1024, ssdsize=40, vsansize=0, description=''):
        # get actors
        api = self.getApiConnection(location)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        images_actor = api.getActor('cloudapi', 'images')
        machines_actor = api.getActor('cloudapi', 'machines')
        sizes_actor = api.getActor('cloudapi', 'sizes')

        # validate args
        cloudspace_ids = [cs['id'] for cs in cloudspaces_actor.list() if cs['location'] == location]
        if not cloudspace_ids:
            raise RuntimeError('Could not find a matching cloudspace')
        image_ids = [image['id'] for image in images_actor.list() if image['name'] == self.IMAGE_NAME]
        if not image_ids:
            raise RuntimeError('Could not find a matching image')
        size_ids = [size['id'] for size in sizes_actor.list() if size['memory'] == memsize]
        if not size_ids:
            raise RuntimeError('Could not find a matching size')
        # create machine
        machine_id = machines_actor.create(cloudspaceId=cloudspace_ids[0], name=name, description=description, sizeId=size_ids[0], imageId=image_ids[0], disksize=ssdsize)
        return machine_id