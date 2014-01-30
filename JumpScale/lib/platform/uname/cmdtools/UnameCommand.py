
from JumpScale import j
from JumpScale.core.baseclasses.CommandWrapper import CommandWrapper


class UnameCommand(CommandWrapper):

    _UNAME_GET_ALL = "uname -a"

    def getKernelName(self):
        """
        Get System Kernel name
        """
        return self._executeCommand(UnameCommand._UNAME_GET_ALL)

    def _executeCommand(self, command):
        """
        Execute given command.
        Raise Exception if exitcode not equal zero

        @param command: command to execute
        """
        # This check on the platform type is not supposed to happen, but it is implemented as a temp solution
        # beside the dummpy vapps to solve the dependency per platform problem
        if not j.system.platformtype.isUnix():
            raise RuntimeError("Command [%s] not supported on [%s]" % (command, j.system.platformtype))
        exitcode, output = j.system.process.execute('%s 2>&1' % command, outputToStdout=False, dieOnNonZeroExitCode=False)
        if exitcode != 0:
            raise RuntimeError('Command: %(command)s failed with exitcode %(exitcode)s. Output: %(output)s' %
                               {'command': command, 'exitcode': exitcode, 'output': str(output)})
        return output
