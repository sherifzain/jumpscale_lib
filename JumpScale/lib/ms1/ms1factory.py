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
    def _customizeMessage(self, cmd, success, **args):
        prepend = ''
        if success:
            prepend = '> '
        message = '%s%s<br/>' % (prepend, cmd)
        for arg, val in args.iteritems():
            if arg == 'spacesecret':
                continue
            message += '%s%s=%s<br/>' % (prepend, arg, val)
        return message

    def machine__new(self, **args):
        machine_id = j.tools.ms1.deployMachineDeck(**args)
        return 'Machine created successfully. Machine ID: %s ' % machine_id

    def machine__list(self, **args):
        return j.tools.ms1.listMachinesInSpace(**args)

    def machine__delete(self, **args):
        if j.tools.ms1.deleteMachine(**args):
            return 'Machine %s was deleted successfully ' % args['name']
        else:
            return 'There was a problem deleting machine %s ' % args['name']

    def machine__start(self, **args):
        status = j.tools.ms1.startMachine(**args)
        message = self._customizeMessage('!machine.start', status, **args)
        if status:
            return '%s> Machine %s was started successfully.<br/>' % (message, args['name'])
        else:
            return '%s< There was a problem starting machine %s.<br/>' % (message, args['name'])

    def machine__stop(self, **args):
        status = j.tools.ms1.stopMachine(**args)
        message = self._customizeMessage('!machine.stop', status, **args)
        if status:
            return '%s> Machine %s was stopped successfully.<br/>' % (message, args['name'])
        else:
            return '%s< There was a problem stopping machine %s.<br/>' % (message, args['name'])

    def machine__snapshot(self, **args):
        status = j.tools.ms1.snapshotMachine(**args)
        message = self._customizeMessage('!machine.snapshot', status, **args)
        if status:
            return '%s> Snapshot %s was created successfully.<br/>' % (message, args['snapshotname'])
        else:
            return '%s< There was a problem creating snapshot %s.<br/>' % (message, args['snapshotname'])

    def machine__tcpportforward(self, **args):
        status = j.tools.ms1.createTcpPortForwardRule(**args)
        message = self._customizeMessage('!machine.tcpportforward', status, **args)
        if status:
            return '%s> Port-forwarding rule was created successfully. Port %s on machine %s was forwarded to %s port %s ' % (message, args['machinetcpport'], args['name'], args['pubip'], args['pubipport'])
        else:
            return '%s< There was a problem creating port-forwarding rule.<br/>' % message

    def machine__udpportforward(self, **args):
        status = j.tools.ms1.createUdpPortForwardRule(**args)
        message = self._customizeMessage('!machine.udpportforward', status, **args)
        if status:
            return '%s> Port-forwarding rule was created successfully. Port %s on machine %s was forwarded to %s port %s ' % (message, args['machineudpport'], args['name'], args['pubip'], args['pubipport'])
        else:
            return '%s< There was a problem creating port-forwarding rule.<br/>' % message

    def machine__execssh(self, **args):
        return j.tools.ms1.execSshScript(**args)

    def mothership1__login(self, **args):
        status, result = j.tools.ms1.setClouspaceSecret(**args)
        message = self._customizeMessage('!mothership1.login', status, **args)
        if status:
            return result, '%s> This is your cloudspace secret %s.<br/>' % (message, result)
        else:
            return result, '%s< Login was not successfull. %s<br/>' % (message, result)