__author__ = 'delandtj'

import os
import os.path
import subprocess
import sys
import syslog
import time

command_name = sys.argv[0]

vsctl = "/usr/bin/ovs-vsctl"
ofctl = "/usr/bin/ovs-ofctl"
ip = "/sbin/ip"
ethtool = "/sbin/ethtool"


# TODO : errorhandling
def send_to_syslog(msg):
    print msg
    # pid = os.getpid()    
    # print ("%s[%d] - %s" % (command_name, pid, msg))    
    # syslog.syslog("%s[%d] - %s" % (command_name, pid, msg))



def doexec(args):
    """Execute a subprocess, then return its return code, stdout and stderr"""
    send_to_syslog(args)
    proc = subprocess.Popen(args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    rc = proc.wait()
    stdout = proc.stdout
    stderr = proc.stderr
    return rc, stdout, stderr


def get_all_namespaces():
    cmd = '%s netns ls' % ip
    r, s, e = doexec(cmd.split())
    return [line.strip() for line in s.readlines()]


def get_all_ifaces():
    """
    List of network interfaces
    @rtype : dict
    """
    netpath = '/sys/class/net'; ifaces = {}
    for i in os.listdir(netpath):
        with open(os.path.join(netpath, i, "address")) as f:
            addr = f.readline().strip()
            ifaces[i] = addr
    return ifaces

def get_all_bridges():
    cmd = '%s list-br' % vsctl
    r, s, e = doexec(cmd.split())
    l =  [line.strip() for line in s.readlines()]
    return l


def ip_link_set(device, args):
    doexec([ip, "link", "set", device, args])


def createBridge(name):
    cmd = '%s --may-exist add-br %s' % (vsctl, name)
    r,s,e = doexec(cmd.split())
    if r:
        raise RuntimeError("Problem with creation of bridge %s, err was: %s" % (name,e))


def destroyBridge(name):
    cmd = '%s --may-exist del-br %s' % (vsctl, name)
    r,s,e = doexec(cmd.split())
    if r:
        send_to_syslog("Problem with destruction of bridge %s, err was: %s" % (name,e))
        exit(1)

def addVlanPair(parentbridge, vlanbridge, vlanid):
    cmd = '%s add-port %s brp-%s tag=%s -- set Interface brp-%s type=patch options:peer=trp-%s' % (vsctl, parentbridge, vlanid, vlanid, vlanid, vlanid)
    r,s,e = doexec(cmd.split())
    if r:
        raise RuntimeError("Add extra vlan pair filed %s" % (e))
    cmd = '%s add-port %s trp-%s -- set Interface trp-%s type=patch options:peer=brp-%s' % (vsctl, vlanbridge, vlanid, vlanid, vlanid)
    r,s,e = doexec(cmd.split())
    if r:
        raise RuntimeError("Add extra vlan pair filed %s" % (e))

def createNameSpace(name):
    if name not in get_all_namespaces():
        cmd = '%s netns add %s' % (ip,name)
        r,s,e  = doexec(cmd.split())
    else:
        send_to_syslog('Namespace %s already exists, not creating' % name)


def destroyNameSpace(name):
    if name in get_all_namespaces():
        cmd = '%s netns delete %s' % (ip, name)
        r,s,e  = doexec(cmd.split())
    else:
        send_to_syslog('Namespace %s doesn\'t exist, nothing done ' % name)


def createVethPair(left,right):
    cmd = '%s link add %s type veth peer name %s' %(ip, left, right)
    if left in allifaces or right in allifaces:
        # one of them already exists
        send_to_syslog("Problem with creation of vet pair %s, %s :one of them exists" %(left,right))
        exit(1)
    r,s,e = doexec(cmd.split())
    # wait for it to come up
    time.sleep(.2)
    ip_link_set(left,'up')
    ip_link_set(right,'up') # when sent into namespace, it'll be down again
    disable_ipv6(left) # not right, as it can be used in a namespace


def destroyVethPair(left):
    cmd = '%s link del %s ' %(ip, left)
    r,s,e = doexec(cmd.split())
    if r:
        send_to_syslog("Problem with destruction of Veth pair %s, err was: %s" % (left,e))
        exit(255)


def createVXlan(vxname,vxid,multicast,vxbackend):
    """
    Always brought up too
    Created with no protocol, and upped (no ipv4, no ipv6)
    Fixed standard : 239.0.x.x, id
    # 0000-fe99 for customer vxlans, ff00-ffff for environments
    """
    cmd = 'ip link add %s type vxlan id %s group %s ttl 60 dev %s' % (vxname, vxid, multicast, vxbackend)
    r,s,e = doexec(cmd.split())
    ip_link_set(vxname,'up')
    if r:
        send_to_syslog("Problem with creation of vxlan %s, err was: %s" % (vxname ,e))


def destroyVXlan(name):
    cmd = '%s link del %s ' %(ip, name)
    r,s,e = doexec(cmd.split())
    if r:
        send_to_syslog("Problem with destruction of Veth pair %s, err was: %s" % (name,e))
        exit(1)


def addIPv4(interface,ipobj,namespace=None):
    netmask = ipobj.prefixlen
    ipv4addr = ipobj.ip
    # if ip existst on interface, we assume all ok

    if namespace != None:
        cmd = '%s netns exec %s ip addr add %s/%s dev %s' % (ip, namespace, ipv4addr, netmask, interface)
    else:
        cmd = '%s addr add %s/%s dev %s' % (ip, ipv4addr, netmask, interface)
    r,s,e = doexec(cmd.split())
    if r:
        send_to_syslog('Clould not add IP %s to interface %s ' % (ipv4addr, interface))
    return r,e


def addIPv6(interface, ipobj, namespace=None):
    netmask = ipobj.prefixlen
    ipv6addr = ipobj.ip
    # if ip existst on interface, we assume all ok

    if namespace != None and namespace in allnamespaces:
        cmd = '%s netns exec %s ip addr add %s/%s dev %s' % (ip, namespace, ipv6addr, netmask, interface)
    else:
        cmd = '%s addr add %s/%s dev %s' % (ip, ipv6addr, netmask, interface)
    r,s,e = doexec(cmd.split())
    if r:
        send_to_syslog('Could not add IP %s to interface %s ' % (ipv6addr, interface))
    return r, e



def connectIfToBridge(bridge,interface):
    cmd = '%s --may-exist add-port %s %s' %(vsctl,bridge,interface)
    r,s,e = doexec(cmd.split())
    if r:
        raise RuntimeError('Error adding port %s to bridge %s' %(interface,bridge))


def connectIfToNameSpace(nsname,interface):
    cmd = '%s link set %s netns %s' %( ip, interface, nsname)
    r,s,e = doexec(cmd.split())
    if r:
        raise RuntimeError("Error moving %s to namespace %s" %(interface,nsname))


def disable_ipv6(interface):
    if interface in allifaces:
        cmd = 'sysctl -w net.ipv6.conf.%s.disable_ipv6=1' % interface
        r,s,e = doexec(cmd.split())

allifaces = get_all_ifaces()
allnamespaces = get_all_namespaces()


