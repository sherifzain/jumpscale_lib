from JumpScale import j
j.base.loader.makeAvailable(j, 'tools')
from Docker import Docker
j.tools.docker = Docker()

