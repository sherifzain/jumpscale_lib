from JumpScale import j
j.base.loader.makeAvailable(j, 'clients')
from CiscoSwitchManager import CiscoSwitchManager
j.clients.ciscoswitch = CiscoSwitchManager()