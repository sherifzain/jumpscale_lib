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

- delete
-- name (n)

- tcpportforward
-- name (n)
-- machinetcpport
-- pubip
-- pubipport

- udpportforward
-- name (n)
-- machinetcpport
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

    def __init__(self):
        self.location = j.tools.ms1.validateSpaceSecrert(None)

    def getLoginPasswd(self, **args):
        if not args.has_key("login") or not args.has_key("passwd"):
            self.txtrobot.error("could not find login & passwd info, please specify login=..\npasswd=..\n\n before specifying any cmd")
        return args["login"],args["passwd"]

    def machine__new(self, **args):
        login, password = self.getLoginPasswd(**args)
        j.tools.ms1.getSecret(login, password, True)
        args.pop('login')
        args.pop('passwd')
        machine_id = j.tools.ms1.deployMachineDeck(self.location, **args)
        return 'Machine created successfully. Machine ID: %s' % machine_id

    def machine__list(self):
        j.tools.ms1.listMachinesInSpace(self.location)

    def machine__delete(self, **args):
        login, password = self.getLoginPasswd(**args)
        j.tools.ms1.getSecret(login, password, True)
        args.pop('login')
        args.pop('passwd')
        j.tools.ms1.deleteMachine(self.location, **args)

    def machine__start(self, **args):
        login, password = self.getLoginPasswd(**args)
        j.tools.ms1.getSecret(login, password, True)
        args.pop('login')
        args.pop('passwd')
        j.tools.ms1.startMachine(self.location, **args)

    def machine__stop(self, **args):
        login, password = self.getLoginPasswd(**args)
        j.tools.ms1.getSecret(login, password, True)
        args.pop('login')
        args.pop('passwd')
        j.tools.ms1.stopMachine(self.location, **args)

    def machine__snapshot(self, **args):
        login, password = self.getLoginPasswd(**args)
        j.tools.ms1.getSecret(login, password, True)
        args.pop('login')
        args.pop('passwd')
        j.tools.ms1.snapshotMachine(self.location, **args)