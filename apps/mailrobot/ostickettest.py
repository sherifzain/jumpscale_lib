
from JumpScale import j

j.application.start("jumpscale:sqltest")

import JumpScale.lib.osticket
client=j.client.osticket.getClient('dco.incubaid.com', 2746,'despiegk', 'Kds007', 'osticket')
# print client.exportTickets()

client.deleteTicket(856019)

j.application.stop()

from IPython import embed
print "DEBUG NOW id"
embed()
