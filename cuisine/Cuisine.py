from OpenWizzy import o

import OpenWizzy.lib.fabric

o.system.platform.ubuntu.check()
do=o.develtools.installer._do

try:
    import cuisine
except:
    do.execute("easy_install cuisine")

import cuisine

class Cuisine():
    def __init__(self):
        self.api=cuisine
        self.fabric=o.tools.fabric.api
        o.tools.fabric.setHost()

    def install(self):
        codename,descr,id,release=o.system.platform.ubuntu.getVersion()
        do=o.develtools.installer._do
        do.execute("easy_install cuisine")


    def help(self):
        C="""
import OpenWizzy.lib.cuisine        
#easiest way to use do:
c=o.tools.cuisine
#and then

c.user_ensure(...)
        """
        print C
        


        