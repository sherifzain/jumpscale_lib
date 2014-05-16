from JumpScale import j
# import JumpScale.baselib.remote
import time
class RouterOSFactory(object):

    def get(self, host, login,password):
        return RouterOS(host, login,password)
#!/usr/bin/python

import sys, posix, time, md5, binascii, socket, select

class ApiRos:
    "Routeros api"
    def __init__(self, sk):
        self.sk = sk
        self.currenttag = 0
        
    def login(self, username, pwd):
        for repl, attrs in self.talk(["/login"]):
            chal = binascii.unhexlify(attrs['=ret'])
        md = md5.new()
        md.update('\x00')
        md.update(pwd)
        md.update(chal)
        res=self.talk(["/login", "=name=" + username,"=response=00" + binascii.hexlify(md.digest())])
        return res[0][0].find("done")<>-1        

    def talk(self, words):
        if self.writeSentence(words) == 0: return
        r = []
        while 1:
            i = self.readSentence();
            if len(i) == 0: continue
            reply = i[0]
            attrs = {}
            for w in i[1:]:
                j = w.find('=', 1)
                if (j == -1):
                    attrs[w] = ''
                else:
                    attrs[w[:j]] = w[j+1:]
            r.append((reply, attrs))
            if reply == '!done': return r

    def writeSentence(self, words):
        ret = 0
        for w in words:
            self.writeWord(w)
            ret += 1
        self.writeWord('')
        return ret

    def readSentence(self):
        r = []
        while 1:
            w = self.readWord()
            if w == '': return r
            r.append(w)
            
    def writeWord(self, w):
        print "<<< " + w
        self.writeLen(len(w))
        self.writeStr(w)

    def readWord(self):
        ret = self.readStr(self.readLen())
        print ">>> " + ret
        return ret

    def writeLen(self, l):
        if l < 0x80:
            self.writeStr(chr(l))
        elif l < 0x4000:
            l |= 0x8000
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))
        elif l < 0x200000:
            l |= 0xC00000
            self.writeStr(chr((l >> 16) & 0xFF))
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))
        elif l < 0x10000000:        
            l |= 0xE0000000         
            self.writeStr(chr((l >> 24) & 0xFF))
            self.writeStr(chr((l >> 16) & 0xFF))
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))
        else:                       
            self.writeStr(chr(0xF0))
            self.writeStr(chr((l >> 24) & 0xFF))
            self.writeStr(chr((l >> 16) & 0xFF))
            self.writeStr(chr((l >> 8) & 0xFF))
            self.writeStr(chr(l & 0xFF))

    def readLen(self):              
        c = ord(self.readStr(1))    
        if (c & 0x80) == 0x00:      
            pass                    
        elif (c & 0xC0) == 0x80:    
            c &= ~0xC0              
            c <<= 8                 
            c += ord(self.readStr(1))    
        elif (c & 0xE0) == 0xC0:    
            c &= ~0xE0              
            c <<= 8                 
            c += ord(self.readStr(1))    
            c <<= 8                 
            c += ord(self.readStr(1))    
        elif (c & 0xF0) == 0xE0:    
            c &= ~0xF0              
            c <<= 8                 
            c += ord(self.readStr(1))    
            c <<= 8                 
            c += ord(self.readStr(1))    
            c <<= 8                 
            c += ord(self.readStr(1))    
        elif (c & 0xF8) == 0xF0:    
            c = ord(self.readStr(1))     
            c <<= 8                 
            c += ord(self.readStr(1))    
            c <<= 8                 
            c += ord(self.readStr(1))    
            c <<= 8                 
            c += ord(self.readStr(1))    
        return c                    

    def writeStr(self, str):        
        n = 0;                      
        while n < len(str):         
            r = self.sk.send(str[n:])
            if r == 0: raise RuntimeError, "connection closed by remote end"
            n += r                  

    def readStr(self, length):      
        ret = ''                    
        while len(ret) < length:    
            s = self.sk.recv(length - len(ret))
            if s == '': raise RuntimeError, "connection closed by remote end"
            ret += s
        return ret


class RouterOS(object):

    def __init__(self, host, login,password):
        # self.configPath = j.system.fs.joinPaths('/etc', 'RouterOS')
        # self.remoteApi = j.remote.cuisine.api
        # j.remote.cuisine.fabric.env['password'] = password
        # self.remoteApi.connect(host)
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((host, 8728 ))  
        self.api = ApiRos(self._s)
        res=self.api.login(login,password)
        self.host=host
        self.login=login
        self.password=password
        self.ftp=None
        if res<>True:
            raise RuntimeError("Could not login into RouterOS: %s"%host)
        self.configpath="%s/apps/routeros/configs/default/"%j.dirs.baseDir

        inputsentence = []

    ##cant get it to work because of ansi
    # def initExpect(self):
    #     e = j.tools.expect.new("ssh %s@%s"%(self.login,self.host))
    #     # e = j.tools.expect.new("telnet %s"%(self.host))
    #     # e.pexpect.delaybeforesend = 0
    #     e.pexpect.logfile = sys.stdout
    #     # r=e.expect("login:",2)
    #     # if r<>"E":
    #     #     #passwd found
    #     #     e.send(self.login+"\n")

    #     r=e.expect("password:",2)
    #     if r<>"E":
    #         #passwd found
    #         e.send(self.password+"\n")
    #     # r=e.expect(" >",1)
    #     # if r=="E":
    #     print "expect enter"        

    #     r=e.pexpect.expect(["Enter"," >"],2)
    #     if r==0:
    #         #means we need to press enter
    #         # e.pexpect.sendcontrol('m')
    #         e.pexpect.send("\r")
    #     elif r==1:
    #         #we are in
    #         return

    #     r=e.expect(" >",2)
    #     print r

    #     from IPython import embed
    #     print "DEBUG NOW lll"
    #     embed()
        
    #     if e.expect("Enter",2)<>"E":
    #         print "found enter"
    #         # e.send("\r\n",newline=False)
    #         e.pexpect.sendcontrol('m')
    #         time.sleep(2)
    #         for i in range(10):
    #             # e.send("\r\n",newline=False)
    #             r=e.expect(" >",0.5)
    #             if r<>"E":
    #                 break
    #             print e.receive()
    #         # time.sleep(1)
    #         # r=e.expect(" >",2)
    #         # if r=="E":
    #         #     raise RuntimeError("could not login to routeros")

    #     from IPython import embed
    #     print "DEBUG NOW error"
    #     embed()

            

    #     # password:

    #     from IPython import embed
    #     print "DEBUG NOW ooo"
    #     embed()
      

    def do(self,cmd,args={}):
        cmds=[]
        cmds.append(cmd)
        for key,value in args.iteritems():
            arg="=%s=%s"%(key,value)
            cmds.append(arg)
        if args<>{}:
            cmds.append("")
        r=self.api.talk(cmds)
        return self._parse_result(r)
 

    def _parse_result(self, talk_result):
        result3=[]
        r = talk_result
        for rc,result in r:
            if rc=="!done":
                return result3
            if rc=="!re" or rc=="!trap":
                #return
                result2={}
                for key,value in result.iteritems():
                    key=key.lstrip("=")
                    if value=="false":
                        value=False
                    elif value=="true":
                        value=True
                    result2[key]=value
                if rc=="!trap":
                    msg=result2["message"]
                    if result2.has_key("category"):
                        cat=result2["category"]
                        cat=int(cat)
                        cats={}
                        cats[0]="missing item or command"
                        cats[1]="argument value failure"
                        cats[2]="execution of command interrupted"
                        cats[3]="scripting related failure"
                        cats[4]="general failure"
                        cats[5]="API related failure"
                        cats[6]="TTY related failure"
                        cats[7]="value generated with :return command"
                        if cats.has_key(cat):
                            msg+"\ncat:%s"%cats[cat]
                    raise RuntimeError("could not execute,error:\n%s"%(msg))
            result3.append(result2)
        return result3

    def _do_filtered(self, cmd, filters):
        cmds = []
        cmds.append(cmd)
        for f in filters:
            cmds.append(f)
        result = self.api.talk(cmds)
        return self._parse_result(result)
        

    def ipaddr_getall(self):
        r=self.do("/ip/address/getall")
        for item in r:
            item["ip"],item["mask"]=item["address"].split("/")
            item["mask"]=int(item["mask"])
        return r

    def iproute_getall(self,staticOnly=False):
        r=self.do("/ip/route/getall")
        nr=0
        result=[]
        for item in r:
            item["nr"]=nr
            nr+=1
            if staticOnly:
                if item["static"]==True:
                    result.append(item)
            else:
                result.append(item)            
        return result     

    def ipaddr_remove(self,ipaddr):
        """
        @ipaddr is without mask e.g. 192.168.7.7
        """
        nr=0
        for item in self.ipaddr_getall():
            if item["ip"]==ipaddr:
                args2={}
                args2["numbers"]="%s"%(nr)
                self.do("/ip/address/remove", args=args2)
            nr+=1
        
    def ipaddr_set(self,interfacename,ipaddr,comment="",single=False):
        """
        @param interfacename e.g. ether1
        @param ipaddr e.g. 192.168.7.3/24  (DO NOT FORGET THE MASK)
        @param single if True then only 1 ip addr per interface, other will be removed
        """
        if ipaddr.find("/")==-1:
            raise RuntimeError("specify mask")
        arg={}
        arg["address"]=ipaddr
        if comment<>"":
            arg["comment"]=comment
        interfaces=self.interface_getnames()
        if interfacename not in interfaces:
            raise RuntimeError("Could not find interface:%s"%interfacename)
        arg["interface"]=interfacename
        if single:
            for item in self.ipaddr_getall():
                if item["interface"]==interfacename:
                    print "found other addr already on interface, will remove.:%s"%item["ip"]
                    self.ipaddr_remove(item["ip"])
        return self.do("/ip/address/add", args=arg)

    def interface_getall(self):
        r=self.do("/interface/getall")
        return r

    def interface_getnames(self):
        names=[]
        for item in self.interface_getall():
            names.append(item["name"])
        return names

    def backup(self,name,destinationdir):
        self.do("/system/backup/save", args={"name":name})
        path="%s.backup"%name
        self.download(path, j.system.fs.joinPaths(destinationdir,path))
        self.do("/export", args={"file":name})
        path="%s.rsc"%name
        self.download(path, j.system.fs.joinPaths(destinationdir,path))

    def download(self,path,dest):
        if self.ftp==None:
            self._getFtp()
        self.ftp.retrbinary('RETR %s'%path, open(dest, 'wb').write)

    def list(self,path):
        self._getFtp()
        res=[]
        def do(arg):
            if arg in [".",".."]:
                return
            res.append(arg)
        self.ftp.retrlines("NLST /%s"%path,do)
        return res

    def delfile(self,path,raiseError=False):
        self._getFtp()
        res=[]
        if raiseError:
            self.ftp.delete(path)
        else:
            try:
                self.ftp.delete(path)
            except Exception, e:
                pass

    def mkdir(self, path):
        self._getFtp()
        self.ftp.mkd(path)

    def _getFtp(self):
        from ftplib import FTP
        self.ftp=FTP(host=self.host, user=self.login, passwd=self.password)
        
    def close(self):
        self.ftp.close()

    def download(self,path,dest,raiseError=False):
        self._getFtp()
        j.system.fs.createDir(j.system.fs.getDirName(dest))
        if raiseError:
            self.ftp.retrbinary('RETR %s'%path, open(dest, 'wb').write)
        else:
            try:
                print "download '%s'"%path,
                self.ftp.retrbinary('RETR %s'%path, open(dest, 'wb').write)
                print
            except Exception, e:
                print "ERROR"
                pass

    def upload(self,path,dest):
        print "upload: '%s' to '%s'"%(path,dest)
        self._getFtp()
        if not j.system.fs.exists(path=path):
            raise RuntimeError("Cannot find %s"%path)
        self.ftp.storbinary('STOR %s'%dest, open(path))

    def removeAllFirewallRules(self):
        cmd="queue tree remove [/queue tree find]"
        self.executeScript(cmd)

    def removeStaticRoutes(self):
        cmd="/ip route remove [/ip route find static=yes]"
        self.executeScript(cmd)

    def uploadExecuteScript(self,name,removeAfter=True,vars={}):
        print "EXECUTE SCRIPT:%s"%name
        name=name+".rsc"
        src=j.system.fs.joinPaths(self.configpath,name)

        content=j.system.fs.fileGetContents(src)
        for key,val in vars.iteritems():
            content=content.replace(key,val)
        src=j.system.fs.joinPaths(j.dirs.tmpDir,j.system.fs.getTempFileName())
        j.system.fs.writeFile(src,content)

        print "EXECUTE:"
        print content
        print "#################END##################"
        
        self.upload(src,name)
        self.do("/import", args={"file-name":name})
        self.delfile(name, raiseError=False)

        j.system.fs.remove(src)


    def executeScript(self,content):
        if content[0]<>"/":
            content="/%s"%content
        name="_tmp_%s"%j.base.idgenerator.generateRandomInt(1,10000)
        src=j.system.fs.joinPaths(self.configpath,"%s.rsc"%name)
        j.system.fs.writeFile(filename=src,contents=content)
        self.uploadExecuteScript(name)
        j.system.fs.remove(src)

    def uploadFilesFromDir(self,path,dest=""):       
        for item in j.system.fs.listFilesInDir(j.system.fs.joinPaths(self.configpath,path),False):
            if dest<>"":
                dest2=j.system.fs.joinPaths(dest,j.system.fs.getBaseName(item))
            else:
                dest2=j.system.fs.getBaseName(item)
            self.upload(item,dest2)

    def addPortForwardRule(self, dstaddress,dstport, toaddress, toport, tags=None):
        arg = {}
        arg['chain'] = 'dstnat'
        arg['dst-address'] = dstaddress
        arg['protocol'] = 'tcp'
        arg['dst-port'] = dstport
        arg['action'] = 'dst-nat'
        arg['to-addresses'] = toaddress
        arg['to-ports']  = toport
        if tags is not None:
            arg['comment'] = tags
        self.do("/ip/firewall/nat/add", args=arg)


    def deletePortForwardRule(self, dstaddress, dstport):
        """
        Delete portforward
        """
        results = self._do_filtered('/ip/firewall/nat/print',filters = ['=.proplist=.id','?dst-address=%s' % dstaddress, '?dst-port=%s' % dstport])
        for i in results:
            self.do('/ip/firewall/nat/remove', args=i)
        return True

    def deletePortForwardRules(self, tags=None):
        """
        Delete port forward rules which has a specific tag.
        This is used for deleting all the rules created by a specific role
        """
        if tags:
            results = self._do_filtered('/ip/firewall/nat/print',filters = ['=.proplist=.id','?comment=%s' % tags])
        else:
            results = self._do_filtered('/ip/firewall/nat/print',filters = ['=.proplist=.id'])
        for i in results:
            self.do('/ip/firewall/nat/remove', args=i)
        return True

    def listPortForwardRules(self, tags=None):
        forwards = self.do('/ip/firewall/nat/getall')
        if tags is not None:
            forwards = [fw for fw in forwards if 'comment' in fw.keys() and fw['comment'] == tags]
        return forwards




