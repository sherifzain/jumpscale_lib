from JumpScale import j
j.base.loader.makeAvailable(j, 'client')
from MySQLFactory import MySQLFactory
j.client.mysql=MySQLFactory()