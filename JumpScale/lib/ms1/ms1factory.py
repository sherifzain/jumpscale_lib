from JumpScale import j
import JumpScale.lib.txtrobot
import JumpScale.lib.ms1
import ujson as json

robotdefinition="""
mothership1 (ms1)
- login
-- login
-- password
-- cloudspace_name
-- location #ca1,us1,us2,be1

machine (m)
- list (l)

- new (create,c,n)
-- name
-- description (descr)
-- memsize  #size is 0.5,1,2,4,8,16 in GB
-- ssdsize  #10,20,30,40,100 in GB
-- template (image) #id or name of template to start from

- delete (del)
-- name (n)

- stop
-- name (n)

- start
-- name (n)

- snapshot
-- name (n)
-- snapshotname (sname)

- tcpportforward
-- name (n)
-- machinetcpport
-- pubip
-- pubipport

- udpportforward
-- name (n)
-- machineudpport
-- pubip
-- pubipport

- execssh
-- name (n)
-- sshport
-- script #predefined vars: $passwd,$ipaddr,$name

- setpasswd
-- name (n)
-- passwd (password)

- execcuisine (cuisine)
-- name (n)
-- script #predefined vars: $passwd,$ipaddr,$name

- execjs (execjumpscript,js,jumpscript)
-- name (n)
-- script #predefined vars: $passwd,$ipaddr,$name

- initjs (initjumpscale)
-- name (n)

- initjsdebug (initjumpscaledebug)
-- name (n)

template (templates,image,images)
- list


####
global required variables
spacesecret=

examples
--------
!machine.list

!machine.new
name=aname
description=mydescr
memsize=1
ssdsize=10


"""
import JumpScale.portal

class MS1RobotFactory(object):

    def getRobot(self):
        robot = j.tools.txtrobot.get(robotdefinition)
        cmds = MS1RobotCmds()
        robot.addCmdClassObj(cmds)
        return robot

class MS1RobotCmds():

    def machine__new(self, **args):
        template=args["template"]        
        res=j.tools.ms1.listImages(**args)
        try:
            templateid=int(template)
        except:
            templateid=0
        if templateid==0:
            if not res.has_key(template.lower().strip()):
                raise RuntimeError("E:Cannot find template with name %s, please use !template.list to find available templates."%template)
            else:
                templateid=res[template.lower().strip()][0]           
            
        machine_id = j.tools.ms1.deployMachineDeck(templateid=templateid,**args)
        return 'Machine created successfully. Machine ID: %s ' % machine_id

    def machine__list(self, **args):
        return j.tools.ms1.listMachinesInSpace(**args)

    def machine__delete(self, **args):
        j.tools.ms1.deleteMachine(**args)
        return 'Machine %s was deleted successfully ' % args['name']

    def machine__start(self, **args):
        status = j.tools.ms1.startMachine(**args)
        return 'Machine %s was started successfully.' % (args['name'])        

    def machine__stop(self, **args):
        status = j.tools.ms1.stopMachine(**args)
        return 'Machine %s was stopped successfully.' % (args['name'])        

    def machine__snapshot(self, **args):
        status = j.tools.ms1.snapshotMachine(**args)
        return 'Snapshot %s for %s was successfull.' % (args['snapshotname'],args['name'])

    def machine__tcpportforward(self, **args):
        status = j.tools.ms1.createTcpPortForwardRule(**args)
        return 'Port-forwarding rule was created successfully.' 

    def machine__udpportforward(self, **args):
        status = j.tools.ms1.createUdpPortForwardRule(**args)
        return 'Port-forwarding rule was created successfully.' 

    def machine__execssh(self, **args):
        return j.tools.ms1.execSshScript(**args)

    def mothership1__login(self, **args):
        result = j.tools.ms1.setClouspaceSecret(**args)
        return "spacesecret=%s" % (result)

    def image__list(self, **args):
        out=""
        res=j.tools.ms1.listImages(**args)

        keys=res.keys()
        keys.sort()
        
        for key in keys:
            id,fullname=res[key]
            out+="%-20s (%-2s) %s\n"%(key,id,fullname)
        return out

