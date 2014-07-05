
from JumpScale import j

j.application.start("jumpscale:sqltest")

import JumpScale.lib.mysql

C="""
SELECT ost_ticket.ticketID AS id__ticketid, ost_ticket.status, ost_ticket__cdata.subject, ost_user.name AS username, ost_user_email.address AS email, ost_ticket__cdata.priority, ost_ticket.closed AS dt__closed, ost_ticket_thread.title AS threadtitle, ost_ticket_thread.body AS html__threadbody, ost_ticket_thread.created AS dt__threadcreated, ost_ticket.isanswered AS bool__isanswered, ost_ticket.duedate AS dt__duedate, ost_ticket.lastmessage AS dt__lastmessage, ost_ticket.lastresponse AS dt__lastresponse
FROM ost_user_email RIGHT JOIN (ost_ticket__cdata INNER JOIN ((ost_ticket_thread INNER JOIN ost_ticket ON ost_ticket_thread.ticket_id = ost_ticket.ticket_id) INNER JOIN ost_user ON ost_ticket.user_id = ost_user.id) ON ost_ticket__cdata.ticket_id = ost_ticket.ticket_id) ON ost_user_email.user_id = ost_ticket.user_id
WHERE (((ost_ticket.closed) Is Null));
"""

client=j.client.mysql.getClient('dco.incubaid.com', 2746,'despiegk', 'Kds007', 'osticket')
result=client.queryToListDict(C)

from IPython import embed
print "DEBUG NOW id"
embed()
