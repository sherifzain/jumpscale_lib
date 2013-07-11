from OpenWizzy import o

class LogRotate(object):
    def start(self):
        o.system.process.execute('logrotate /etc/logrotate.d/*')

    def stop(self):
        pass

    def restart(self):
        pass

    def status(self):
        pass
