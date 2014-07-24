from JumpScale import j

from robots import *

j.application.start('testrobot')

C="""
login=root
passwd=rooter

project=test


@START cb1
#just comments
@END

!p.r
!u.r

@start cb2
#just comments
@end

!snippet.create cb1

!story.new
name=first working version of cloud.robot
descr=...
brrr
...
who=despiegk

"""

from robots import *

robot=robots["youtrack"]

print robot.process(C)

j.application.stop(0)
