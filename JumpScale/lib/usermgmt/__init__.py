from JumpScale import j
j.base.loader.makeAvailable(j, 'tools.usermgmt')
from .UserFactory import UserFactory
j.tools.usermgmt = UserFactory()