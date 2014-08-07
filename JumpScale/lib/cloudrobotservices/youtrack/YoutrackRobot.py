from JumpScale import j
import sys

import JumpScale.lib.txtrobot
import copy
import ujson as json

import JumpScale.lib.youtrackclient

initcmds="""
project (proj,p)
- list (l)
- refresh (r)
- new (n)
-- id
-- name
-- description
-- lead

##############################################

user (u)
- list (l)
- refresh (r)
- alias
-- name
-- alias #comma separated when more than 1 alias

- new (n)
-- name
-- fullname
-- email
-- upasswd
-- alias
-- jabber

##############################################

group (g)
- new (n)
-- name
-- role

##############################################

story (issue,bug)
- list (l)
-- project (proj,p) #obliged
-- max #max amount of items
-- start #startpoint e.g. 10 is id
-- filter (f) #is filter like used in youtrack
-- verbose (v) #1-3 3 being most verbose

- assignee
-- name
-- who

- get
-- id
-- name (n)
-- project (p)

- create (c,n,new,update,u)
-- name
-- project
-- who #name of person who will do it
-- prio #0-4,4 being highest, see below
-- descr (description,d)
-- parent #specify part of name or id of task which we are subtask for

- delete (d,del)
-- id
-- name (n)

- comment
-- id
-- name (n) #specify name or part of name
-- comment
-- created
-- author

- depend
-- id
-- name (n) #speciy name or part of name
-- on #depend on 

- subtask
-- id
-- name (n) #speciy name or part of name
-- parent #parent of this task


*****************************************
priorities:
  Show-stopper:4
  Critical:3
  Major:2
  Normal:1
  Minor:0

"""

class YoutrackRobot(object):

    def __init__(self):
        pass

    def getRobot(self,url):
        robot=j.tools.txtrobot.get(initcmds)
        cmds=YouTrackRobotCmds(url)
        robot.addCmdClassObj(cmds)
        return robot


class YouTrackRobotCmds():
    def __init__(self,url):
        self.url=url
        self.clients={}
        self.alwaysdie=False
        self.channel="youtrack"

    def getLoginPasswd(self,args):
        if not args.has_key("login") or not args.has_key("passwd"):
            raise RuntimeError("E:could not find login & passwd info, please specify login=..\npasswd=..\n\n before specifying any cmd")
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

    def _prioNameToId(self,name):
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


    def project__new(self,**args):
        client=self.getClient(args)
        if self.txtrobot.redis.hexists("youtrack:project",args["name"].lower()):
            OUT="**WARNING: Project existed"
            return OUT
        else:
            self.txtrobot.redis.hexists("youtrack:project",args["name"].lower())
            result=client.createProjectDetailed(args["id"], args["name"], args["description"], args["lead"])
            self.project__refresh(**args)


    def group__new(self,**args):
        client=self.getClient(args)

        if not args["name"].lower() in [str(item["name"]).lower() for item in client.getGroups()]:
            client.createGroup(args["name"])
        if args.has_key("role"):
            for role in args["role"].split(","):
                if role.strip()<>"":
                    raise RuntimeError("E:role param not supported yet")
                    roles=[str(item["name"]) for item in client.getRoles() if str(item["name"]).lower()==role.lower().strip()]
                    if len(roles)==1:
                        role=roles[0]
                    else:
                        raise RuntimeError("E:Cannot find role:%s"%role)

                    result=client.addUserRoleToGroup(args["name"],role.strip())
                    
    def user__new(self,**args):
        client=self.getClient(args)
        if args["email"].find(",")<>-1:
            args["email"]=args["email"].split(",")[0].strip()
        
        result= client.createUserDetailed(args["name"],args["fullname"],args["email"],args["jabber"],args["upasswd"])
        if not result[0]["status"]=='200':
            raise RuntimeError("E:Could not create user")

        for gr in args["groups"].split(","):
            if gr.strip()<>"":
                groups=[str(item["name"]) for item in client.getGroups() if str(item["name"]).lower()==gr.lower().strip()]
                if len(groups)==1:
                    gr=groups[0]
                else:
                    raise RuntimeError("E:Cannot find group:%s"%gr)

                result=client.setUserGroup(args["name"],gr)
                if not result["status"]=='200':
                    raise RuntimeError("E:Could not create group:%s"%gr)

        return "OK"


    def user__refresh(self,**args):
        client=self.getClient(args)
        self.txtrobot.redis.delete("youtrack:user")
        for user in client.getUsers():
            user=client.getUser(user.login)
            # print user
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
        from IPython import embed
        print "DEBUG NOW user refresh"
        embed()
        
        return "Refresh OK"

    def user__alias(self,**args):
        for alias in args["alias"].split(","):
            if alias.strip()<>"":
                alias=alias.lower()
                self.txtrobot.redis.hset("youtrack:useralias",alias,args["name"])
        return "OK"

    def _getProject(self,name):
        data=self.txtrobot.redis.hget("youtrack:project",name.lower())
        if data==None:
            return None
        return json.loads(data)

    def _getUser(self,name):
        if self.txtrobot.redis.hexists("youtrack:useralias",name):
            name=self.txtrobot.redis.hget("youtrack:useralias",name)

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
            raise RuntimeError("E:Cannot list stories when project not mentioned")

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
            raise RuntimeError("E:Could not find project:'%s'"%args["project"])

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

    def story__comment(self,**args):
        client=self.getClient(args)
        done=""
        c=args["comment"].replace("\\n","\n")
        for story in self._storiesGet(args):            
            client.executeCommand(story.id,"comment",c)
            done+="%s,"%story.id
        return "COMMENT:%s"%done

    def story__assign(self,**args):
        client=self.getClient(args)
        done=""
        for story in self._storiesGet(args):            
            client.executeCommand(story.id,"assignee",args["who"])
            done+="%s,"%story.id
        return "ASSIGN:%s"%done

    def story__delete(self,**args):
        client=self.getClient(args)
        done=""
        for story in self._storiesGet(args):
            client.deleteIssue(story.id) 
            done+="%s,"%story.id            

        return "DELETED:%s"%done

    def story__depend(self,**args):
        client=self.getClient(args)
        done=""
        for story in self._storiesGet(args):
            #find deps
            args2=copy.copy(args)
            if args2.has_key("id"):
                args2.pop("id")
            args2["name"]=args["on"]
            deps=self._storiesGet(args2)
            for dep in deps:
                client.executeCommand(story.id,"depends on %s"%dep.id)            
                done+="%s,"%story.id            

        return "DEPEND done"

    def story__subtask(self,**args):
        client=self.getClient(args)
        done=""
        for story in self._storiesGet(args):
            #find deps
            args2=copy.copy(args)
            if args2.has_key("id"):
                args2.pop("id")
            args2["name"]=args["parent"]
            parent=self._storiesGet(args2)
            if len(parent)>1:
                raise RuntimeError("E:CANNOT LINK TO MORE THAN 1 PARENT.")
            parent=parent[0]
            client.executeCommand(story.id,"subtask of %s"%parent.id)            
            done+="%s,"%story.id            

        return "DEPEND done"

    def _storiesGet(self,args):
        client=self.getClient(args)

        proj=self._getProject(args["project"])
        if proj==None:
            raise RuntimeError("E:Could not find project:'%s'"%args["project"])

        stories=[]

        if args.has_key("id"):
            if args["id"].find(",")==-1:
                ids=[args["id"]]
            else:
                ids=args["id"].split(",")

            for idd in ids:
                idd=str(idd)
                if idd.find("-")<>-1:
                    idd=args["id"]
                else:
                    idd="%s-%s"%(proj["id"],idd)
                try:
                    story=client.getIssue(idd)
                except Exception,e:
                    if str(e).find("404: Not Found")==-1:
                        raise RuntimeError(str(e))
                    continue
                stories.append(story)
            return stories

        if args.has_key("name"):
            issues=client.getIssues(proj["id"],"summary: \"%s\""%args["name"],0,100)
            return issues

        if args.has_key("filter"):
            issues=client.getIssues(proj["id"],args["filter"],0,100)
            return issues

        return client.getIssues(proj["id"],"",0,100)

    def story__get(self,**args):
        if args.has_key("filter"):
            if args["filter"]=="open":
                args["filter"]="State: -Fixed -{Won't fix} -{Verified}"
        
        client=self.getClient(args)
        out="\n"
        for story in self._storiesGet(args):
            parent=""
            out+="##########################################################################\n"
            out+="!issue.update\n"
            
            links=story.getLinks()
            
            if len(links)>0:
                for link in links:
                    if link.target==story.id:
                        if link.typeName=="Subtask":
                            parent=link.source
                
            prio=self._prioNameToId(story.Priority)
            out+="id=%s\n"%story.id
            out+="name=%s\n"%story.summary
            if story.__dict__.has_key('Assignee'):
                out+="who=%s\n"%story.Assignee
            out+="state=%s\n"%story.State              
            if story.__dict__.has_key('description'):
                out+="descr=...\n%s\n...\n"%story.description.strip()
            out+="prio=%s\n"%prio
            out+="parent=%s\n"%parent
            # out+="created=%s #%s\n"%(story.created,j.base.time.epoch2HRDateTime(story.created))
            out+="\n"
            if int(story.commentsCount)>0:                
                out+="prio=%s\n"%prio
                for comment in story.getComments():
                    out+="!issue.comment\n"
                    out+="id=%s\n"%story.id
                    out+="comment=...\n%s\n...\n"%comment.text.strip()
                    # out+="created=%s #%s\n"%(comment.created,j.base.time.epoch2HRDateTime(comment.created))
                    out+="author=%s\n"%comment.author
                out+="\n"
        return out
        
    def story__create(self,**args):
        client=self.getClient(args)

        if args.has_key("who") and args["who"].find(",")<>-1:
            from IPython import embed
            print "DEBUG NOW id"
            embed()
            first=""
            for who in args["who"].split(","):
                if first=="":
                    first=who
                args2=copy.copy(args)
                args2["who"]=who
                result=self.story__create(**args2)
                from IPython import embed
                print "DEBUG NOW ooo"
                embed()
                

            story__create
        else:
                            
            proj=self._getProject(args["project"])
            if proj==None:
                raise RuntimeError("E:Could not find project:'%s'"%args["project"])

            issues=client.getIssues(proj["id"],"summary: \"%s\""%args["name"],0,100)

            if len(issues)>1:
                raise RuntimeError("E:Found more than 1 story with samen name:%s"%args["name"])
            elif len(issues)==1:
                issue=issues[0]
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
                    raise RuntimeError("E:Could not find user:'%s'"%args["who"])
                who=user["login"]

                if not args.has_key("descr"):
                    args["descr"]= ""

                result=client.updateIssue(issue.id,summary=args["name"],description=args["descr"])

                client.executeCommand(issue.id,"Assignee %s"%args["who"],"") 

            
                # if len(issue.getAttachments())>0:
                #     raise RuntimeError(E:Cannot update the story, there are attachments, not supported")

                # if not args.has_key("prio"):
                #     args["prio"]= self._prioNameToId(issue.Priority)
                # else:
                #     args["prio"]= int(args["prio"])

                # if int(args["prio"])>4:
                #     args["prio"]=4

                # if issue.__dict__.has_key('Fix versions'):
                #     fv=issue.__dict__['Fix versions']
                # else:
                #     fv=[]

                # if not args.has_key("who"):
                #     if issue.__dict__.has_key('Assignee'):
                #         who= issue.Assignee
                #     else:
                #         user=self._getUser(proj["lead"])
                #         if user==None:
                #             raise RuntimeError("E:Could not find user:'%s'"%proj["lead"]
                #         who=user["login"]
                # else:
                #     user=self._getUser(args["who"])
                #     if user==None:
                #         raise RuntimeError("E:Could not find user:'%s'"%args["who"])
                #     who=user["login"]
               
                # if not args.has_key("descr"):
                #     if not issue.__dict__.has_key('description'):
                #         args["descr"]=""
                #     else:
                #         args["descr"]=issue.description                

                # args["descr"]=args["descr"].replace("\\n","\n")

                # data = {'numberInProject':str(int(issue.numberInProject)),
                #             'summary':issue.summary,
                #             'description':args["descr"],
                #             'priority':str(args["prio"]),
                #             'fixedVersion':fv,
                #             'type':issue.Type,
                #             'state':issue.State,
                #             'created':str(issue.created),
                #             'reporterName': issue.reporterName,
                #             'assigneeName':who}


                # links=issue.getLinks()
                # comments=issue.getComments()

                # client.deleteIssue(issue.id)

                # result =client.importIssues(proj["id"],"Developers",[data])
                # client.importLinks(links)

                # for comment in comments:
                #     client.executeCommand(issue.id,"comment",comment.text)

                idd=issue.id

                msg="Issue updated with id:%s"%idd

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
                    raise RuntimeError("E:Could not find user:'%s'"%args["who"])
                who=user["login"]

                if not args.has_key("descr"):
                    args["descr"]= ""
                
                result=client.createIssue(project=args["project"],assignee=who,summary=args["name"],description=args["descr"],priority=args["prio"])

                idd=result.split("/")[-1]

                if args.has_key("comment"):            
                    client.executeCommand(idd,"comment", args["comment"])

                msg="Issue created with id:'%s'"%idd

            if args.has_key("parent"):     
                from IPython import embed
                print "DEBUG NOW parent"
                embed()
                          
                args2=copy.copy(args)
                if args2.has_key("id"):
                    args2.pop("id")
                args2["name"]=args["parent"]            
                parent=self._storiesGet(args2)
                if len(parent)>1:
                    return "**ERROR**: CANNOT LINK TO MORE THAN 1 PARENT."
                parent=parent[0]
                client.executeCommand(idd,"subtask of %s"%parent.id)            

        return msg

