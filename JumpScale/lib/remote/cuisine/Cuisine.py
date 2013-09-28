from JumpScale import j

import JumpScale.lib.remote.fabric

j.system.platform.ubuntu.check()
do = j.develtools.installer._do

try:
    import cuisine
except:
    do.execute("easy_install cuisine")

import cuisine


class Cuisine():

    def __init__(self):
        self.api = cuisine
        self.fabric = j.remote.fabric.api
        j.remote.fabric.setHost()

    def install(self):
        codename, descr, id, release = j.system.platform.ubuntu.getVersion()
        do = j.develtools.installer._do
        do.execute("easy_install cuisine")

    def help(self):
        C = """
import JumpScale.lib.remote.cuisine        
#easiest way to use do:
c=j.remote.cuisine
#and then

c.user_ensure(...)
        """
        print C
