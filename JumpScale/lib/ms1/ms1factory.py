from JumpScale import j
import JumpScale.baselib.txtrobot
import JumpScale.lib.ms1
import ujson as json

robotdefinition="""
machine (m)
- list (l)

- new (create,c,n)
-- name
-- description (descr)
-- memsize  #size is 0.5,1,2,4,8,16 in GB
-- ssdsize  #10,20,30,40,100 in GB

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

####
global required variables
spacesecret=
"""

class MS1RobotFactory(object):

    def getRobot(self):
        robot = j.tools.txtrobot.get(robotdefinition)
        cmds = MS1RobotCmds()
        robot.addCmdClassObj(cmds)
        return robot

class MS1RobotCmds():

    def machine__new(self, **args):
        machine_id = j.tools.ms1.deployMachineDeck(**args)
        return 'Machine created successfully. Machine ID: %s' % machine_id

    def machine__list(self, **args):
        return j.tools.ms1.listMachinesInSpace(**args)

    def machine__delete(self, **args):
        if j.tools.ms1.deleteMachine(**args):
            return 'Machine %s was deleted successfully' % args['name']
        else:
            return 'There was a problem deleting machine %s' % args['name']

    def machine__start(self, **args):
        if j.tools.ms1.startMachine(**args):
            return 'Machine %s was started successfully' % args['name']
        else:
            return 'There was a problem starting machine %s' % args['name']

    def machine__stop(self, **args):
        if j.tools.ms1.stopMachine(**args):
            return 'Machine %s was stopped successfully' % args['name']
        else:
            return 'There was a problem stopping machine %s' % args['name']

    def machine__snapshot(self, **args):
        if j.tools.ms1.snapshotMachine(**args):
            return 'Snapshot %s was created successfully' % args['snapshotname']
        else:
            return 'There was a problem creating snapshot %s' % args['snapshotname']

    def machine__tcpportforward(self, **args):
        if j.tools.ms1.createTcpPortForwardRule(**args):
            return 'Port-forwarding rule was created successfully. Port %s on machine %s was forwarded to %s port %s' % (args['machinetcpport'], args['name'], args['pubip'], args['pubipport'])
        else:
            return 'There was a problem creating port-forwarding rule'

    def machine__udpportforward(self, **args):
        if j.tools.ms1.createUdpPortForwardRule(**args):
            return 'Port-forwarding rule was created successfully. Port %s on machine %s was forwarded to %s port %s' % (args['machineudpport'], args['name'], args['pubip'], args['pubipport'])
        else:
            return 'There was a problem creating port-forwarding rule'

    def machine__execssh(self, **args):
        pass