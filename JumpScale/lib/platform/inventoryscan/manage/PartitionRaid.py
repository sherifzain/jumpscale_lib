# <License type="Aserver BSD" version="2.2">
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
from JumpScale.core.baseclasses.CMDBSubObject import CMDBSubObject


class PartitionRaid(CMDBSubObject):

    def __init__(self, level, state, devices, activeDevices, failedDevices, totalDevices, raidDevices, spareDevices, backendsize):
        self.level = level
        self.state = state
        self.devices = devices
        self.activeDevices = int(activeDevices)
        self.failedDevices = int(failedDevices)
        self.totalDevices = int(totalDevices)
        self.raidDevices = int(raidDevices)
        self.spareDevices = int(spareDevices)
        self.backendsize = int(backendsize)

    activeDevices = j.basetype.integer(doc='active devices', allow_none=False)
    failedDevices = j.basetype.integer(doc='failed devices', allow_none=False)
    totalDevices = j.basetype.integer(doc='total devices', allow_none=False)
    raidDevices = j.basetype.integer(doc='raid devices', allow_none=False)
    spareDevices = j.basetype.integer(doc='spare devices', allow_none=False)
    level = j.basetype.string(doc='raid level', allow_none=False)
    state = j.basetype.string(doc='raid state', allow_none=False)
    devices = j.basetype.dictionary(doc='raid devices overview', allow_none=False)
    backendsize = j.basetype.integer(doc='total size of physical used partitions', allow_none=False)

    def __repr__(self):
        return "activeDevices: %s, failedDevices: %s, totalDevices: %s, raidDevices: %s, spareDevices: %s, level: %s, state: %s" % (self.activeDevices,
                                                                                                                                    self.failedDevices,
                                                                                                                                    self.totalDevices,
                                                                                                                                    self.raidDevices,
                                                                                                                                    self.spareDevices,
                                                                                                                                    self.level,
                                                                                                                                    self.state)
