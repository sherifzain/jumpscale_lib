from JumpScale import j
j.base.loader.makeAvailable(j, 'clients.rogerthat')
from rogerthat import RogerthatFactory
j.clients.rogerthat = RogerthatFactory()