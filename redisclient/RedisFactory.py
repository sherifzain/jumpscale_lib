
import redis
from RedisQueue import RedisQueue
from JumpScale import j


class RedisClient():

    def __init__(self, host, port, db=0, key=""):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self.key = ""
        self.queues = {}

    def getQueue(self, name):
        if name in self.queues:
            return self.queues[name]
        self.queues[name] = RedisQueue(name, self)
        return self.queues[name]

    def ping(self):
        return self.redis.ping()


class RedisFactory():

    def __init__(self):
        self.redisclients = {}

    def get(self, host, port, db=0, key=""):
        port = int(port)
        key = "%s_%s_%s"
        if key in self.redisclients:
            client, key2 = self.redisclients[key]
            if key2 != key:
                self.redisclients[key] = RedisClient(host, port, db, key), key
        else:
            self.redisclients[key] = RedisClient(host, port, db, key), key
        return self.redisclients[key][0]

    def ping(self, host, port, db=0, key=""):
        cl = self.get(host, port, db, key)
        try:
            cl.ping()
        except:
            pass
        try:
            return cl.ping()
        except Exception as e:
            print e
            from JumpScale.core.Shell import ipshellDebug, ipshell
            print "DEBUG NOW ping"
            # ipshell()

            return False

        return True
