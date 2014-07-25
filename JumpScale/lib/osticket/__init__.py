from JumpScale import j
j.base.loader.makeAvailable(j, 'client')
from OSTicketFactory import OSTicketFactory
j.client.osticket=OSTicketFactory()