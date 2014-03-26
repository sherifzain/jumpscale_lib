__author__ = 'delandtj'
"""

"""
class Osd(object):
    def __init__(self,definition,volume,fstype="btrfs",log=None):
        self.definition = definition
        self.fstype = fstype
        self.log = log

    def prepconfig(self,):
        pass

    def activateOsd(self,definition):
        placeconfig(definition)
        makefs(definition)
        register(definition)
        registerOS(definition)
        os_start(definition)

if __name__ == "__main_":
    pass