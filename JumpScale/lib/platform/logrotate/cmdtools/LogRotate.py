from JumpScale import j


class LogRotate(object):

    def start(self):
        j.system.process.execute('logrotate /etc/logrotate.d/*')

    def stop(self):
        pass

    def restart(self):
        pass

    def status(self):
        pass
