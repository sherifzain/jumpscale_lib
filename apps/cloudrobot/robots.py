
from JumpScale import j

import sys
args=sys.argv
instance=args[1]

jp=j.packages.findNewest(name="cloudrobot",domain="serverapps")
jp=jp.load(instance=instance)

j.servers.cloudrobot.hrd=jp.hrd_instance

robots2=jp.hrd_instance.getList("cloudrobot.robots")
robots2=[item.split("/",1)[0] for item in robots2]

import JumpScale.baselib.mailclient

robots={}


if "ms1_iaas" in robots2:
    import JumpScale.lib.cloudrobotservices.ms1_iaas
    robots["ms1_iaas"]= j.robots.ms1_iaas.getRobot()

if "youtrack" in robots2:    
    import JumpScale.lib.cloudrobotservices.youtrack

    for item in jp.hrd_instance.getList("cloudrobot.robots"):
        if item.find("youtrack")==0:
            tmp,ytinstance=item.split("/",1)
            ytinstance=ytinstance.strip()

    jp_yt=j.packages.findNewest(name="youtrack_client",domain="serverapps")
    jp_yt=jp_yt.load(instance=ytinstance)

    url=jp_yt.hrd_instance.get("youtrack.url")
    
    robots["youtrack"]= j.robots.youtrack.getRobot(url)

if "user" in robots2:        
    import JumpScale.lib.cloudrobotservices.usermgmt
    robots["user"]= j.robots.usermgmt.getRobot()


