from JumpScale import j

class TxtRobotHelp(object):       

    def intro(self):
        help="""
get detailed help by using one of following commands

#explain how to use the robot
help

#show help how commands are defined 
!help.definition

#explain the available cmds in this robot
!help.cmds

"""
        return '%s ' % help


    def help(self):
        help="""
The format of each message is:
'
login=mylogin
passwd=mypasswd

!entity.cmd
anotherparam=val
'

entity is something line project, user, invoice, machine...

#everything starting with ! is a cmdline
#the lines after the cmdline are all the arguments

##example:
!project.list

!issue.create
name=aname
descr=descr of issue
deadline=6d

#everything before the first ! are considered to be global params e.g. login, passwd, url, ...

available commands can be asked for by sending command:  !help.cmds

variables can be multiline by using special instruction ...
description=...
this is multiline
text
.
name=aname

the multiline stops when . or # or ! found


"""
        return '%s ' % help

    def help_definition(self):
        help="""
each robot has a definition file which describes how the robot can be used
the format of this file can be best explained by example:

project (proj,p)
- list (l)
- delete (del,d)
-- name (n)

this means entity is project
synonym for project is proj & p
cmds on project are list with as synonym l
so !p.l is same as !project.list or !project.l
argument required for delete is name which has alias n
example usage would be

!p.del
n=myname

this would delete project with name myname

can also call as 

!p.del n=myname

"""
        return '%s ' % help
