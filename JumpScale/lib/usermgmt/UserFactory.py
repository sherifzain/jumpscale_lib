from JumpScale import j
import JumpScale.lib.txtrobot
import ujson as json

import JumpScale.baselib.mailclient

robotdefinition="""


####
global required variables
login=
passwd=

user (u)
- list (l)
-- company #optional
- new (n)
-- firstname
-- lastname
-- ulogin       #7 last letters of lastname, first letter of firstname (if not give then calculated)
-- upasswd
-- company      #comma separated 
-- email        #comma separated list (most relevant email first)
-- alias        #comma separated
-- jabber       #is e.g. main gmail email name 
-- mobile       #comma separated
-- skype
-- role         #ceo,developer,teamlead,sales,syseng,supportl1,supportl2,supportl3,admin,legal,finance (mark all)
-- bitbucketlogin   #login on bitbucket
-- linkedin         #id on linkedin
-- dsakey           #key for sshaccess (pub)
-- gmail        #main gmail account, if not filled in will take first email add
- get (g)
-- ulogin
- passwd
-- ulogin
-- upassd
- check (c)

"""
import JumpScale.portal

class UserFactory(object):

    def getRobot(self):
        robot = j.tools.txtrobot.get(robotdefinition)
        cmds = UserCmds()
        robot.addCmdClassObj(cmds)
        return robot

class UserCmds():
    def __init__(self):
        self.path="/opt/code/incubaid/default__identities/identities/"
        

    def findUser(self,login,failIfNotExist=True):
        login=login.lower()
        for path in j.system.fs.listFilesInDir(self.path, recursive=True, filter="*.hrd"):
            hrd=j.core.hrd.getHRD(path)
            login2=hrd.get("id.login").strip().lower()
            if login2==login:
                return hrd
        if failIfNotExist:
            raise RuntimeError("E:Could not find user:%s"%login)
        else:
            return None

    def user__new(self, **args):
        if not args.has_key("ulogin"):
            raise RuntimeError("E:specify ulogin (7 letters last name, first letter first name)")
        user=self.findUser(args["ulogin"],False)
        if user==None:
            #newuser
            C="""
id.firstname=
id.lastname=
id.login=$login
id.alias=
id.company=$company
#ceo,developer,teamlead,sales,syseng,supportl1,supportl2,supportl3,admin,legal,finance
id.role=
id.email=
id.mobile=
id.skype=
id.bitbucket.login=
id.linkedin=
id.jabber=
id.key.dsa.pub=

"""         
            if not args.has_key("company"):
                raise RuntimeError("E:specify company (can be more than 1, comma separated, first one is primary.)")

            C=C.replace("$company",args["company"])
            C=C.replace("$login",args["ulogin"])

            comp=args["company"].split(",")[0]
            pathdir=j.system.fs.joinPaths(self.path,comp,args["ulogin"])
            j.system.fs.createDir(pathdir)
            j.system.fs.writeFile("%s/id.hrd"%(pathdir),C)
            user=self.findUser(args["ulogin"])


        def do(argname,hrdname,user,args,extracheck=None,help="",die=True):
            if args.has_key(argname) and not args[argname].strip()=="":
                val=args[argname]
                if extracheck<>None:
                    res=extracheck(val)
                    if res<>"":
                        raise RuntimeError("E:Could not validate:%s, %s"%(argname,res))
                user.set(hrdname,val)
            res=user.get(hrdname,default="")
            if res=="":
                if die==False:
                    return 
                if help=="":
                    raise RuntimeError("E:Need argument with name %s"%argname)
                else:
                    raise RuntimeError("E:Need argument with name %s\n%s"%(argname,help))
            return res 
                
        res=do("firstname","id.firstname",user,args,die=False)
        if res==None:
            if user.get("id.name",default="")<>"":
                user.set("id.firstname",user.get("id.name").split(" ")[0])

            
        res=do("lastname","id.lastname",user,args,die=False)
        if res==None:
            if user.get("id.name",default="")<>"":
                name=" ".join(user.get("id.name").split(" ",1)[1:])
                user.set("id.lastname",name)

        user.delete("id.name")

        res=do("bitbucketlogin","id.bitbucket.login",user,args,die=False)
        res=do("alias","id.alias",user,args,die=False)
        res=do("company","id.company",user,args,die=False)
        res=do("email","id.email",user,args,die=False)
        res=do("mobile","id.mobile",user,args,die=False)
        res=do("skype","id.skype",user,args,die=False)
        res=do("linkedin","id.linkedin",user,args,die=False)
        res=do("jabber","id.jabber",user,args,die=False)
        res=do("upasswd","id.passwd",user,args,die=False)
        res=do("gmail","id.gmail",user,args,die=False)
        res=do("dsakey","id.key.dsa.pub",user,args,die=False)

        for check in ["id.alias","id.company","id.email","id.mobile","id.skype","id.bitbucket.login","id.linkedin"\
                ,"id.jabber","id.key.dsa.pub","id.firstname","id.lastname","id.gmail","id.upasswd"]:
            if not user.exists(check):
                user.set(check,"")
    
        return 'User created successfully.'

    def user__list(self, **args):
        result={}
        for path in j.system.fs.listFilesInDir(self.path, recursive=True, filter="*.hrd"):
            hrd=j.core.hrd.getHRD(path)
            if args.has_key("company"):
                companies=[item.lower().strip() for item in hrd.get("id.company").split(",") if item.strip()<>""]
                if args.has_key("ulogin"):
                    if hrd.get("id.login")==args["ulogin"] and args["company"].lower() in companies:
                        result[hrd.get("id.login")]=hrd
                else:
                    if args["company"].lower() in companies:
                        result[hrd.get("id.login")]=hrd
            elif args.has_key("ulogin"):
                if hrd.get("id.login")==args["ulogin"]:
                    result[hrd.get("id.login")]=hrd
            else:   
                result[hrd.get("id.login")]=hrd
        keys=result.keys()
        keys.sort()
        out=""
        for key in keys:
            hrd=result[key]
            out+="!user.new\n"
            out+="ulogin=%s\n"%hrd.get("id.login")
            #out+="upasswd=%s\n"%hrd.get("id.passwd")
            out+="firstname=%s\n"%hrd.get("id.firstname")
            out+="lastname=%s\n"%hrd.get("id.lastname")
            out+="alias=%s\n"%hrd.get("id.alias")
            out+="bitbucketlogin=%s\n"%hrd.get("id.bitbucket.login")
            out+="company=%s\n"%hrd.get("id.company")
            out+="email=%s\n"%hrd.get("id.email")
            out+="mobile=%s\n"%hrd.get("id.mobile")
            out+="skype=%s\n"%hrd.get("id.skype")
            out+="linkedin=%s\n"%hrd.get("id.linkedin")
            out+="jabber=%s\n"%hrd.get("id.jabber")
            out+="gmail=%s\n"%hrd.get("id.gmail")
            out+="dsakey=...\n%s\n...\n"%hrd.get("id.key.dsa.pub")
            if len(keys)>1:
                out+="\n########################################################\n"
        return out
            

    def user__get(self, **args):    
        self.findUser(args["ulogin"]) 
        out=self.user__list(**args)
        out2=""
        for line in out.split("\n"):
            line=line.lstrip("< ")
            out2+="%s\n"%line
        return out2

    def user__check(self,**args):
        for path in j.system.fs.listFilesInDir(self.path, recursive=True, filter="*.hrd"):
            hrd=j.core.hrd.getHRD(path)
            login=hrd.get("id.login").strip().lower()
            self.user__new(ulogin=login)

            hrd=j.core.hrd.getHRD(path)

            ok=True
            for check in ["id.alias","id.company","id.email","id.mobile","id.skype","id.bitbucket.login","id.linkedin",\
                "id.jabber","id.key.dsa.pub","id.firstname","id.lastname","id.gmail","id.upasswd"]:
                if not hrd.get(check)=="":
                    ok=False

            if ok==False:
                recipients=["kristof@incubaid.com"]
                sender="user@robot.vscalers.com"
                subject="error in data of your user account, please fix."
                message=self.user__get(ulogin=login)
                j.clients.email.send(recipients, sender, subject, message, files=None)
                from IPython import embed
                print "DEBUG NOW uuu"
                embed()
                p
                




