from JumpScale import j
import sys
sys.path.append("%s/lib/youtrackclient/"%j.dirs.jsLibDir)
# from JumpScale.lib.youtrackclient.youtrack.connection import Connection
from youtrack.connection import Connection
import copy
import ujson as json
sys.path.pop(sys.path.index("%s/lib/youtrackclient/"%j.dirs.jsLibDir))

class YoutrackFactory(object):

    def __init__(self):
        pass
        
    def get(self, url, login,password):
        # print "connection get: %s '%s':'%s'"%(url,login,password)
        return Connection(url,login,password)


