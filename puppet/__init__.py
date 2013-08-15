
from OpenWizzy import o

o.base.loader.makeAvailable(o, 'tools')

from PuppetTool import PuppetTool

o.tools.puppet=PuppetTool()
