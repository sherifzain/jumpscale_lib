
from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')

from FabricTool import FabricTool

j.remote.fabric = FabricTool()
