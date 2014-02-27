from JumpScale import j
j.base.loader.makeAvailable(j, 'system.ovsnetconfig')
from .NetConfigFactory import NetConfigFactory
j.system.ovsnetconfig = NetConfigFactory()

