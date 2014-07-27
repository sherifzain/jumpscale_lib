import os
# os.system(command)
import sys
import time
args=sys.argv
import ujson as json

if len(args)<>2:
    print "please specify right options"
    print "https://$url/?session=$sessionid"
    exit()

tags=args[1].split("?",1)[1]
# print tags

name,value=tags.split("=",1)

if name.lower().strip()<>"session":
    print "please specify right options, arg needs to be named session"
    print "https://$url/?session=$sessionid"
    exit()

name=value.strip()

class Session():
    def __init__(self):
        self.epoch=int(time.time())
        self.pids=[]
        self.addPid(os.getpid())

    def addPid(self,pid):
        if pid not in self.pids:
            self.pids.append(pid)


import redis
r = redis.StrictRedis(host='localhost', port=7768)



if r.hexists("robot:sessions", name):
    sessiondict=json.loads(r.hget("robot:session:jobsession", name))
    session=Session()
    session.__dict__.update(sessiondict)
    session.addPid(os.getpid())
else:
    session=Session()
    
r.hset("robot:sessions", name, json.dumps(session.__dict__))

_stderr = sys.stderr
_stdout = sys.stdout

null = open(os.devnull,'wb')
sys.stdout = null
sys.stderr = null

# os.system("tmux kill-session -t %s"%name)
# os.system("tmux new-session -d -s %s  js"%name)
# os.system("tmux set-option -t %s status off"%name)
# os.system("tmux send -t %s clear ENTER"%name)

sys.stderr=_stderr
sys.stdout=_stdout

# print "Start Robot Session"

print r.hget("robot:session:jobsession", name)

os.system("tmux a -t %s"%name)

# os.system("tmux send -t %s  exit  ENTER"%name)

