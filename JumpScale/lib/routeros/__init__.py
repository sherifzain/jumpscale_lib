from JumpScale import j
j.base.loader.makeAvailable(j, 'clients')
from RouterOS import RouterOSFactory
j.clients.routeros = RouterOSFactory()