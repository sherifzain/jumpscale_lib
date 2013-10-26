"""
Udev file generation and parsing library
"""


class IDS:

    def id_kernel(self):
        return 'KERNEL'

    def id_kernels(self):
        return 'KERNELS'

    def id_subsystems(self):
        return 'SUBSYSTEMS'

    def id_subsystem(self):
        return 'SUBSYSTEM'

    def id_drivers(self):
        return 'DRIVERS'

    def id_driver(self):
        return 'DRIVER'

    def id_env(self, value):
        return 'ENV{%s}' % value.upper()

    def id_Sattr(self, value):
        return '$attr{%s}' % value

    def id_attr(self, value):
        return 'ATTR{%s}' % value

    def id_attrs(self, value):  # property is reserved word
        return 'ATTRS{%s}' % value

    def id_symlink(self):
        return 'SYMLINK'

    def id_goto(self):
        return 'GOTO'

    def id_run(self):
        return 'RUN'

    def id_tag(self):
        return 'TAG'

    def id_label(self):
        return 'LABEL'

    def id_action(self):
        return 'ACTION'

    def id_group(self):
        return 'GROUP'

    def id_mode(self):
        return 'MODE'

    def id_import(self):
        return 'IMPORT{program}'

    def id_name(self):
        return 'NAME'

    def id_owner(self):
        return 'OWNER'


class COMPS:

    def com_equal(self):
        return "=="

    def com_nonequal(self):
        return "!="

    def com_assignment(self):
        return "="

    def com_addition(self):
        return '+='


class UDEVParser(object):

    class predicate():

        def __init__(self, identity, comparator, value):
            self.identity = identity
            self.comparator = comparator
            self.value = self._escape(value)

        def __str__(self):
            return '%s%s"%s"' % (self.identity, self.comparator, self._escape(self.value))

        def __repr__(self):
            return self.__str__()

        def _escape(self, string):

            if len(string) > 0 and string[0] == "'" and string[-1] == "'":
                return string[1:-1]
            if len(string) > 0 and string[0] == '"' and string[-1] == '"':
                return string[1:-1]
            return string

    class emptypredicate(predicate):

        def __init__(self, value):
            self.identity = ''
            self.comparator = ''
            self.value = self._escape(value)

        def __str__(self):
            return str(self.value)

    class line():

        def __init__(self, predicates):
            """
            create a 'line' (as a line in a text file) from a list of predicates
            """
            if not isinstance(predicates, list):
                raise RuntimeError('Expected a list got %s' % type(predicates))
            self.predicates = predicates

        def __str__(self):
            return str(self.predicates)

        def __repr__(self):
            return self.__str__()

        def add(self, predicate):
            self.predicates.extend(predicate)

        def remove(self, predicate):
            try:
                index = self.predicates.index(predicate)
            except ValueError:
                return False
            self.predicates.pop(index)
            return True

    def __init__(self, udevFile=None, udevList=None):
        _IDS = IDS()
        _COMPS = COMPS()
        # reverse match
        self.IDS = {'KERNEL': _IDS.id_kernel,
                    'KERNELS': _IDS.id_kernels,
                    'SUBSYSTEM': _IDS.id_subsystem,
                    'SUBSYSTEMS': _IDS.id_subsystems,
                    'DRIVER': _IDS.id_driver,
                    'DRIVERS': _IDS.id_drivers,
                    'ACTION': _IDS.id_action,
                    'GOTO': _IDS.id_goto,
                    'RUN': _IDS.id_run,
                    'LABEL': _IDS.id_label,
                    'NAME': _IDS.id_name,
                    'OWNER': _IDS.id_owner,
                    'GROUP': _IDS.id_group,
                    'MODE': _IDS.id_mode,
                    'SYMLINK': _IDS.id_symlink,
                    'IMPORT': _IDS.id_import,
                    'TAG': _IDS.id_tag
                    }
        self.IDSArgs = {'ENV': _IDS.id_env,
                        'ATTR': _IDS.id_attr,
                        'ATTRS': _IDS.id_attrs}
        self.IDVars = {'$attr': _IDS.id_Sattr}

        self.COMP = {'==': _COMPS.com_equal,
                     '=': _COMPS.com_assignment,
                     '!=': _COMPS.com_nonequal,
                     '+=': _COMPS.com_addition}
        if udevFile:
            self.FILEREPR = self._fromFile(udevFile)
        elif udevList:
            self.FILEREPR = udevList
        else:
            pass  # somewhere

    def _fromFile(self, udevFile):
        """
        process a text file (in udev format) into a list of lists of predicates
        """
        _FILEUDEV = []
        for LINE in udevFile:
            if LINE.startswith('#'):
                _FILEUDEV.append([UDEVParser.emptypredicate(LINE.replace('\n', ''))])
            elif len(LINE) == 1 and LINE[0] == '\n':
                _FILEUDEV.append([UDEVParser.emptypredicate(LINE.replace('\n', ''))])
            else:
                res = self._processLINE(LINE)
                if res:
                    _FILEUDEV.append(res)
        return _FILEUDEV

    def _processLINE(self, line):
        """
        process a line of text into a line of predicate objects
        """
        _PREDS = []
        for predicate in line.split(','):
            if predicate != '':
                res = self._processPREDICATE(predicate)
                if res:
                    _PREDS.append(res)
        return _PREDS

    def _processPREDICATE(self, pred):
        """
        transform a predicate string into a predicate object
        """
        ident = None
        com = None
        val = None
        try:
            if ord(pred) < 32:  # line feed: CR, LF
                return None
        except:  # pred is not a single character
            pass
        if pred[0] == ' ':
            pred = pred[1:]
        for _id in self.IDS.keys():
            if pred[:len(_id)] == _id:
                ident = self.IDS[_id]()

        if ident and pred[len(str(ident))] == 'S':
            ident = self.IDS['%sS' % ident]()
        if not ident:
            for _id in self.IDSArgs.keys():
                if pred[:len(_id)] == _id:
                    _idval = pred[pred.find(_id) + len(_id) + 1:pred.find('}')]
                    ident = self.IDSArgs[_id](_idval)
        if not ident:
            raise ValueError('Bad id in predicate %s' % pred)
        pred = pred.replace(str(ident), '')

        for _comp in self.COMP.keys():
            if pred[:len(_comp)] == _comp:
                com = self.COMP[_comp]()
            if com and _comp == '=' and pred[:len(_comp) + 1] == '==':
                com = self.COMP['==']()
        if not com:
            raise ValueError('Bad comparator in predicate %s' % pred)

        pred = pred.replace(str(com), '').replace('"', '')

        for attrS in self.IDVars.keys():

            if pred.startswith(attrS):
                _val = pred.replace(attrS, '')[1:-1].replace('}', '').strip()  # remove trailing whitespace
                val = self.IDVars[attrS](_val)
        if not val:
            val = pred.replace('\n', '').strip()
        return UDEVParser.predicate(ident, com, val)

    def toFile(self):
        out = []
        for line in self.FILEREPR:
            out.append(str(line)[1:-1])
        return '\n'.join(out)

    def __str__(self):
        return self.toFile()


class UDEV:

    """
    udev file generator class
    
    e.g:
    udev = q.<extensionGroup>.<extensionClass>
    udevList = [udev.line([udev.predicate(udev.IDS.id_kernel(), udev.COMPS.com_equal(), 'sd*[!0-9]|sr*'),
                       udev.predicate(udev.IDS.id_subsystems(), udev.COMPS.com_equal(), 'usb'),
                       udev.predicate(udev.IDS.id_drivers(), udev.COMPS.com_equal(), 'usb-storage'), 
                       udev.predicate(udev.IDS.id_env('SIZE'), udev.COMPS.com_assignment(), udev.IDS.id_Sattr('size'))]),
            udev.line([udev.predicate(udev.IDS.id_kernel(), udev.COMPS.com_equal(), '?[!0-9]-[!0-9]'),
                       udev.predicate(udev.IDS.id_subsystems(), udev.COMPS.com_equal(), 'usb'),
                       udev.predicate(udev.IDS.id_drivers(), udev.COMPS.com_equal(), 'usb'), 
                       udev.predicate(udev.IDS.id_env('ID_MODEL'), udev.COMPS.com_assignment(), udev.IDS.id_Sattr('model')),
                       udev.predicate(udev.IDS.id_env('ID_SERIAL_SHORT'), udev.COMPS.com_assignment(), udev.IDS.id_Sattr('serial'))])]

    udev.saveFile(udevList, '99-persistent-storage-usb.rules')
    
    OUTPUT: (written to file)

    KERNEL=="sd*[!0-9]|sr*", SUBSYSTEMS=="usb", DRIVERS=="usb-storage", ENV{SIZE}="$attr{size}"
    KERNEL=="?[!0-9]-[!0-9]", SUBSYSTEMS=="usb", DRIVERS=="usb", ENV{ID_MODEL}="$attr{model}", ENV{ID_SERIAL_SHORT}="$attr{serial}"
    """

    def __init__(self):
        """
        @params filename: name of the file to be read or saved to
        """
        self.IDS = IDS()
        self.COMPS = COMPS()
        self.PARSER = UDEVParser()
        self.predicate = self.PARSER.predicate
        self.line = self.PARSER.line

    def fileToList(self, filename):
        self.filename = filename
        with open(self.filename, 'r') as udevfile:
            udevContent = udevfile.readlines()
        return self.PARSER._fromFile(udevContent)

    def listToFile(self, List):
        self.PARSER.FILEREPR = List
        return self.PARSER.toFile()

    def saveFile(self, List, filename):
        with open(filename, 'w') as udevfile:
            udevfile.write(self.listToFile(List))

"""
    def tests(self):
        udev = UDEV()
        udevList = [udev.line([udev.predicate(udev.IDS.id_kernel(), udev.COMPS.com_equal(), 'sd*[!0-9]|sr*'),
                               udev.predicate(udev.IDS.id_subsystems(), udev.COMPS.com_equal(), 'usb'),
                               udev.predicate(udev.IDS.id_drivers(), udev.COMPS.com_equal(), 'usb-storage'), 
                               udev.predicate(udev.IDS.id_env('SIZE'), udev.COMPS.com_assignment(), udev.IDS.id_Sattr('size'))]),
                    udev.line([udev.predicate(udev.IDS.id_kernel(), udev.COMPS.com_equal(), '?[!0-9]-[!0-9]'),
                               udev.predicate(udev.IDS.id_subsystems(), udev.COMPS.com_equal(), 'usb'),
                               udev.predicate(udev.IDS.id_drivers(), udev.COMPS.com_equal(), 'usb'), 
                               udev.predicate(udev.IDS.id_env('ID_MODEL'), udev.COMPS.com_assignment(), udev.IDS.id_Sattr('model')),
                               udev.predicate(udev.IDS.id_env('ID_SERIAL_SHORT'), udev.COMPS.com_assignment(), udev.IDS.id_Sattr('serial'))])
                    ]
        
        udev.saveFile(udevList, '99-persistent-storage-usb.rules')
        
        udev = UDEV()
        print udev.fileToList('rules.udev')
        udev = UDEV()
        
        print udev.listToFile(udev.fileToList('rules.udev'))
        print udev.listToFile(udevList)
         
        assert udev.fileToList('rules.udev')[0][0].identity == udevList[0].predicates[0].identity, 'Incorrect format'
        
        print udev.fileToList('rules.udev')[0] # line
        print udevList[0] #line
        
        print '*'*20
        print udev.fileToList('rules.udev')[0][0] # predicate
        print udevList[0].predicates[0] #predicate
        print '*'*20
        print udev.fileToList('rules.udev')
        print udevList
        print '*'*20
        assert udev.listToFile(udev.fileToList('rules.udev')) == udev.listToFile(udevList), 'Incorrect parsing'   
        
UDEV().tests()
"""
