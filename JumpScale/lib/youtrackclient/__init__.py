from JumpScale import j
j.base.loader.makeAvailable(j, 'tools')
from YoutrackFactory import YoutrackFactory
j.tools.youtrack=YoutrackFactory()