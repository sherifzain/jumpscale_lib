from JumpScale import j

import JumpScale.lib.fabric

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
        self.fabric = j.tools.fabric.api
        j.tools.fabric.setHost()

    def install(self):
        codename, descr, id, release = j.system.platform.ubuntu.getVersion()
        do = j.develtools.installer._do
        do.execute("easy_install cuisine")

    def help(self):
        C = """
import JumpScale.lib.cuisine        
#easiest way to use do:
c=j.tools.cuisine
#and then

c.user_ensure(...)
        """
        print C
