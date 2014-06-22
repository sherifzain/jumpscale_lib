from JumpScale import j
import sys
sys.path.append("%s/lib/youtrackclient/"%j.dirs.jsLibDir)
from youtrack.connection import Connection
import JumpScale.baselib.txtrobot
import copy
import ujson as json

initcmds="""
project (proj,p)
- list (l)
- refresh (r)

user (u)
- list (l)
- refresh (r)

story (issue,bug)
- list (l)
-- project (proj,p) #obliged
-- max #max amount of items
-- start #startpoint e.g. 10 is id
-- filter (f) #is filter like used in youtrack
-- verbose (v) #1-3 3 being most verbose

- create (c,n,new,update,u)
-- name
-- project
-- who #name of person who will do it
-- prio #0-4,4 being highest, see below
-- descr (description,d)

- delete (d,del)
-- id

- comment
-- id
-- name #specify name or id
-- comment

#####
priorities:
  Show-stopper:4
  Critical:3
  Major:2
  Normal:1
  Minor:0

"""

class YoutrackFactory(object):

    def __init__(self):
        pass
        
    def get(self, url, login,password):
        return Connection(url,login,password)


    def getRobot(self,url):
        robot=j.tools.txtrobot.get(initcmds)
        cmds=YouTrackRobotCmds(url)
        robot.addCmdClassObj(cmds)
        return robot


class YouTrackRobotCmds():
    def __init__(self,url):
        self.url=url
        self.clients={}

    def getLoginPasswd(self,args):
        if not args.has_key("login") or not args.has_key("passwd"):
            self.txtrobot.error("could not find login & passwd info, please specify login=..\npasswd=..\n\n before specifying any cmd")
        return args["login"],args["passwd"]

    def getClient(self,args):
        login,passwd=self.getLoginPasswd(args)
        
        key="%s_%s"%(login,passwd)
        if not self.clients.has_key(key):
            self.clients[key]=j.tools.youtrack.get(self.url,login,passwd)
        return self.clients[key]

    def _toJson(self,obj):
        dd=copy.copy(obj.__dict__)
        dd.pop("youtrack")
        return json.dumps(dd)        

    def _projNameToId(self,name):
        mmap={"show-stopper":4,"critical":3,"major":2,"normal":1,"minor":0}
        return mmap[name.lower()]


    def project__refresh(self,**args):
        client=self.getClient(args)
        self.txtrobot.redis.delete("youtrack:project")
        for key,pname in client.getProjects().iteritems():
            proj=client.getProject(key)
            data=self._toJson(proj)
            self.txtrobot.redis.hset("youtrack:project",key.lower(),data)
            self.txtrobot.redis.hset("youtrack:project",pname.lower(),data)
        return "Refresh OK"

    def user__refresh(self,**args):
        client=self.getClient(args)
        self.txtrobot.redis.delete("youtrack:user")
        for user in client.getUsers():
            user=client.getUser(user.login)
            print user
            user2={}
            user2["name"]=user.fullName
            user2["login"]=user.login
            if user.__dict__.has_key("email"):
                user2["email"]=user.email
            else:
                user2["email"]=""
            data=json.dumps(user2)
            self.txtrobot.redis.hset("youtrack:user",user2["login"].lower(),data)
            self.txtrobot.redis.hset("youtrack:user",user2["name"].lower(),data)
        return "Refresh OK"

    def _getProject(self,name):
        data=self.txtrobot.redis.hget("youtrack:project",name.lower())
        if data==None:
            return None
        return json.loads(data)

    def _getUser(self,name):
        data=self.txtrobot.redis.hget("youtrack:user",name.lower())
        if data==None:
            return None
        return json.loads(data)

    def project__list(self,**args):        
        client=self.getClient(args)
        return client.getProjectIds()

    def story__list(self,**args):
        client=self.getClient(args)

        if not args.has_key("project"):
            return self.error("Cannot list stories when project not mentioned")

        if args.has_key("state"):
            if args["state"]=="open":
                filt="state:-Fixed,-Verified,-{Won't fix},-Obsolete"
            elif args["state"]=="fixed":
                filt="state:-Fixed"
            else:
                filt=""

        if args.has_key("filter"):
            filt=args["filter"]

        if args.has_key("verbose"):
            verbose=int(args["verbose"])
            if verbose>3:
                verbose=3
        else:
            verbose=1

        if not args.has_key("max"):
            args["max"]=200
        if not args.has_key("start"):
            args["start"]=0

        proj=self._getProject(args["project"])
        if proj==None:
            return "Could not find project:'%s'"%args["project"]

        issues=client.getIssues(proj["id"],filt,args["start"],args["max"])

        result=[]
        if verbose>1:
            
            for issue in issues:
                row={}
                row["id"]=issue.id
                row["summary"]=issue.summary
                row["state"]=issue.State
                row["priority"]=issue.Priority
                if issue.hasAssignee():
                    row["assignee"]=issue.Assignee            
                if issue.links<>None:
                    row["links"]=issue.links
                result.append(row) 
        else:
            out=""
            for issue in issues:
                if issue.__dict__.has_key('Fix versions'):
                    fv=issue.__dict__['Fix versions']
                    if not j.basetype.string.check(fv):
                        fv=",".join(fv)
                else:
                    fv=""
                
                out+="%-7s %-15s %-10s %s\n"%(issue.id,issue.State,fv,issue.summary)
            result=out

        return result

    def story_comment(self,**args):
        client=self.getClient(args)
        client.executeCommand(args["id"],"comment",args["comment"])

    def story__create(self,**args):
        client=self.getClient(args)
        
        proj=self._getProject(args["project"])
        if proj==None:
            return "Could not find project:'%s'"%args["project"]

        self.story__list(filter="summary: atest",**args)

        issues=client.getIssues(proj["id"],"summary: %s"%args["name"],0,100)
        
        if len(issues)>1:
            return self.txtrobot.error("Found more than 1 story with samen name:%s"%args["name"])
        elif len(issues)==1:
            issue=issues[0]

            if len(issue.getAttachments())>0:
                return self.txtrobot.error("Cannot update the story, there are attachments, not supported")

            if not args.has_key("prio"):
                args["prio"]= self._projNameToId(issue.Priority)
            else:
                args["prio"]= int(args["prio"])

            if int(args["prio"])>4:
                args["prio"]=4

            if issue.__dict__.has_key('Fix versions'):
                fv=issue.__dict__['Fix versions']
            else:
                fv=[]

            if not args.has_key("who"):
                if issue.__dict__.has_key('Assignee'):
                    who= issue.Assignee
                else:
                    user=self._getUser(proj["lead"])
                    if user==None:
                        return "Could not find user:'%s'"%proj["lead"]
                    who=user["login"]
            else:
                user=self._getUser(args["who"])
                if user==None:
                    return self.txtrobot.error("Could not find user:'%s'"%args["who"])
                who=user["login"]
           
            if not args.has_key("descr"):
                if not issue.__dict__.has_key('description'):
                    args["descr"]=""
                else:
                    args["descr"]=issue.description                

            args["descr"]=args["descr"].replace("\\n","\n")

            data = {'numberInProject':str(int(issue.numberInProject)),
                        'summary':issue.summary,
                        'description':args["descr"],
                        'priority':str(args["prio"]),
                        'fixedVersion':fv,
                        'type':issue.Type,
                        'state':issue.State,
                        'created':str(issue.created),
                        'reporterName': issue.reporterName,
                        'assigneeName':who}


            links=issue.getLinks()
            comments=issue.getComments()

            client.deleteIssue(issue.id)

            result =client.importIssues("OPS","Developers",[data])
            client.importLinks(links)

            for comment in comments:
                client.executeCommand(issue.id,"comment",comment.text)

        else:
            if not args.has_key("prio"):
                args["prio"]= 1
            else:
                args["prio"]= int(args["prio"])

            if int(args["prio"])>4:
                args["prio"]=4

            if not args.has_key("who"):
                args["who"]= proj["lead"]
            user=self._getUser(args["who"])
            if user==None:
                return "Could not find user:'%s'"%args["who"]
            who=user["login"]

            if not args.has_key("descr"):
                args["descr"]= ""
            
            result=client.createIssue(project=args["project"],assignee=who,summary=args["name"],description=args["descr"],priority=args["prio"])

        return result        

# class YoutrackConnection(object):

#     def __init__(self, url, login,password):
#         """
#         @param url example http://incubaid.myjetbrains.com/youtrack/
#         """
#         yt = 
#         from IPython import embed
#         print "DEBUG NOW opopopo"
#         embed()
        
#         # print yt.createIssue('SB', 'resttest', 'test', 'test', '1', 'Bug', 'Unknown', 'Open', '', '', '')

