import re
from OpenWizzy import o
from OpenWizzy.core.baseclasses import BaseEnumeration
from LogRotateOptions import LogRotateTime, LogRotateSize

_LOGROTATE_CONFIG_PATH = '/etc/logrotate.d/'

class LogRotateException(Exception):
    pass

class Services(object):
    def __init__(self):
        '''
        instantiates a new service
        '''
        self._services = dict()

    def __getitem__(self, key):
        '''
        Returns a service

        @param key: service name
        @type key:  string

        @return:    The specified service

        @raise LogRotateException: if service does not exist
        '''
        service = self._services.get(key)
        #if service is not yet loaded
        #try to load service.
        if not service:
            service = self._services[key] = ServiceLogConfig(key)
        return service

    def __contains__(self, service):
        '''
        Checks if a service is loaded

        @param service: service name
        @type service:  string

        @return:        True if service is loaded, false otherwise.
        @rtype:         boolean
        '''
        return service in self._services

    def _remove(self, service):
        '''
        Removes a service from the list of loaded services.

        @param key: service name
        @type key:  string
        '''
        if service in self._services:
            self._services.pop(service)

    def _save(self):
        '''
        Saves all loaded services
        '''
        map(lambda service: service.save(), self._services.values())

class ServiceLogConfig(object):
    '''
    Represents an instance of logrotate.d service
    '''
    def __init__(self, service):
        '''
        instantiates a new logrotate.d service

        @param service: service name
        @type service:  string
        '''
        self._service        = service
        self.sections        = dict()
        self._logCfgFilePath = o.system.fs.joinPaths(_LOGROTATE_CONFIG_PATH, service)

        o.logger.log('loading logrotate config file %s'%self._logCfgFilePath)
        if not o.system.fs.isFile(self._logCfgFilePath):
            raise LogRotateException('%s service does not exist'%service)

        self._editor = o.codetools.getTextFileEditor(self._logCfgFilePath)
        self._loadLogConfigSections()

    def _loadLogConfigSections(self):
        '''
        Creates a section objects for the list of logPaths specfieid in arguments

        Note: a log Path isn't necessary identical to a section header, since multiple log paths can share a common configuration section.
        An object is created for each path specified, assuming that those files are intended to have a separate configuration section each
        '''
        self.sections = dict()
        self.content  = self._editor.content
        regex         = '(.*\w.*)\s*{([\w\W\s]*?)}$'

        #parse sections
        for match in re.finditer(regex, self.content, re.MULTILINE):
            self.sections[match.groups()[0]] = LogConfigSection(self, match.groups()[0], match.groups()[1], self.content[match.start():match.end()])

    def addSection(self, logPath):
        '''
        Adds a new config section to this service

        @param logPath: The config section header(i.e. the log file path)
        @type logPath:  string

        @rtype:         LogConfigSection
        '''

        if self.sections.has_key(logPath):
            return self.sections[logPath]

        section                   = LogConfigSection(self._service, logPath)
        section._serviceLogConfig = self #to have access to the editor
        self.sections[logPath]    = section
        section.save()
        return section

    def removeSection(self, logConfigSection):
        '''
        Removes a config section from this service

        @param logConfigSection: The config section header (i.e. the log file path)
        @type logConfigSection:  string
        '''
        section = self.sections[logConfigSection]
        self.sections.pop(logConfigSection)
        self._deleteLogConfigSection(section)

    def save(self):
        '''
        Saves this service
        '''
        map(lambda sec: sec.save(), self.sections.values())
        self._editor.save()

    def listSections(self):
        '''
        Lists all sections in this service

        @return: A list of the sections in this service
        @rtype:  list
        '''
        return [section._dump() for section in self.sections.values()]

    def listSectionKeys(self):
        '''
        Lists all sections keys in this service
        @return: A list of the sections keys in this service
        @rtype:  list
        '''
        return self.sections.keys()

    def _addLogConfigSection(self, logConfigSection):
        self._editor.content += '\n%s'%logConfigSection._dump()
        self._editor.save()

    def _updateLogConfigSection(self, logConfigSection):
        self._editor.content = self._editor.content.replace(logConfigSection._originalSection, logConfigSection._dump())
        self._editor.save()

    def _deleteLogConfigSection(self, logConfigSection):
        self._editor.content = self._editor.content.replace(logConfigSection._originalSection, '')
        self._editor.save()

class LogConfigSection(object):
    '''
    Represents a config section in a logrotate service
    '''
    _OPTION_GROUPS = {str(o.enumerators.LogRotateGroups.COPY)          : [str(o.enumerators.LogRotateOptions.COPY),
                                                                          str(o.enumerators.LogRotateOptions.NOCOPY)],
                      str(o.enumerators.LogRotateGroups.CREATE)        : [str(o.enumerators.LogRotateOptions.CREATE),
                                                                          str(o.enumerators.LogRotateOptions.NOCREATE)],
                      str(o.enumerators.LogRotateGroups.COPYTRUNCATE)  : [str(o.enumerators.LogRotateOptions.COPYTRUNCATE),
                                                                          str(o.enumerators.LogRotateOptions.NOCOPYTRUNCATE)],
                      str(o.enumerators.LogRotateGroups.COMPRESS)      : [str(o.enumerators.LogRotateOptions.COMPRESS),
                                                                          str(o.enumerators.LogRotateOptions.NOCOMPRESS)], #compress | nocompress
                      str(o.enumerators.LogRotateGroups.DELAYCOMPRESS) : [str(o.enumerators.LogRotateOptions.DELAYCOMPRESS)],
                      str(o.enumerators.LogRotateGroups.SIZE)          : [str(o.enumerators.LogRotateOptions.SIZE)], #size <size>[K|M]
                      str(o.enumerators.LogRotateGroups.TIME)          : [str(o.enumerators.LogRotateOptions.DAILY),
                                                                          str(o.enumerators.LogRotateOptions.WEEKLY),
                                                                          str(o.enumerators.LogRotateOptions.MONTHLY)], #daily|weekly|monthly
                      str(o.enumerators.LogRotateGroups.ROTATE)        : [str(o.enumerators.LogRotateOptions.ROTATE)], #rotate <count>
                      str(o.enumerators.LogRotateGroups.ROTATIONDIR)   : [str(o.enumerators.LogRotateOptions.OLDDIR),
                                                                          str(o.enumerators.LogRotateOptions.NOOLDDIR)], #olddir <dir>|noolddir
                      str(o.enumerators.LogRotateGroups.MAIL)          : [str(o.enumerators.LogRotateOptions.MAIL),
                                                                          str(o.enumerators.LogRotateOptions.NOMAIL),
                                                                          str(o.enumerators.LogRotateOptions.MAILFIRST),
                                                                          str(o.enumerators.LogRotateOptions.MAILLAST)],
                      str(o.enumerators.LogRotateGroups.SHAREDSCRIPTS) : [str(o.enumerators.LogRotateOptions.SHAREDSCRIPTS)],
                      str('unknown')                                   : []}

    def _categorizeOptions(self, optionsList):
        def categorize(option):
            for k, v in self._OPTION_GROUPS.iteritems():
                if option[0] in v: return k
            return 'unknown'

        groups = map(categorize, optionsList)
        return dict(zip(groups, optionsList))

    def __init__(self, service, logPath, options=None, section=None):
        '''
        instantiates a new config section
    
        @param service: The service that owns this section
        @type service:  string
        '''
        self._serviceLogConfig      = service
        self._originalSection       = section if section else ''
        self._originalOptions       = self._options = options if options else ''
        self._originalSectionHeader = self._sectionHeader = self._logPath = logPath #create a separate new section for this logPath
        self._new                   = True if not options else False

        #find remove and remove all scripts from options
        scripts = []
        script  = re.search('(postrotate|prerotate|firstaction|lastaction)([\w\W\s]*?)(endscript)', self._options)
        while script:
            scripts.append(script)
            self._options = self._options[0:script.start()] + self._options[script.end():]
            script = re.search('(postrotate|prerotate|firstaction|lastaction)([\w\W\s]*?)(endscript)', self._options)

        #split each option into a list of option:args then categorize options
        self._options = self._categorizeOptions(map(lambda s: s.strip().split(' ', 1), self._options.split('\n')))

        #add script to options dictionary
        for script in scripts:
            self._options[script.groups()[0]] =  list(script.groups())

        self._options["missingok"] = ["missingok"]

    def setCompressMode(self, compress=True, delayed=False):
        '''
        Sets the compression mode of this section

        @param compress: True enables the compression, false disables the compression
        @type compress:  boolean
        '''
        self._options[str(o.enumerators.LogRotateGroups.COMPRESS)] = [str(o.enumerators.LogRotateOptions.COMPRESS)] if compress else [str(o.enumerators.LogRotateOptions.NOCOMPRESS)]
        if compress and delayed:
            self._options[str(o.enumerators.LogRotateGroups.DELAYCOMPRESS)] = [str(o.enumerators.LogRotateOptions.DELAYCOMPRESS)]
        else:
            self._options.pop(str(o.enumerators.LogRotateGroups.DELAYCOMPRESS), None)

    def setCopy(self, copy=True):
        '''
        Sets the copy mode of this section

        @param copy: sets the copy option if True, else sets nocopy
        @type copy:  boolean
        '''
        self._options[str(o.enumerators.LogRotateGroups.COPY)] = [str(o.enumerators.LogRotateOptions.COPY) if copy else str(o.enumerators.LogRotateOptions.NOCOPY)]

    def setCopyTruncate(self, copytruncate=True):
        '''
        Sets the copytruncate mode of this section

        @param copytruncate: sets the copytruncate option if True, else sets nocopytruncate
        @type copytruncate:  boolean
        '''
        self._options[str(o.enumerators.LogRotateGroups.COPYTRUNCATE)] = [str(o.enumerators.LogRotateOptions.COPYTRUNCATE) if copytruncate else str(o.enumerators.LogRotateOptions.NOCOPYTRUNCATE)]

    def setCreate(self, create=True):
        '''
        Sets the create mode of this section

        @param create: sets the create option if True, else sets nocreate
        @type create:  boolean
        '''
        self._options[str(o.enumerators.LogRotateGroups.CREATE)] = [str(o.enumerators.LogRotateOptions.CREATE) if create else str(o.enumerators.LogRotateOptions.NOCREATE)]

    def setMaximumSize(self, size, sizeIdentifier=LogRotateSize.K):
        '''
        Sets the maximum size of the log file.
        Only the form 'size <size>[K|M]' is supported.

        @param sizeIdentifier: The size specifier.
        @type sizeIdentifier:  LogRotateSize.
        '''
        self._options[str(o.enumerators.LogRotateGroups.SIZE)] = [str(o.enumerators.LogRotateOptions.SIZE), '%d%s'%(size, sizeIdentifier)]

    def setRotationDirectory(self, directory=None):
        '''
        Sets the rotation directory of this log config section.

        @param directory: the rotation directory
        @type directory:  string
        '''
        self._options[str(o.enumerators.LogRotateGroups.ROTATIONDIR)] = [str(o.enumerators.LogRotateOptions.OLDDIR), directory] if directory else [str(o.enumerators.LogRotateOptions.NOOLDDIR)]

    def setRotationCount(self , count):
        '''
        Sets the number of times to rotate the log files in one day

        @param count: the rotate count
        @type count:  int
        '''
        self._options[str(o.enumerators.LogRotateGroups.ROTATE)] = [str(o.enumerators.LogRotateOptions.ROTATE), str(count)]

    def setRotationTime(self, time=LogRotateTime.DAILY):
        '''
        Sets the time interval of the log rotation for this config section.

        @param time: The time interval of the log rotation, DAILY, WEEKLY etc..
        @type time:  LogRotateTime
        '''
        self._options[str(o.enumerators.LogRotateGroups.TIME)] = [str(time)]

    def setMail(self, mail, addr = None):
        '''
        Sets the mail option of this log config section MAIL, NOMAIL etc...

        @param mail: The mail option
        @type mail:  LogRotateMail

        @param addr: email address
        @type addr:  string
        '''
        self._options[str(o.enumerators.LogRotateGroups.MAIL)] = [str(mail), addr] if addr else [str(mail),]

    def setScript(self, scriptType, script):
        '''
        Adds or removes a script from a section.

        @param scriptType: postrotate, prerotate etc...
        @type scriptType:  LogRotateScript

        @param script:     the script code
        @type script:      string
        '''
        key = str(scriptType)
        self._options[key] = [key, '\n'+script, '\nendscript']

    def setSharedScripts(self, shared):
        '''
        Enable/Disable sharedscripts

        @param shared: if True enable sharedscripts else disable sharedscripts 
        @type shared:  boolean
        '''
        if shared:
            self._options[str(o.enumerators.LogRotateGroups.SHAREDSCRIPTS)] = [str(o.enumerators.LogRotateOptions.SHAREDSCRIPTS)]
        else:
            self._options.pop(str(o.enumerators.LogRotateGroups.SHAREDSCRIPTS), None)

    def removeOption(self, key):
        '''
        Removes an option from the config section if it exists.

        @param key: option key to be removed
        @type key:  LogRotateGroups
        '''
        if o.enumerators.LogRotateGroups.check(key):
            self._options.pop(str(key), None)
        else:
            raise LogRotateException('not a valid option key %s'%key)

    def save(self):
        '''
        Saves this config section
        '''
        if self._new:
            self._serviceLogConfig._addLogConfigSection(self)
        else:
            self._serviceLogConfig._updateLogConfigSection(self)

        self._originalOptions = self._dumpOptions()
        self._originalSection = self._dump()
        self._new = False

    def _dump(self):
        return '%s\n{%s}\n'%(self._sectionHeader, self._dumpOptions())

    def _dumpOptions(self):
        return '\n%s\n'%'\n'.join(map(lambda x: ' '.join(x), self._options.values()))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return 'original : %s\nmodified : %s'%(self._originalSection, self._dump())

_services = Services()

class LogRotate(object):

    def save(self):
        '''
        Saves all services.
        '''
        global _services
        _services._save()
        #clear services 
        _services = Services()

    def addService(self, service):
        '''
        Adds a new service to logrotate.d

        @param service:   service name
        @type service:    string

        @raise Exception: if service already exists
        '''
        global _services
        serviceConfigPath = o.system.fs.joinPaths(_LOGROTATE_CONFIG_PATH, service)
        if o.system.fs.exists(serviceConfigPath):
            raise Exception('logrotate config file %s already exists for service %s'%(serviceConfigPath, service))

        o.system.fs.createEmptyFile(serviceConfigPath)
        return _services[service]

    def removeService(self, service):
        '''
        Removes a service from logrotate.d

        @param service: service name
        @type service:  string
        '''
        #get service path
        global _services
        serviceConfigPath = o.system.fs.joinPaths(_LOGROTATE_CONFIG_PATH, service)
        #remove service from file system
        if o.system.fs.exists(serviceConfigPath):
            o.system.fs.removeFile(o.system.fs.joinPaths(_LOGROTATE_CONFIG_PATH, service))
        #also remove service from the services dictionary
        _services._remove(service)

    def listServices(self):
        '''
        Lists all services in logrotate.d

        @return: A list of services in logrotate.d
        @rtype:  list
        '''
        return [o.system.fs.getBaseName(service) for service in o.system.fs.walk(_LOGROTATE_CONFIG_PATH)]

    def configure(self, configurationparams):
        """
        Configures logrotate
        configurationparams example = 
        { 'monitoring_logs': [{'/opt/qbase3/var/log/monitoring/monitoring_archive.tgz':{'mode'      : ['nocopy', 'nocreate'],
                                                                                        'time'      : o.enumerators.LogRotateTime.DAILY,
                                                                                        'rotate'    : 7,
                                                                                        'size'      : [0, o.enumerators.LogRotateSize.K],
                                                                                        'compress'  : False}},
                              {'/opt/qbase3/var/log/monitoring/*.log':{'mode'          : ['nocopy', 'nocreate'],
                                                                       'time'          : o.enumerators.LogRotateTime.DAILY,
                                                                       'rotate'        : 0,
                                                                       'size'          : [0, o.enumerators.LogRotateSize.K],
                                                                       'compress'      : False,
                                                                       'prerotate'     : "tar czf /opt/qbase3/var/log/monitoring/monitoring_archive.tgz /opt/qbase3/var/log/monitoring/*.log",
                                                                       'sharedScript'  : True}}],}"""
        global _services
        for key, value in configurationparams.iteritems():
            if not key in self.listServices():
                o.logger.log("Logrotate - Initialise logrotate: Adding service: %s"%key, 1)
                self.addService(key)
            service = _services[key]
            for info in value:
                file = info.keys()[0]
                config = info[file]
                if not file in service.listSections():
                    o.logger.log("Logrotate - Initialise logrotate: Adding section: %s"%file, 1)
                    service.addSection(file)
                section = service.sections[file]
                # Set mode
                for mode in config['mode']:
                    if mode == 'copy':
                        section.setCopy(True)
                    if mode == 'nocopy':
                        section.setCopy(False)
                    if mode == 'copytruncate':
                        section.setCopyTruncate(True)
                    if mode == 'create':
                        section.setCreate(True)
                    if mode == 'nocreate':
                        section.setCreate(False)
                # If needed enable compression
                if config['compress']:
                    o.logger.log("Logrotate - Initialise logrotate: enable compression", 1)
                    section.setCompressMode(True)
                # set time interval
                section.setRotationTime(config['time'])
                # set maximum size
                section.setMaximumSize(config['size'][0], config['size'][1])
                # set rotate count
                section.setRotationCount(config['rotate'])
                # Set pre/post rotate script if a script needs to be set
                keys = config.keys()
                if 'sharedScript' in keys:
                    o.logger.log("Logrotate - Initialise logrotate: enable shared scripts", 1)
                    section.setSharedScripts(config['sharedScript'])
                if 'prerotate' in keys:
                    o.logger.log("Logrotate - Initialise logrotate: adding prerotate script: %s"%config['prerotate'], 1)
                    section.setScript(o.enumerators.LogRotateScript.PREROTATE, config['prerotate'])
                if 'postrotate' in keys:
                    o.logger.log("Logrotate - Initialise logrotate: adding postrotate script: %s"%config['postrotate'], 1)
                    section.setScript(o.enumerators.LogRotateScript.POSTROTATE, config['postrotate'])
        self.save()
