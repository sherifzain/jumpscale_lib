
from OpenWizzy import o

o.base.loader.makeAvailable(o, 'tools')

from FabricTool import FabricTool

o.tools.fabric=FabricTool()
