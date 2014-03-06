from JumpScale import j
j.base.loader.makeAvailable(j, 'clients')
from Routerboard import RouterboardFactory
j.clients.routerboard = RouterboardFactory()