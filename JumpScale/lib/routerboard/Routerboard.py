from JumpScale import j
# import JumpScale.baselib.remote

class RouterboardFactory(object):

    def get(self, host, login,password):
        return Routerboard(host, login,password)
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

# def main():
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.connect((sys.argv[1], 8728))  
#     apiros = ApiRos(s);             
#     apiros.login(sys.argv[2], sys.argv[3]);

#     inputsentence = []

#     while 1:
#         r = select.select([s, sys.stdin], [], [], None)
#         if s in r[0]:
#             # something to read in socket, read sentence
#             x = apiros.readSentence()

#         if sys.stdin in r[0]:
#             # read line from input and strip off newline
#             l = sys.stdin.readline()
#             l = l[:-1]

#             # if empty line, send sentence and start with new
#             # otherwise append to input sentence
#             if l == '':
#                 apiros.writeSentence(inputsentence)
#                 inputsentence = []
#             else:
#                 inputsentence.append(l)

# if __name__ == '__main__':
#     main()


class Routerboard(object):

    def __init__(self, host, login,password):
        # self.configPath = j.system.fs.joinPaths('/etc', 'Routerboard')
        # self.remoteApi = j.remote.cuisine.api
        # j.remote.cuisine.fabric.env['password'] = password
        # self.remoteApi.connect(host)
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((host, 8728))  
        self.api = ApiRos(self._s)
        res=self.api.login(login,password)
        self.host=host
        self.login=login
        self.password=password
        if res<>True:
            raise RuntimeError("Could not login into routerboard: %s"%host)

        inputsentence = []
        
    def do(self,cmd,args={}):
        cmds=[]
        cmds.append(cmd)
        for key,value in args.iteritems():
            arg="=%s=%s"%(key,value)
            cmds.append(arg)
        if args<>{}:
            cmds.append("")
        r=self.api.talk(cmds)
        result3=[]
        for rc,result in r:
            if rc=="!done":
                return result3
            if rc=="!re" or rc=="!trap":
                #return
                result2={}
                for key,value in result.iteritems():
                    key=key.lstrip("=")
                    if key[0]==".":
                        # value=int(value.replace("*",""))-1
                        continue
                    if value=="false":
                        value=False
                    elif value=="true":
                        value=True
                    else:
                        try:
                            value=int(value)
                        except Exception,e:
                            pass
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
                    raise RuntimeError("could not execute:%s,error:\n%s"%(cmd,msg))
                    
                result3.append(result2)

    def ipaddr_getall(self):
        r=self.do("/ip/address/getall")
        for item in r:
            item["ip"],item["mask"]=item["address"].split("/")
            item["mask"]=int(item["mask"])
        return r

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
        from ftplib import FTP
        ftp=FTP(host=self.host, user=self.login, passwd=self.password)
        ftp.retrbinary('RETR %s'%path, open(dest, 'wb').write)
        ftp.close()
