from JumpScale import j

import time
import JumpScale.lib.mysql

class OSTicketFactory():
    """
    """

    def __init__(self):
        self.clients={}


    def getClient(self,ipaddr,port,login,passwd,dbname):
        """
        use info from osticket db server (mysql)
        """
        key="%s_%s_%s_%s_%s"%(ipaddr,port,login,passwd,dbname)
        if not self.clients.has_key(key):
            self.clients[key]=j.client.mysql.getClient(ipaddr, port,login, passwd, dbname)
        return OSTicketClient(self.clients[key])


class OSTicketClient():

    def __init__(self,cl):
        self.client=cl

    def _boolToInt(self,arg):
        if arg:
            return 1
        else:
            return 0
        # arg=str(arg.lower())
        # if arg=="false" or arg=="0":
        #     return False

    def _getOSTicketIDFromLargeId(self,id):
        C="""
SELECT ticketID, ticket_id
FROM ost_ticket
WHERE ticketID=$id;
"""
        C=C.replace("$id",str(id))

        result=self.client.queryToListDict(C)
        if len(result)==1:
            return result[0]['ticket_id']
        else:
            return 0

    
    def deleteTicket(self,id):
        id=self._getOSTicketIDFromLargeId(id)
        if id==0:
            return "NOTFOUND"
        self.client.deleteRow("ost_ticket__cdata","ticket_id=%s"%id)
        self.client.deleteRow("ost_ticket_event","ticket_id=%s"%id)
        self.client.deleteRow("ost_ticket_thread","ticket_id=%s"%id)
        attachid=self.client.select1("ost_ticket_attachment","file_id","ticket_id=%s"%id)
        if attachid<>None:
            self.client.deleteRow("ost_file","file_id=%s"%attachid)
            self.client.deleteRow("ost_file_chunk","file_id=%s"%attachid)
        self.client.deleteRow("ost_ticket","ticket_id=%s"%id)
    

    def getStaff(self):
        C="""
SELECT ost_staff.staff_id, ost_staff.username, ost_staff.firstname, ost_staff.lastname, ost_staff.email, ost_staff.phone, ost_staff.phone_ext, ost_staff.mobile, ost_staff.notes, ost_staff.isactive AS bool__isactive, ost_staff.isadmin AS bool__isadmin, ost_staff.lastlogin AS dt__lastlogin, ost_staff.created AS dt__created, ost_groups.group_name
FROM ost_staff INNER JOIN ost_groups ON ost_staff.group_id = ost_groups.group_id;


"""
        result2={}
        result=self.client.queryToListDict(C)
        for item in result:
            staffid=item["staff_id"]
            item.pop("staff_id")
            result2[int(staffid)]=item
        return result2

    def exportTickets(self):
        staff=self.getStaff()
        out=""
        C="""
SELECT ost_ticket.ticketID AS id__ticketid, ost_ticket.status, ost_ticket__cdata.subject, ost_user.name AS username, ost_user_email.address AS email, ost_ticket__cdata.priority, ost_ticket.closed AS dt__closed, ost_ticket_thread.title AS threadtitle, ost_ticket_thread.body AS html__threadbody, ost_ticket_thread.created AS dt__threadcreated, ost_ticket.isanswered AS bool__isanswered, ost_ticket.duedate AS dt__duedate, ost_ticket.lastmessage AS dt__lastmessage, ost_ticket.lastresponse AS dt__lastresponse, ost_ticket_thread.staff_id AS id__threadstaffid, ost_ticket.staff_id AS id__assignee
FROM ost_user_email RIGHT JOIN (ost_ticket__cdata INNER JOIN ((ost_ticket_thread INNER JOIN ost_ticket ON ost_ticket_thread.ticket_id = ost_ticket.ticket_id) INNER JOIN ost_user ON ost_ticket.user_id = ost_user.id) ON ost_ticket__cdata.ticket_id = ost_ticket.ticket_id) ON ost_user_email.user_id = ost_ticket.user_id
WHERE (((ost_ticket.closed) Is Null));

"""

        result=self.client.queryToListDict(C)
        
        if len(result)==0:
            return ""
        currentsubject=""
        for item in result:
            if currentsubject<>item["subject"]:
                currentsubject=item["subject"]
                out+= "\n##################################\n"
                out=j.tools.text.addCmd(out,"ticket","new")
                out=j.tools.text.addVal(out,"subject",item["subject"])
                out=j.tools.text.addVal(out,"status",item["status"])
                out=j.tools.text.addVal(out,"body",item["threadbody"])
                out=j.tools.text.addVal(out,"priority",item["priority"].lower())
                out=j.tools.text.addVal(out,"id_osticket",item["ticketid"])
                out=j.tools.text.addVal(out,"isanswered",self._boolToInt(item["isanswered"]))
                out=j.tools.text.addVal(out,"from_email",item["email"])
                out=j.tools.text.addVal(out,"from_username",item["username"])
                out=j.tools.text.addVal(out,"duedate",item["duedate"],addtimehr=True)
                out=j.tools.text.addVal(out,"time_created",item["threadcreated"],addtimehr=True)
                out=j.tools.text.addVal(out,"time_lastmessage",item["lastmessage"],addtimehr=True)
                out=j.tools.text.addVal(out,"time_lastresponse",item["lastresponse"],addtimehr=True)
                if staff.has_key(int(item["assignee"])):
                    st=staff[int(item["assignee"])]
                    out=j.tools.text.addVal(out,"assignee",st["email"])
                    
                if item["closed"]<>0:
                    out=j.tools.text.addVal(out,"time_closed",item["closed"])
            else:
                #add thread
                if item["threadtitle"]<>currentsubject:
                    out+="\n###\n!ticket.thread\n"
                    out=j.tools.text.addVal(out,"id_osticket",item["ticketid"])
                    out=j.tools.text.addVal(out,"subject",item["threadtitle"])
                    out=j.tools.text.addVal(out,"body",item["threadbody"])
                    out=j.tools.text.addVal(out,"time_created",item["threadcreated"],addtimehr=True)

        return out
