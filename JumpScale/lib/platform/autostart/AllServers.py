from JumpScale import j, i


class AllServers():

    def start(self):
        configItems = i.config.autostart.list()
        for configItem in configItems:
            config = i.config.autostart.getConfig(configItem)
            self._executeCommands(item=config,
                                  actiontype='start')

    def stop(self):
        configItems = i.config.autostop.list()
        for configItem in configItems:
            config = i.config.autostop.getConfig(configItem)
            self._executeCommands(item=config,
                                  actiontype='stop')

    def _executeCommands(self, item, actiontype):
        cmd = item['command']
        try:
            eval(cmd)
        except Exception as e:
            if actiontype == 'stop':
                j.logger.log("Failed to execute command '%s'.\nDetails:\n" % cmd)
            else:
                q.eventhandler.raiseError("Failed to execute command '%s'.\nDetails:\n%s" % (cmd, e.message))
