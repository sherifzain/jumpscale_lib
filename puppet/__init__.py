
from JumpScale import j

j.base.loader.makeAvailable(j, 'tools')

from PuppetTool import PuppetTool

j.tools.puppet = PuppetTool()
