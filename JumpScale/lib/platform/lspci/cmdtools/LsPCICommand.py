# <License type="Sun Cloud BSD" version="2.2">
#
# Copyright (c) 2005-2009, Sun Microsystems, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# 3. Neither the name Sun Microsystems, Inc. nor the names of other
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SUN MICROSYSTEMS, INC. "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SUN MICROSYSTEMS, INC. OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# </License>

from JumpScale import j
from JumpScale.core.baseclasses.CommandWrapper import CommandWrapper


class LsPCICommand(CommandWrapper):

    _listComponents = "lspci -m"

    def listComponents(self):
        """
        List available PCI components
        """
        return self._executeCommand(LsPCICommand._listComponents)

    def _executeCommand(self, command):
        """
        Execute given command.
        Raise Exception if exit code not equal zero

        @param command: command to execute
        """
        j.logger.log("Executing command : %s" % command, 3)
        # This check on the platform type is not supposed to happen, but it is implemented as a temp solution
        # beside the dummpy vapps to solve the dependency per platform problem
        if not j.system.platformtype.isLinux():
            raise RuntimeError("Command [%s] not supported on [%s]" % (command, j.system.platformtype))
        exitcode, output = j.system.process.execute('%s 2>&1' % command, outputToStdout=False, dieOnNonZeroExitCode=False)
        if exitcode:
            raise RuntimeError('Command: %(command)s failed with exitcode %(exitcode)s. Output: %(output)s' %
                               {'command': command, 'exitcode': exitcode, 'output': str(output)})
        return output
