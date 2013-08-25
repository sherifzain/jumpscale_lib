from JumpScale import j

j.system.platform.ubuntu.check()

do = j.develtools.installer._do
try:
    import fabric
except:
    do.execute("easy_install fabric")

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
        self.do = j.develtools.installer._do
        self.api = fabric.api
        self.setHost()

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
f=j.tools.fabric.api
and then

f.run(...)
        """
        print C
