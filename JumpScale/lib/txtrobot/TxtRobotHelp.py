from JumpScale import j

class TxtRobotHelp(object):       

    def intro(self):
        help="""
get detailed help by using one of following commands<br/>

#explain how to use the robot<br/>
help<br/>
<br/>
#show help how commands are defined <br/>
!help.definition<br/>
<br/>
#explain the available cmds in this robot<br/>
!help.cmds<br/>
<br/>
"""
        return '%s <br/><br/>' % help


    def help(self):
        help="""
The format of each message is:<br/>
'<br/>
login=mylogin<br/>
passwd=mypasswd<br/>
<br/>
!entity.cmd<br/>
anotherparam=val<br/>
'<br/>
<br/>
entity is something line project, user, invoice, machine...<br/>
<br/>
#everything starting with ! is a cmdline<br/>
#the lines after the cmdline are all the arguments<br/>
<br/>
##example:<br/>
!project.list<br/>
<br/>
!issue.create<br/>
name=aname<br/>
descr=descr of issue<br/>
deadline=6d<br/>
<br/>
#everything before the first ! are considered to be global params e.g. login, passwd, url, ...<br/>
<br/>
available commands can be asked for by sending command:  !help.cmds<br/>
<br/>
variables can be multiline by using special instruction ...<br/>
description=...<br/>
this is multiline<br/>
text<br/>
.<br/>
name=aname<br/>
<br/>
the multiline stops when . or # or ! found<br/>
<br/>
<br/>
<br/>
<br/>
"""
        return '%s <br/><br/>' % help

    def help_definition(self):
        help="""
each robot has a definition file which describes how the robot can be used<br/>
the format of this file can be best explained by example:<br/>
<br/>
project (proj,p)<br/>
- list (l)<br/>
- delete (del,d)<br/>
-- name (n)<br/>
<br/>
this means entity is project<br/>
synonym for project is proj & p<br/>
cmds on project are list with as synonym l<br/>
so !p.l is same as !project.list or !project.l<br/>
argument required for delete is name which has alias n<br/>
example usage would be<br/>
<br/>
!p.del<br/>
n=myname<br/>
<br/>
this would delete project with name myname<br/>
<br/>
can also call as <br/>
<br/>
!p.del n=myname<br/>
<br/>
"""
        return '%s <br/><br/>' % help
