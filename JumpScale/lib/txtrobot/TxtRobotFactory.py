from JumpScale import j
import yaml
import JumpScale.baselib.hash
from TxtRobotHelp import TxtRobotHelp

import JumpScale.baselib.redis
import copy

class TxtRobotFactory(object):

    def __init__(self):
        pass
        
    def get(self, definition):
        """
        example definition:
        
        project (proj,p)
        - list (l)
        - delete (del,d)
        -- name (n)
        user (u)
        - list (l)
        """
        return TxtRobot(definition)

class TxtRobot():
    def __init__(self,definition):
        self.definition=definition.replace('\n', '<br/>')
        self.cmdAlias={}
        self.entityAlias={}
        self.entities=[]
        self.cmds={}
        self._initCmds(definition)
        self.cmdsToImpl={}
        self.help=TxtRobotHelp()
        # self.snippet = TxtRobotSnippet()
        self.cmdobj=None
        self.redis=j.clients.redis.getRedisClient("localhost",7768)
        self.codeblocks={}
        alias={}
        alias["l"]="login"
        alias["p"]="passwd"
        alias["pwd"]="passwd"
        alias["password"]="passwd"
        self.argsAlias=alias

    def _initCmds(self,definition):

        for line in definition.split("\n"):
            # print line
            line=line.strip()
            if line=="":
                continue
            if line[0]=="#":
                continue

            if line.find("###")<>-1:
                break

            if line[0]<>"-":
                if line.find(" ")<>-1:
                    ent,remainder=line.split(" ",1)
                else:
                    ent=line
                    remainder=""
                ent=ent.lower().strip()
                self.entities.append(ent)
                if remainder.find("(")<>-1 and remainder.find(")")<>-1:
                    r=remainder.strip("(")
                    r=r.strip(")")
                    r=r.strip()
                    for alias in r.split(","):
                        alias=alias.lower().strip()
                        self.entityAlias[alias]=ent

            if line[0]=="-" and line[1]<>"-":
                if ent=="":
                    raise RuntimeError("entity cannot be '', line:%s"%line)
                line=line.strip("-")
                line=line.strip()
                if line.find(" ")==-1:
                    cmd=line
                    remainder=""
                else:
                    cmd,remainder=line.split(" ",1)
                cmd=cmd.lower().strip()
                if not self.cmds.has_key(ent):
                    self.cmds[ent]=[]
                if not self.cmdAlias.has_key(ent):
                    self.cmdAlias[ent]={}
                if cmd not in self.cmds[ent]:
                    self.cmds[ent].append(cmd)

                if remainder.find("(")<>-1 and remainder.find(")")<>-1:
                    r=remainder.strip("(")
                    r=r.strip(")")
                    r=r.strip()
                    for alias in r.split(","):
                        alias=alias.lower().strip()
                        self.cmdAlias[ent][alias]=cmd                

    def _processGlobalArg(self,args,line):
        res={}
        out=""
        alias=self.argsAlias
        name,data=line.split("=",1)
        name=name.lower().strip("@")
        if alias.has_key(name):
            name=alias[name]
        args[name]=data.strip().replace("\\n","\n")
        return args

    def _longTextTo1Line(self,txt):
        txt=txt.rstrip("\n")
        state="start"
        out=""
        lt=""
        ltstart=""
        for line in txt.split("\n"):
            line=line.strip()
            if state=="LT":
                if len(line)>0 and line.find("...")==0:
                    #means we reached end of block
                    state="start"
                    out+="%s%s\n"%(ltstart,lt)
                    ltstart=""
                    lt=""
                    continue
                else:
                    lt+="%s\\n"%line
                    continue      
            if len(line)>0 and line[0]=="#":
                continue      
            if state=="start" and line.find("=")<>-1:
                before,after=line.split("=",1)                
                if after.strip()[0:3]=="...":
                    state="LT"
                    ltstart="%s="%before
                    continue

            out+="%s\n"%line
            
        return out

    def _findCodeBlocks(self,txt):
        cbname=""
        out=""
        cb=""
        txt=txt.rstrip("\n")
        for line in txt.split("\n"):
            line2=line.lower()
            if line2.find("@end")==0:
                if cbname=="MAIN":
                    #means we will only deal with main block, all the rest is irrelevant
                    return cb
                cb=cb.strip()
                self.codeblocks[cbname.lower()]=cb
                #do not put codeblock in out

                cb=""
                cbname=""
                continue

            if cbname<>"":
                #we are in block so remember
                cb+="%s\n"%line
                continue

            if line2.find("@start")==0:
                cbname=line2.split("@start")[1].strip()
                if cbname=="":
                    #do not remember prev lines because found main block
                    out=""
                    cbname="MAIN"
                continue
            out+="%s\n"%line
        return out

    def response(self,cblock,result):
        if cblock<>"":
            out=j.tools.text.prefix("< ",cblock)
        else:
            out=""
        if out[-1]<>"\n":
            out+="\n"
        if result<>"":
            out+=j.tools.text.prefix("> ",result)
        if out[-1]<>"\n":
            out+="\n"
        return out

    def responseError(self,cblock,result):
        out=cblock
        if out[-1]<>"\n":
            out+="\n"        
        if result<>"":
            out+=j.tools.text.prefix(">ERROR: ",result)
        if out[-1]<>"\n":
            out+="\n"            
        return out

    def _processSnippets(self,txt):
        out=""
        txt=txt.rstrip("\n")
        for line in txt.split("\n"):
            if line.find("!snippet.get")==0:
                remainder=line.split("!snippet.get",1)[1]
                md5=remainder.strip()
                snippet = self.redis.hget("robot:snippets", md5)
                if snippet==None:
                    out+=self.responseError(line,"Could not find snippet with key:%s"%md5)
                else:
                    out+="%s\n"%snippet
                continue
            out+="%s\n"%line
        return out

    def _snippetCreate(self,name):
        name=name.lower()
        if not self.codeblocks.has_key(name):
            return self.responseError("","Could not find codeblock with name:'%s'"%name)
        else:
            snippet=self.codeblocks[name]
            md5=j.tools.hash.md5_string(snippet)
        self.redis.hset("robot:snippets", md5, snippet)
        return "snippetkey=%s"%md5

    def process(self, txt):
        txt=self._findCodeBlocks(txt)        
        txt=self._longTextTo1Line(txt)
        txt=self._processSnippets(txt) #replace snippets 

        entity=""
        args={}
        cmds=list()
        cmd=""
        out=""

        txt=txt.rstrip("\n")
        splitted=txt.split("\n")

        gargs={}

        for line in splitted:
            # print "process:%s"%line
            line=line.strip()

            if line.find(">ERROR:")==0:
                continue

            if line=="" or line[0]=="#" or line[0]==">" or line[0]=="<":
                out+="%s\n"%line
                continue

            #DEAL WITH HELP CMDS
            if line=="?" or line=="h" or line=="help":
                out+=self.response("help",self.help.help())
                continue
            if line.find("help.definition")<>-1:
                out+=self.response("!help.definition",self.help.help_definition())
                continue
            if line.find("help.cmds")<>-1:
                out+=self.response("!help.cmds",self.definition)
                # out+= '%s\n' % self.definition  #<br/>
                continue

            if cmd<>"" and (line[0]=="!" or line[0]=="@" or line.find("******")<>-1):
                #end of cmd block                
                out+=self.processCmd(cmdblock,entity, cmd, args,gargs)
                cmdblock=""
                cmd=""                

            #DEAL WITH SNIPPET CREATE CMD
            if line.find("!snippet.create")==0:
                remainder=line.split("!snippet.create",1)[1]
                out+=self.response(line,self._snippetCreate(remainder.strip()))
                continue

            if cmd=="" and line.find("=")<>-1:
                #global args                
                gargs=self._processGlobalArg(gargs,line)
                out+="%s\n"%line
                continue

            if line[0]=="!":
                #CMD
                entity=""
                cmd=""
                args={}
                line2=line.strip("!")
                line2=line2.strip()
                entity,cmd=line2.split(".",1)
                entity=entity.lower().strip()
                if cmd.find(" ")<>-1:
                    cmd,remainder=cmd.split(" ",1)
                    args["name"]=remainder.strip()
                cmd=cmd.lower().strip()
                cmdblock=""
                if self.entityAlias.has_key(entity):
                    entity=self.entityAlias[entity]

                if not entity in self.entities:
                    # out+= '%s\n' % self.error(,help=True)
                    out+=self.responseError(line,"Could not find entity:'%s'"%(entity))
                    continue

                if self.cmdAlias[entity].has_key(cmd):
                    cmd=self.cmdAlias[entity][cmd]

                if not cmd in self.cmds[entity]:
                    out+= self.responseError(line,"Could not understand command '%s'."%(cmd))
                    continue
                if line.find(" ")<>-1:
                    remainder=line.split(" ",1)[1]
                    args["name"]=remainder.strip()

            if cmd<>"":
                cmdblock+="%s\n"%line

            if line.find("=")<>-1 and cmd<>"":
                name,data=line.split("=",1)
                name=name.lower()
                # print "args:%s:%s '%s'"%(name,data,line)
                args[name]=data.strip().replace("\\n","\n")

        if cmd<>"":
            #end of cmd block                
            out+=self.processCmd(cmdblock,entity, cmd, args,gargs)

        out=out.strip()+"\n"

        for cbname,cblock in self.codeblocks.iteritems():            
            out="@START %s\n%s\n@END\n\n%s"%(cbname,cblock,out)

        out=out.strip()

        while out.find("\n\n\n")<>-1:
            out=out.replace("\n\n\n","\n\n")

        return out


    def processCmd(self, cmdblock,entity, cmd, args,gargs):
        
        args=copy.copy(args)
        for key,val in gargs.iteritems():
            args[key]=val
        
        key="%s__%s"%(entity,cmd)
        result=None
        if self.cmdobj<>None:
            if hasattr(self.cmdobj,key):
                try:
                    method=eval("self.cmdobj.%s"%key)
                except Exception,e:
                    return self.responseError(cmdblock,"Cannot execute: '%s':'%s' , could not eval code."%(entity,cmd))
                #now execute the code
                try:
                    result=method(**args)
                except Exception,e:
                    if str(e).find("E:")==0:
                        j.errorconditionhandler.processPythonExceptionObject(e)
                        e=str(e)[2:]
                        return self.responseError(cmdblock,"Cannot execute: '%s':'%s'\n%s"%(entity,cmd,e))
                    else:
                        j.errorconditionhandler.processPythonExceptionObject(e)
                    return self.responseError(cmdblock,"Cannot execute: '%s':'%s' , could not execute code, error."%(entity,cmd))

        if result==None:
            return self.responseError(cmdblock,"Cannot execute: '%s':'%s' , entity:method not found."%(entity,cmd))
        
        if not j.basetype.string.check(result):
            result=yaml.dump(result, default_flow_style=False).replace("!!python/unicode ","")        
        out=self.response(cmdblock,result)
        return out

        # if j.basetype.list.check(result):
        #     out=""
        #     for item in result:
        #         out+="- %s\n"%item
        #     out+="\n\n"
        #     return out


        
    def addCmdClassObj(self,cmdo):
        cmdo.txtrobot=self
        self.cmdobj=cmdo

