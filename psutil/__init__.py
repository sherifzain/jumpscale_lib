
from OpenWizzy import o

o.base.loader.makeAvailable(o, 'tools')

try:
    import psutil
except:
    do.execute("easy_install psutil")

import psutil

o.tools.psutil=psutil

# from PSutilTool import PSutilTool

# o.tools.psutil=PSutilTool()
