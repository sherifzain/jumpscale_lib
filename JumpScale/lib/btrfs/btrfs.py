from JumpScale import j
import re

BASECMD = "btrfs"

KB = 1024
MB = KB * 1024
GB = MB * 1024
TB = GB * 1024

FACTOR = {None: 1,
          'KB': KB,
          'MB': MB,
          'GB': GB,
          'TB': TB}

class BtrfsExtension(object):
    
    def __init__(self):
        self.__conspattern = re.compile("^(?P<key>[^:]+): total=(?P<total>[^,]+), used=(?P<used>.+)$", re.MULTILINE)
        self.__listpattern = re.compile("^ID (?P<id>\d+).+?path (?P<name>.+)$", re.MULTILINE)
        
    def __btrfs(self, command, action, *args):
        cmd = "%s %s %s %s" % (BASECMD, command, action, " ".join(map(lambda a: '"%s"' % a, args)))
        code, out, err = j.system.process.run(cmd, stopOnError=False)
        
        if code:
            raise RuntimeError(err)
        
        return out


    def snapshotReadOnlyCreate(self, path, dest):
        """
        Create a readonly snapshot 
        """
        self.__btrfs("subvolume", "snapshot -r", path, dest)
        
    
    def subvolumeCreate(self, path, name):
        """
        Create a subvolume in <dest> (or the current directory if not passed).
        """
        self.__btrfs("subvolume", 'create', j.system.fs.joinPaths(path, name))

    
    def subvolumeDelete(self, path, name):
        """
        Delete the subvolume <name>.
        """
        self.__btrfs("subvolume", "delete", j.system.fs.joinPaths(path, name))
    
    def subvolumeList(self, path):
        """
        List the snapshot/subvolume of a filesystem.
        """
        out = self.__btrfs("subvolume", "list", path)
        result = []
        for m in self.__listpattern.finditer(out):
            result.append(m.groupdict())
        return result
    
    def deviceAdd(self, path, dev):
        """
        Add a device to a filesystem.
        """
        self.__btrfs("device", 'add', dev, path)
    
    def deviceDelete(self, dev, path):
        """
        Remove a device from a filesystem.
        """
        self.__btrfs("device", 'delete', dev, path)
    
    def __consumption2kb(self, word):
        m = re.match("(\d+.\d+)(\D{2})?", word)
        if not m:
            raise ValueError("Invalid input '%s' should be in the form of 0.00XX" % word)
        value = float(m.group(1)) * FACTOR[m.group(2)]
        return value / 1024 #in KB
    
    def getSpaceUsage(self, path):
        out = self.__btrfs("filesystem", "df", path)
        result = {}
        for m in self.__conspattern.finditer(out):
            cons = m.groupdict()
            key = cons['key'].lower()
            key = key.replace(", ", "-")
            values = {'total': self.__consumption2kb(cons['total']),
                      'used': self.__consumption2kb(cons['used'])}
            result[key] = values
            
        return result