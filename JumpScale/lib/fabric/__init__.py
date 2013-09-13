
from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')

from FabricTool import FabricTool

j.tools.fabric = FabricTool()
