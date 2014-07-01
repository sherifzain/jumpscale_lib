import requests
import time
from JumpScale import j
import JumpScale.portal

import JumpScale.baselib.remote
import JumpScale.baselib.redis
import JumpScale.portal
import ujson as json

class MS1(object):

    def __init__(self):
        self.secret = ''
        self.IMAGE_NAME = 'Ubuntu 14.04 (JumpScale)'
        self.redis_cl = j.clients.redis.getGeventRedisClient('localhost', int(j.application.config.get('redis.port.redisp')))

    def getCloudspaceObj(self, space_secret,**args):
        if not self.redis_cl.hexists('cloudrobot:cloudspaces:secrets', space_secret):
            raise RuntimeError("E:Space secret does not exist, cannot continue (END)")
        space=json.loads(self.redis_cl.hget('cloudrobot:cloudspaces:secrets', space_secret))
        return space

    def getCloudspaceId(self,space_secret,**args):
        cs=self.getCloudspaceObj(space_secret)
        return cs["id"]

    def setClouspaceSecret(self, login, password, cloudspace_name, location, spacesecret=None,**args):
        params = {'username': login, 'password': password, 'authkey': ''}
        response = requests.post('https://www.mothership1.com/restmachine/cloudapi/users/authenticate', params)
        if response.status_code != 200:
            raise RuntimeError("E:Could not authenticate user %s" % login)
        auth_key = response.json()
        params = {'authkey': auth_key}
        response = requests.post('https://www.mothership1.com/restmachine/cloudapi/cloudspaces/list', params)
        cloudspaces = response.json()
        
        cloudspace = [cs for cs in cloudspaces if cs['name'] == cloudspace_name and cs['location'] == location]
        if cloudspace:
            cloudspace = cloudspace[0]
        else:
            raise RuntimeError("E:Could not find a matching cloud space with name %s and location %s" % (cloudspace_name, location))

        self.redis_cl.hset('cloudrobot:cloudspaces:secrets', auth_key, json.dumps(cloudspace))
        return auth_key

    def getApiConnection(self, space_secret,**args):
        cs=self.getCloudspaceObj(space_secret)

        host = 'www.mothership1.com' if cs["location"] == 'ca1' else '%s.mothership1.com' % cs["location"]
        try:
            api=j.core.portal.getClient(host, 443, space_secret)
        except Exception,e:
            raise RuntimeError("E:Could not login to MS1 API.")

        # system = api.getActor("system", "contentmanager")

        return api            

    def deployAppDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, jpdomain='solutions', jpname=None, config=None, description=None,**args):
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

    def deployMachineDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, description='',**args):
        # get actors
        api = self.getApiConnection(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        images_actor = api.getActor('cloudapi', 'images')
        machines_actor = api.getActor('cloudapi', 'machines')
        sizes_actor = api.getActor('cloudapi', 'sizes')

        # validate args
        cloudspace_id = self.getCloudspaceId(spacesecret)
        image_ids = [image['id'] for image in images_actor.list() if image['name'] == self.IMAGE_NAME]
        if len(image_ids)==0:
            raise RuntimeError('E:Could not find a matching image')
        size_ids = [size['id'] for size in sizes_actor.list() if size['memory'] == int(memsize)]
        if len(size_ids)==0:
            raise RuntimeError('E:Could not find a matching size')
        # create machine
        machine_id = machines_actor.create(cloudspaceId=cloudspace_id, name=name, description=description, sizeId=size_ids[0], imageId=image_ids[0], disksize=int(ssdsize))
        return machine_id

    def listMachinesInSpace(self, spacesecret,**args):
        # get actors
        api = self.getApiConnection(spacesecret)        
        machines_actor = api.getActor('cloudapi', 'machines')
        cloudspace_id = self.getCloudspaceId(spacesecret)
        # list machines
        machines = machines_actor.list(cloudspaceId=cloudspace_id)
        return machines

    def _getMachineApiActorId(self, spacesecret, name,**args):
        api=self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        machine_id = [machine['id'] for machine in machines_actor.list(cloudspace_id) if machine['name'] == name]
        if len(machine_id)==0:
            raise RuntimeError("E:Could not find machine with name:%s, could not start."%name)
        machine_id = machine_id[0]
        actor=api.getActor('cloudapi', 'machines')
        return (api,actor,machine_id,cloudspace_id)

    def deleteMachine(self, spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.delete(machine_id)
        except Exception,e:
            raise RuntimeError("E:could not start machine.")
        return "OK"

    def startMachine(self, spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.start(machine_id)
        except Exception,e:
            raise RuntimeError("E:could not start machine.")
        return "OK"

    def stopMachine(self, spacesecret, name,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.stop(machine_id)
        except Exception,e:
            raise RuntimeError("E:could not stop machine.")
        return "OK"

    def snapshotMachine(self, spacesecret, name, snapshotname,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        try:
            machines_actor.snapshot(machine_id,snapshotname)
        except Exception,e:
            raise RuntimeError("E:could not stop machine.")
        return "OK"

    def createTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip, pubipport,**args):
        return self._createPortForwardRule(spacesecret, name, machinetcpport, pubip, pubipport, 'tcp')

    def createUdpPortForwardRule(self, spacesecret, name, machineudpport, pubip, pubipport,**args):
        return self._createPortForwardRule(spacesecret, name, machineudpport, pubip, pubipport, 'udp')

    def _createPortForwardRule(self, spacesecret, name, machineport, pubip, pubipport, protocol,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        portforwarding_actor.create(cloudspace_id, pubip, pubipport, machine_id, machineport, protocol)
        return "OK"

    def execSshScript(self, spacesecret, name, sshport, script,**args):
        api = self.getApiConnection(spacesecret)
        machines_actor = api.getActor('cloudapi', 'machines')
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')

        cloudspace_id = self.getCloudspaceId(spacesecret)
        machine_id = [machine['id'] for machine in machines_actor.list(cloudspace_id) if machine['name'] == name]
        if not machine_id:
            return 'Machine %s does not exist' % name
        machine = machines_actor.get(machine_id[0])
        if machine['cloudspaceid'] != cloudspace_id:
            return 'Machine %s does not belong to cloudspace whose secret is given' % name
        cloudspace = cloudspaces_actor.get(cloudspace_id)
        if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(sshport), 5):
            return "Failed to connect to %s %s" % (cloudspace['publicipaddress'], sshport)

        ssh_connection = j.remote.cuisine.api
        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
        ssh_connection.fabric.api.env['password'] = password
        ssh_connection.fabric.api.env['connection_attempts'] = 5
        ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], sshport), username)
        if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(sshport), 60):
            return "Failed to connect to %s %s" % (cloudspace['publicipaddress'], ssh_port)
        return ssh_connection.sudo(script)
