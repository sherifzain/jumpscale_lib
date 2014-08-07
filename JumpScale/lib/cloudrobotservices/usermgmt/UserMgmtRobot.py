from JumpScale import j
import JumpScale.lib.txtrobot
import ujson as json
import JumpScale.lib.cloudrobots
import JumpScale.baselib.mailclient

robotdefinition="""

user (u,users)
- list (l)
-- company #optional

- export (e)
-- company #optional

- new (n)
-- firstname
-- lastname
-- ulogin           #7 last letters of lastname, first letter of firstname (if not give then calculated)
-- upasswd
-- company          #comma separated 
-- email            #comma separated list (most relevant email first)
-- alias            #comma separated
-- jabber           #is e.g. main gmail email name 
-- mobile           #comma separated
-- skype
-- role             #ceo,developer,teamlead,sales,syseng,supportl1,supportl2,supportl3,admin,legal,finance (mark all)
-- bitbucketlogin   #login on bitbucket
-- linkedin         #id on linkedin
-- dsakey           #key for sshaccess (pub)
-- gmail            #main gmail account, if not filled in will take first email add
-- dropbox

- get (g)
-- ulogin

- passwd
-- ulogin
-- upassd

- check (c)

oss
- sync
-- company #optional

"""
import JumpScale.portal

class UserMgmtRobot(object):

    def getRobot(self):
        robot = j.tools.txtrobot.get(robotdefinition)
        cmds = UserCmds()
        robot.addCmdClassObj(cmds)
        return robot

class UserCmds():
    def __init__(self):
        self.alwaysdie=False
        self.path="/opt/code/incubaid/default__identities/identities/"
        self.aliasses={}
        self.aliasses["alias"]="id.alias"
        self.aliasses["company"]="id.company"
        self.aliasses["email"]="id.email"
        self.aliasses["mobile"]="id.mobile"
        self.aliasses["skype"]="id.skype"
        self.aliasses["bitbucket"]="id.bitbucket.login"
        self.aliasses["linkedin"]="id.linkedin"
        self.aliasses["jabber"]="id.jabber"
        self.aliasses["dsakey"]="id.key.dsa.pub"
        self.aliasses["firstname"]="id.firstname"
        self.aliasses["lastname"]="id.lastname"
        self.aliasses["gmail"]="id.gmail"
        self.aliasses["upasswd"]="id.passwd"
        self.aliasses["ulogin"]="id.login"
        self.aliasses["dropbox"]="id.dropbox"
        self.aliassesR={}
        for key,val in self.aliasses.iteritems():
            self.aliassesR[val]=key
        self.osis = j.core.osis.getClient(user='root')
        self.osis_system_user=j.core.osis.getClientForCategory(self.osis, 'system', 'user')    
        self.osis_oss_user=j.core.osis.getClientForCategory(self.osis, 'oss', 'user')
        self.channel="user"
        self.redis=j.clients.redis.getRedisClient("127.0.0.1", 7768)
        

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
id.dropbox=
id.gmail=
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


        def do(argname,hrdname,user,args,extracheck=None,help="",die=True,lower=False):
            if args.has_key(argname) and not args[argname].strip()=="":
                val=args[argname]
                if extracheck<>None:
                    res=extracheck(val)
                    if res<>"":
                        raise RuntimeError("E:Could not validate:%s, %s"%(argname,res))
                if lower:
                    val=val.lower().strip()
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
        res=do("alias","id.alias",user,args,die=False,lower=True)
        res=do("company","id.company",user,args,die=False,lower=True)
        res=do("email","id.email",user,args,die=False,lower=True)
        res=do("mobile","id.mobile",user,args,die=False)
        res=do("skype","id.skype",user,args,die=False)
        res=do("linkedin","id.linkedin",user,args,die=False,lower=True)
        res=do("jabber","id.jabber",user,args,die=False)
        res=do("upasswd","id.passwd",user,args,die=False)
        res=do("gmail","id.gmail",user,args,die=False,lower=True)
        res=do("dropbox","id.dropbox",user,args,die=False)
        res=do("dsakey","id.key.dsa.pub",user,args,die=False)

        if args.has_key("checkonly"):
            return

        for check in ["id.alias","id.company","id.email","id.mobile","id.skype","id.bitbucket.login","id.linkedin"\
                ,"id.jabber","id.key.dsa.pub","id.firstname","id.lastname","id.gmail","id.passwd","id.dropbox"]:
            if not user.exists(check):
                user.set(check,"")

        if user.exists("id.upasswd"):
            user.delete("id.upasswd")

        userEmail,missing,msg=self.checkUser(user,send2user=False)
        if userEmail<>"":
            raise RuntimeError("F:\n%s\n"%(msg))
        else:
            return 'User created successfully.'

    def users_get(self,**args):
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
        return result

    def hrd_out(self,hrd,out=""):
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
        out+="dropbox=%s\n"%hrd.get("id.dropbox")
        return out

    def user__export(self, firstonly=False,**args):

        out=""
        result=self.users_get(**args)
        companies=[]
        keys=result.keys()
        for key in keys:        
            hrd=result[key]                        
            for company in [item.lower() for item in hrd.get("id.company").split(",") if item.strip()<>""]:
                if company not in companies:
                    companies.append(company)

        for company in companies:
            args["company"]=company
            result=self.users_get(**args)
            keys=result.keys()
            keys.sort()
            for key in keys:        
                hrd=result[key]   
                out=self.hrd_out(hrd,out)
                # out+="dsakey=...\n%s\n...\n"%hrd.get("id.key.dsa.pub")                
                out+="-------\n\n"
        
            if len(keys)>1:
                out+="\n########################################################\n"
        return out

    def oss__sync(self, **args):
        cl=self.osis_system_user
        out=""
        result=self.users_get(**args)
        companies=[]
        keys=result.keys()
        out=""
        for key in keys:        
            if args.has_key("company"):
                if args["company"].lower().strip()<>company.lower().strip():
                    continue
            hrd=result[key] 
            login=hrd.get("id.login")

            comps= hrd.getList("id.company")
            if "jumpscale" in comps or "mothership1" in comps or "codescalers" in comps or "incubaid" in comps:              
                res=cl.simpleSearch({"id":login})
                if len(res)>0:
                    guid=res[0]["guid"]
                    user=cl.get(guid)
                else:
                    user=cl.new()
                    user.id=login

                user.emails=hrd.getList("id.email")
                user.groups=["admin"]

                if hrd.get("id.passwd")=="":
                    passwd=chr(j.base.idgenerator.generateRandomInt(97,123))+chr(j.base.idgenerator.generateRandomInt(97,123))+str(j.base.idgenerator.generateRandomInt(100,999))
                    hrd.set("id.passwd",passwd)
                    user.passwd
                else:
                    user.passwd=hrd.get("id.passwd")

                #out+="%s\n"%user.guid
                #@todo temp
                out+="%s %s\n"%(user.guid,user.passwd)

                cl.set(user)

                pubkey=hrd.get("id_key_dsa_pub")

                userd=user.__dict__
                if userd.has_key('_ckey'):
                    userd.pop('_ckey')
                if userd.has_key('_meta'):
                    userd.pop('_meta')

                userd["sshpubkey"]=hrd.get("id_key_dsa_pub",default="")
                
                self.redis.hset("users",login,json.dumps(userd))
            
        return out
            
    def users_getalias(self,**args):
        result2={}
        result=self.users_get(**args)
        keys=result.keys()
        keys.sort()
        for key in keys:
            hrd=result[key]
            result2[key.lower()]=[item.lower() for item in hrd.get("id.alias").split(",") if item.strip()<>""]
        return result2


    def user__list(self,**args):
        
        out=""
        result=self.users_get(**args)
        companies=[]
        keys=result.keys()
        for key in keys:        
            hrd=result[key]                        
            for company in [item.lower() for item in hrd.get("id.company").split(",") if item.strip()<>""]:
                if company not in companies:
                    companies.append(company)

        for company in companies:
            args["company"]=company
            result=self.users_get(**args)
            out+="\n**%s**\n"%company
            keys=result.keys()
            keys.sort()
            for key in keys:        
                hrd=result[key]   
                if key<>"system":         
                    out+="%s :%s %s (%s)\n"%(key,hrd.get("id.firstname"),hrd.get("id.lastname"),hrd.get("id.alias"))
        
        return out


    def user__get(self, **args):    
        hrd=self.findUser(args["ulogin"]) 
        out=self.hrd_out(hrd)
        return out
        # out2=""
        # for line in out.split("\n"):
        #     line=line.lstrip("< ")
        #     out2+="%s\n"%line
        # return out2

    def user__check(self,**args):
        out3=""
        for path in j.system.fs.listFilesInDir(self.path, recursive=True, filter="*.hrd"):
            hrd=j.core.hrd.getHRD(path)
            login=hrd.get("id.login").strip().lower()
            self.user__new(ulogin=login,checkonly=True)
            hrd=j.core.hrd.getHRD(path)
            if args.has_key("msg"):
                msg=args["msg"]
            else:
                msg=""
            userEmail,missing,msg2=self.checkUser(hrd,msg=msg)
            if userEmail<>"":
                out3+="ERROR: '%s' %s\n"%(userEmail,missing)

        if out3<>"":
            return out3

        return "OK"

    def checkUser(self,userhrd,msg="",send2user=True,**args):

        missing=""
        for check in ["id.alias","id.company","id.email","id.mobile","id.skype",\
            "id.firstname","id.lastname","id.gmail"]:
            if userhrd.get(check,default="")=="":
                check2=self.aliassesR[check]
                missing+="%s,"%check2

        missing=missing.strip(",")

        if missing<>"":
            # recipients=["kristof@incubaid.com"]
            recipients=[userhrd.get("id.email").split(",")[0]]
            recipients=[recipients[0]]

            login=userhrd.get("id.login").strip().lower()
            
            sender="user@robot.vscalers.com"
            subject="error in data of your user account, please fix."
            message=self.user__get(ulogin=login)
            
            message=j.tools.text.prefix(":*: ",message)

            HELP="""
*****************
HELP
*****************
Please complete the form above.
Missing arguments are: $missing

id.firstname=
id.lastname=
id.login=   #YOUR OFFICIAL LOGIN and will already be filled in (is 7 letters last name, first letter firstname)
id.alias=   #what are other names which can be used in e.g. tickets for you? your aliases, need to be unique over company.
id.company= #mark all relevant companies (comma separated) e.g. mothership1,codescalers  
id.role=    # shose one or more of: ceo,developer,teamlead,sales,syseng,supportl1,supportl2,supportl3,admin,legal,finance
id.email=   #mark ALL YOUR EMAILS (comma separated), your primary one first
id.mobile=  #mark all, again comma separated
id.skype=
id.bitbucket.login=     #if you have
id.linkedin=            #if you have
id.gmail=               #your main gmail account which should be used to communicate when using google drive
id.jabber=              #this is normally same as your gmail acount
id.dropbox=             #your dropbox account (if you have)

the robot will keep on complaining untill all required fields are filled in.
Please try to be as complete as possible

just reply on this email and complete the fields starting with :#: with missing info
the robot will do the rest (means will populate the user db for you)
you will get an email wich confirms your input.

"""
            HELP=HELP.replace("$missing",missing)
            message="%s\n\n%s\n"%(message,HELP)
            
            if send2user:                
                if message.strip()<>"" and msg<>"":
                    message="%s\n\n%s"%(msg,message)

                try:
                    j.clients.email.send(recipients, sender, subject, message, files=None)
                except Exception,e:             
                    if str(e).find("Bad recipient")<>-1:       
                        missing="EMAIL ADDRESS NOT PROPERLY FILLED IN: was:'%s'"%recipients[0]
                        recipients[0]=login
                    else:
                        raise RuntimeError("E:error in sending mail:%s"%e)

            return recipients[0],missing,message
        return "","",""

            
            




