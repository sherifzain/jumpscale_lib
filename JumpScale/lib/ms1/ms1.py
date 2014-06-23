import requests
import time
from JumpScale import j
import JumpScale.portal
import JumpScale.baselib.remote
import JumpScale.baselib.redis

class MS1(object):

    def __init__(self):
        self.secret = ''
        self.IMAGE_NAME = 'Ubuntu 14.04 (JumpScale)'
        self.redis_cl = j.clients.redis.getGeventRedisClient('localhost', int(j.application.config.get('redis.port.redisp')))

    def getCloudspaceId(self, space_secret):
        if not self.redis_cl.hexists('cloudspaces:secrets', space_secret):
            raise RuntimeError('Space secret does not exist')
        return int(self.redis_cl.hget('cloudspaces:secrets', space_secret))

    def getCloudspaceLocation(self, space_secret):
        cloudspace_id = self.getCloudspaceId(space_secret)
        portal_client = j.core.portal.getClient('www.mothership1.com', 443, space_secret)
        cloudspaces_actor = portal_client.getActor('cloudapi', 'cloudspaces')
        cloudspace = [cs for cs in cloudspaces_actor.list() if cs['id'] == cloudspace_id][0] # TODO use get instead of list
        return cloudspace['location']

    def getApiConnection(self, space_secret):
        location = self.getCloudspaceLocation(space_secret)
        host = 'www.mothership1.com' if location == 'ca1' else '%s.mothership1.com' % location
        return j.core.portal.getClient(host, 443, space_secret)

    def deployAppDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, jpdomain='solutions', jpname=None, config=None, description=None):
        machine_id = self.deployMachineDeck(spacesecret, name, memsize, ssdsize, vsansize, description)
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
        if not j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
            raise RuntimeError('Machine was created, but never got an IP address')
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
        if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(ssh_port), 60):
            raise RuntimeError("Failed to connect to %s %s" % (cloudspace['publicipaddress'], ssh_port))
        ssh_connection = j.remote.cuisine.api
        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
        ssh_connection.fabric.api.env['password'] = password
        ssh_connection.fabric.api.env['connection_attempts'] = 5
        ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], ssh_port), username)

        # install jpackages there
        ssh_connection.sudo('jpackage mdupdate')
        if config:
            jpackage_hrd_file = j.system.fs.joinPaths(j.dirs.hrdDir, '%s_%s' % (jpdomain, jpname))
            ssh_connection.file_write(jpackage_hrd_file, config, sudo=True)
        if jpdomain and jpname:
            ssh_connection.sudo('jpackage install -n %s -d %s' % (jpname, jpdomain))

        #cleanup 
        cloudspace_forward_rules = portforwarding_actor.list(machine['cloudspaceid'])
        ssh_rule_id = [rule['id'] for rule in cloudspace_forward_rules if rule['publicPort'] == ssh_port][0]
        portforwarding_actor.delete(machine['cloudspaceid'], ssh_rule_id)
        if config:
            hrd = j.core.hrd.getHRD(content=config)
            if hrd.exists('services_ports'):
                ports = hrd.getList('services_ports')
                for port in ports:
                    portforwarding_actor.create(machine['cloudspaceid'], cloudspace['publicipaddress'], str(port), machine['id'], str(port))
        return {'publicip': cloudspace['publicipaddress']}

    def deployMachineDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, description=''):
        # get actors
        api = self.getApiConnection(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        images_actor = api.getActor('cloudapi', 'images')
        machines_actor = api.getActor('cloudapi', 'machines')
        sizes_actor = api.getActor('cloudapi', 'sizes')

        # validate args
        cloudspace_id = self.getCloudspaceId(spacesecret)
        image_ids = [image['id'] for image in images_actor.list() if image['name'] == self.IMAGE_NAME]
        if not image_ids:
            raise RuntimeError('Could not find a matching image')
        size_ids = [size['id'] for size in sizes_actor.list() if size['memory'] == int(memsize)]
        if not size_ids:
            raise RuntimeError('Could not find a matching size')
        # create machine
        machine_id = machines_actor.create(cloudspaceId=cloudspace_id, name=name, description=description, sizeId=size_ids[0], imageId=image_ids[0], disksize=int(ssdsize))
        return machine_id

    def listMachinesInSpace(self, spacesecret):
        # get actors
        api = self.getApiConnection(spacesecret)
        machines_actor = api.getActor('cloudapi', 'machines')
        cloudspace_id = self.getCloudspaceId(spacesecret)

        # list machines
        machines = machines_actor.list(cloudspaceId=cloudspace_id)
        return machines

    def deleteMachine(self, location, name):
        # get actors
        api = self.getApiConnection(location)
        machines_actor = api.getActor('cloudapi', 'machines')

        # delete machine
        machine_id = [machine['id'] for machine in machines_actor.list() if machine['name'] == name]
        if not machine_id:
            raise
        machine_id = machine_id[0]

        machine = machines_actor.delete(machine_id)
        return True

    def startMachine(self, location, name):
        # get actors
        api = self.getApiConnection(location)
        machines_actor = api.getActor('cloudapi', 'machines')

        # start machine
        machine_id = [machine['id'] for machine in machines_actor.list() if machine['name'] == name]
        if not machine_id:
            raise
        machine_id = machine_id[0]
        machine = machines_actor.start(machine_id)
        return True

    def stopMachine(self, location, name):
        # get actors
        api = self.getApiConnection(location)
        machines_actor = api.getActor('cloudapi', 'machines')

        # stop machine
        machine_id = [machine['id'] for machine in machines_actor.list() if machine['name'] == name]
        if not machine_id:
            raise
        machine_id = machine_id[0]
        machine = machines_actor.stop(machine_id)
        return True

    def snapshotMachine(self, location, name, ssname):
        # get actors
        api = self.getApiConnection(location)
        machines_actor = api.getActor('cloudapi', 'machines')

        # take a snapshot of machine
        machine_id = [machine['id'] for machine in machines_actor.list() if machine['name'] == name]
        if not machine_id:
            raise
        machine_id = machine_id[0]
        machine = machines_actor.snapshot(machine_id, ssname)
        return True
