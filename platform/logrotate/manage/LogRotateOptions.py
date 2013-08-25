from JumpScale import j
from JumpScale.core.baseclasses import BaseEnumeration


class LogRotateMail(BaseEnumeration):

    @classmethod
    def _initItems(cls):
        cls.registerItem('mail')
        cls.registerItem('mailfirst')
        cls.registerItem('maillast')
        cls.finishItemRegistration()


class LogRotateTime(BaseEnumeration):

    @classmethod
    def _initItems(cls):
        cls.registerItem('daily')
        cls.registerItem('weekly')
        cls.registerItem('monthly')
        cls.finishItemRegistration()


class LogRotateSize(BaseEnumeration):

    @classmethod
    def _initItems(cls):
        cls.registerItem('k')
        cls.registerItem('M')
        cls.registerItem('G')
        cls.finishItemRegistration()


class LogRotateScript(BaseEnumeration):

    @classmethod
    def _initItems(cls):
        cls.registerItem('postrotate')
        cls.registerItem('prerotate')
        cls.registerItem('firstaction')
        cls.registerItem('lastaction')
        cls.finishItemRegistration()


class LogRotateOptions(BaseEnumeration):

    @classmethod
    def _initItems(cls):
        # copy
        cls.registerItem('copy')
        cls.registerItem('nocopy')
        # truncate
        cls.registerItem('copytruncate')
        cls.registerItem('nocopytruncate')
        # creation
        cls.registerItem('create')
        cls.registerItem('nocreate')
        # compression
        cls.registerItem('compress')
        cls.registerItem('nocompress')
        cls.registerItem('delaycompress')
        # size
        cls.registerItem('size')
        # rotation time
        cls.registerItem('daily')
        cls.registerItem('weekly')
        cls.registerItem('monthly')
        # rotation count
        cls.registerItem('rotate')
        # rotation dir
        cls.registerItem('olddir')
        cls.registerItem('noolddir')
        cls.registerItem('rotationdir')
        # mail
        cls.registerItem('mail')
        cls.registerItem('nomail')
        cls.registerItem('mailfirst')
        cls.registerItem('maillast')
        cls.registerItem('sharedscripts')
        cls.finishItemRegistration()


class LogRotateGroups(BaseEnumeration):

    @classmethod
    def _initItems(cls):
        cls.registerItem('copy')
        cls.registerItem('create')
        cls.registerItem('copytruncate')
        cls.registerItem('compress')
        cls.registerItem('delaycompress')
        cls.registerItem('size')
        cls.registerItem('time')
        cls.registerItem('rotate')
        cls.registerItem('rotationdir')
        cls.registerItem('mail')
        cls.registerItem('sharedscripts')
        cls.registerItem('postrotate')
        cls.registerItem('prerotate')
        cls.registerItem('firstaction')
        cls.registerItem('lastaction')
        cls.finishItemRegistration()
