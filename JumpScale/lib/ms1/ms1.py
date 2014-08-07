import requests
import time
from JumpScale import j
import JumpScale.portal
import JumpScale.lib.cloudrobots

import JumpScale.baselib.remote
import JumpScale.baselib.redis
import JumpScale.portal
import ujson as json

class MS1(object):

    def __init__(self):
        self.secret = ''
        self.IMAGE_NAME = 'Ubuntu 14.04 (JumpScale)'
        self.redis_cl = j.clients.redis.getGeventRedisClient('localhost', 7768)


    def getCloudspaceObj(self, space_secret,**args):
        if not self.redis_cl.hexists('cloudrobot:cloudspaces:secrets', space_secret):
            raise RuntimeError("E:Space secret does not exist, cannot continue (END)")
        space=json.loads(self.redis_cl.hget('cloudrobot:cloudspaces:secrets', space_secret))
        return space


    def getCloudspaceId(self, space_secret):
        space=self.getCloudspaceObj(space_secret)
        return space["id"]

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

    # def getCloudspaceLocation(self, space_secret):
    #     cloudspace_id = self.getCloudspaceId(space_secret)
    #     portal_client = j.core.portal.getClient('www.mothership1.com', 443, space_secret)
    #     cloudspaces_actor = portal_client.getActor('cloudapi', 'cloudspaces')
    #     cloudspace = [cs for cs in cloudspaces_actor.list() if cs['id'] == cloudspace_id][0] # TODO use get instead of list
    #     return cloudspace['location']

#    def getApiConnection(self, space_secret):
#        location = self.getCloudspaceLocation(space_secret)
#        host = 'www.mothership1.com' if location == 'ca1' else '%s.mothership1.com' % location
#        try:
#            j.core.portal.getClient(host, 443, space_secret)
#        except Exception,e:
#            from IPython import embed
#            print "DEBUG NOW getApiConnection"
#            embed()
#            raise RuntimeError("E:Could not login to MS1 API.")

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

    def deployMachineDeck(self, spacesecret, name, memsize=1024, ssdsize=40, vsansize=0, description='',templateid=0,**args):
        """
        memsize  #size is 0.5,1,2,4,8,16 in GB
        ssdsize  #10,20,30,40,100 in GB
        imagename= fedora,windows,ubuntu.13.10,ubuntu.12.04,windows.essentials,ubuntu.14.04
                   zentyal,debian.7,arch,fedora,centos,opensuse,gitlab,ubuntu.jumpscale
        """
        ssdsize=int(ssdsize)
        memsize=int(memsize)
        ssdsizes={}
        ssdsizes[10]=10
        ssdsizes[20]=20
        ssdsizes[30]=30
        ssdsizes[40]=40
        ssdsizes[100]=100
        memsizes={}
        memsizes[0.5]=512
        memsizes[1]=1024
        memsizes[2]=2048
        memsizes[4]=4096
        memsizes[8]=8192
        memsizes[16]=16384
        if not memsizes.has_key(memsize):
            raise RuntimeError("E: supported memory sizes are 0.5,1,2,4,8,16 (is in GB), you specified:%s"%memsize)
        if not ssdsizes.has_key(ssdsize):
            raise RuntimeError("E: supported ssd sizes are 10,20,30,40,100  (is in GB), you specified:%s"%memsize)
        if templateid==0:
            raise RuntimeError("E: please specify templateid")


        # get actors
        api = self.getApiConnection(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        machines_actor = api.getActor('cloudapi', 'machines')
        sizes_actor = api.getActor('cloudapi', 'sizes')

        cloudspace_id = self.getCloudspaceId(spacesecret)

        j.cloudrobot.vars["cloudspace.id"]=cloudspace_id
        j.cloudrobot.vars["machine.name"]=name

        memsize2=memsizes[memsize]
        size_ids = [size['id'] for size in sizes_actor.list() if size['memory'] == int(memsize2)]
        if len(size_ids)==0:
            raise RuntimeError('E:Could not find a matching memory size %s'%memsize2)

        ssdsize2=ssdsizes[ssdsize]

        # create machine
        if not j.basetype.integer.check(templateid):
            raise RuntimeError("E:template id needs to be of type int, a bug happened, please contact MS1.")

        try:
            machine_id = machines_actor.create(cloudspaceId=cloudspace_id, name=name, description=description, \
                sizeId=size_ids[0], imageId=templateid, disksize=int(ssdsize2))
        except Exception,e:
            if str(e).find("Selected name already exists")<>-1:
                raise RuntimeError("E:Could not create machine it does already exist.")            
            raise RuntimeError("E:Could not create machine, unknown error.")
        
        j.cloudrobot.vars["machine.id"]=machine_id

        for _ in range(30):
            machine = machines_actor.get(machine_id)
            if j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
                break
            else:
                time.sleep(2)
        if not j.basetype.ipaddress.check(machine['interfaces'][0]['ipAddress']):
            raise RuntimeError('E:Machine was created, but never got an IP address')

        j.cloudrobot.vars["machine.ip.addr"]=machine['interfaces'][0]['ipAddress']
            
        return machine_id

    def listImages(self,spacesecret,**args):
        api = self.getApiConnection(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
        images_actor = api.getActor('cloudapi', 'images')
        result={}
        alias={}
        imagetypes=["ubuntu.jumpscale","fedora","windows","ubuntu.13.10","ubuntu.12.04","windows.essentials","ubuntu.14.04",\
            "zentyal","debian.7","arch","fedora","centos","opensuse","gitlab"]
        # imagetypes=["ubuntu.jumpscale"]        
        for image in images_actor.list():
            name=image["name"]
            # print "name:%s"%name
            namelower=name.lower()
            for imagetype in imagetypes:
                found=True
                # print "imagetype:%s"%imagetype
                for check in [item.strip().lower() for item in imagetype.split(".") if item.strip()<>""]:                    
                    if namelower.find(check)==-1:
                        found=False
                    # print "check:%s %s %s"%(check,namelower,found)
                if found:
                    result[imagetype]=[image["id"],image["name"]]
        return result

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
        machines_actor = api.getActor('cloudapi', 'machines')
        machine_id = [machine['id'] for machine in machines_actor.list(cloudspace_id) if machine['name'] == name]
        if len(machine_id)==0:
            raise RuntimeError("E:Could not find machine with name:%s, cannot continue action."%name)
        machine_id = machine_id[0]
        actor=api.getActor('cloudapi', 'machines')
        return (api,actor,machine_id,cloudspace_id)

    def deleteMachine(self, spacesecret, name,**args):
        try:        
            api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        except Exception,e:
            if str(e).find("Could not find machine")<>-1:
                return "NOTEXIST"
        try:
            machines_actor.delete(machine_id)
        except Exception,e:
            raise RuntimeError("E:could not delete machine %s"%name)
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

    def createTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip="", pubipport=22,**args):
        return self._createPortForwardRule(spacesecret, name, machinetcpport, pubip, pubipport, 'tcp')

    def createUdpPortForwardRule(self, spacesecret, name, machineudpport, pubip="", pubipport=22,**args):
        return self._createPortForwardRule(spacesecret, name, machineudpport, pubip, pubipport, 'udp')

    def deleteTcpPortForwardRule(self, spacesecret, name, machinetcpport, pubip, pubipport,**args):
        return self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'tcp')

    def _createPortForwardRule(self, spacesecret, name, machineport, pubip, pubipport, protocol,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        if pubip=="":
            cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
            cloudspace = cloudspaces_actor.get(cloudspace_id)   
            pubip=cloudspace['publicipaddress'] 
        j.cloudrobot.vars["space.ip.pub"]=pubip
        self._deletePortForwardRule(spacesecret, name, pubip, pubipport, 'tcp')
        portforwarding_actor.create(cloudspace_id, pubip, str(pubipport), machine_id, str(machineport), protocol)
        return "OK"

    def _deletePortForwardRule(self, spacesecret, name,pubip,pubipport, protocol,**args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')
        if pubip=="":
            cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')
            cloudspace = cloudspaces_actor.get(cloudspace_id)   
            pubip=cloudspace['publicipaddress'] 

        for item in portforwarding_actor.list(cloudspace_id):
            if int(item["publicPort"])==int(pubipport) and item['publicIp']==pubip:
                print "delete portforward: %s "%item["id"]
                portforwarding_actor.delete(cloudspace_id,item["id"])

        return "OK"        

    def getFreeIpPort(self,spacesecret,**args):
        api=self.getApiConnection(spacesecret)
        cloudspace_id = self.getCloudspaceId(spacesecret)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')

        vars={}
    
        space=cloudspaces_actor.get(cloudspace_id)
        vars["space.free.tcp.addr"]=space["publicipaddress"]
        j.cloudrobot.vars["space.ip.pub"]=space["publicipaddress"]
        pubip=space["publicipaddress"]

        portforwarding_actor = api.getActor('cloudapi', 'portforwarding')

        tcpports={}
        udpports={}
        for item in portforwarding_actor.list(cloudspace_id):
            if item['publicIp']==pubip:
                if item['protocol']=="tcp":
                    tcpports[int(item['publicPort'])]=True
                elif item['protocol']=="udp":
                    udpports[int(item['publicPort'])]=True

        for i in range(90,1000):
            if not tcpports.has_key(i) and not udpports.has_key(i):
                break

        if i>1000:
            raise RuntimeError("E:cannot find free tcp or udp port.")

        vars["space.free.tcp.port"]=str(i)
        vars["space.free.udp.port"]=str(i)

        return vars
        
        

    def _getSSHConnection(self, spacesecret, name, **args):
        api,machines_actor,machine_id,cloudspace_id=self._getMachineApiActorId(spacesecret,name)
        cloudspaces_actor = api.getActor('cloudapi', 'cloudspaces')

        machine = machines_actor.get(machine_id)
        if machine['cloudspaceid'] != cloudspace_id:
            return 'Machine %s does not belong to cloudspace whose secret is given' % name
        

        tempport=j.base.idgenerator.generateRandomInt(1000,1500)
        # tempport=1333

        counter=1
        localIP=machine["interfaces"][0]["ipAddress"]
        while localIP=="" or localIP.lower()=="undefined":
            print "NO IP YET"
            machine = machines_actor.get(machine_id)
            counter+=1
            time.sleep(0.5)
            if counter>100:
                raise RuntimeError("E:could not find ip address for machine:%s"%name)
            localIP=machine["interfaces"][0]["ipAddress"]        

        self.createTcpPortForwardRule(spacesecret, name, 22, pubipport=tempport)

        cloudspace = cloudspaces_actor.get(cloudspace_id)   
        pubip=cloudspace['publicipaddress'] 

        if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(tempport), 5):
            raise RuntimeError("E:Failed to connect to %s" % (tempport))

        ssh_connection = j.remote.cuisine.api
        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
        ssh_connection.fabric.api.env['password'] = password
        ssh_connection.fabric.api.env['connection_attempts'] = 5
        ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], tempport), username)
        # if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(sshport), 60):
        #     return "Failed to connect to %s %s" % (cloudspace['publicipaddress'], ssh_port)

        username, password = machine['accounts'][0]['login'], machine['accounts'][0]['password']
        ssh_connection.fabric.api.env['password'] = password
        ssh_connection.fabric.api.env['connection_attempts'] = 5
        ssh_connection.connect('%s:%s' % (cloudspace['publicipaddress'], tempport), username)
        # if not j.system.net.waitConnectionTest(cloudspace['publicipaddress'], int(sshport), 60):
        #     return "Failed to connect to %s %s" % (cloudspace['publicipaddress'], ssh_port)

        return ssh_connection

    def execSshScript(self, spacesecret, name, script,**args):
        
        ssh_connection=self._getSSHConnection(spacesecret,name,**args)

        out=""
        for line in script.split("\n"):
            line=line.strip()
            if line.strip()=="":
                continue
            if line[0]=="#":
                continue
            out+="%s\n"%line
            print line
            result= ssh_connection.sudo(line+"\n")
            out+="%s\n"%result
            print result

        self._deletePortForwardRule(spacesecret, name,cloudspace['publicipaddress'],1033,"tcp")

        return result
