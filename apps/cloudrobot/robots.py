
from JumpScale import j

import sys
args=sys.argv
instance=args[1]

jp=j.packages.findNewest(name="cloudrobot",domain="serverapps")
jp=jp.getInstance(instance)

j.servers.cloudrobot.hrd=jp.hrd_instance

robots=jp.hrd_instance.getList("cloudrobot.robots")
robots=[item.split("/",1)[0] for item in robots]

import JumpScale.baselib.mailclient

robots={}


if "ms1_iaas" in robots:
    import JumpScale.lib.ms1
    robots["ms1_iaas"]= j.tools.ms1robot.getRobot()

if "youtrack" in robots:    
    import JumpScale.lib.youtrackclient

    for item in jp.hrd_instance.getList("cloudrobot.robots"):
        if item.find("youtrack")==0:
            tmp,ytinstance=item.split("/",1)
            ytinstance=ytinstance.strip()

    jp_yt=j.packages.findNewest(name="youtrack_client",domain="serverapps")
    jp_yt=jp_yt.getInstance(ytinstance)

    url=jp_yt.hrd_instance.get("youtrack.url")
    
    robots["youtrack"]= j.tools.youtrack.getRobot(url)

if "user" in robots:        
    import JumpScale.lib.usermgmt
    robots["user"]= j.tools.usermgmt.getRobot()


