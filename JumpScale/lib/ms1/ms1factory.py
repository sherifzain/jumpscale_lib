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
-- type     #type:arch,fedora,ubuntu,centos,opensuse,zentyal,debian,ubuntu13.10,ubuntu14.04,w2012_std,w2012_ess
-- typeid   #id type id used, type cannot be used

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

    def get(self, login, password):
        j.tools.ms1.getSecret(login, password, True)

    def getRobot(self):
        robot = j.tools.txtrobot.get(robotdefinition)
        cmds = MS1RobotCmds()
        robot.addCmdClassObj(cmds)
        return robot

class MS1RobotCmds():
    def __init__(self):
        self.location = j.tools.ms1.validateSpaceSecrert(spacesecret='')

    def machine__create(self, **args):
        j.tools.ms1.deployMachineDeck(self.location, **args)

    def machine__list(self):
        j.tools.ms1.listMachinesInSpace(self.location)

    def machine__delete(self, **args):
        j.tools.ms1.deleteMachine(self.location, **args)

    def machine__start(self, **args):
        j.tools.ms1.startMachine(self.location, **args)

    def machine__stop(self, **args):
        j.tools.ms1.stopMachine(self.location, **args)

    def machine__snapshot(self, **args):
        j.tools.ms1.snapshotMachine(self.location, **args)
