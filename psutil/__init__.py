
from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')

try:
    import psutil
except:
    do.execute("easy_install psutil")

import psutil

j.tools.psutil = psutil

# from PSutilTool import PSutilTool

# j.tools.psutil=PSutilTool()
