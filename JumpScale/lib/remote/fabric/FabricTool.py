from JumpScale import j

j.system.platform.ubuntu.check()

do = j.develtools.installer._do
import fabric
import fabric.api

# from fabric.api import run as frun
# from fabric.api import execute as fexecute
# from fabric.api import env as fenv
# from fabric.api import open_shell as fopen_shell
# from fabric.api import path as fpath
# from fabric.api import show as fshow
# from fabric.api import put as fput

class FabricTool():

    def __init__(self):
        self._do = j.develtools.installer._do
        self.api = fabric.api
        self.setHost()
        self.api.env.passwords = {}

    def setDefaultPasswd(self,passwd,host="localhost"):
        self.api.env["password"]=passwd
        self.api.env.passwords["root@%s"%host]=passwd
        # self.api.env.hosts = ['user1@host1:port1', 'user2@host2.port2']
        # self.api.env.passwords = {'user1@host1:port1': 'password1', 'user2@host2.port2': 'password2'}

    def install(self):
        codename, descr, id, release = j.system.platform.ubuntu.getVersion()
        do = j.develtools.installer._do
        do.execute("pip install fabric")

    def setHost(self, host="localhost"):
        self.api.env["host_string"] = host

    def setHosts(self, hosts=["localhost"]):
        """
        list of hosts on which the commands will work
        """
        self.api.env.hosts = [hosts]

    def help(self):
        C = """
easiest way to use do:
f=j.remote.fabric.api
and then

f.api.run(...)
        """
        print C
