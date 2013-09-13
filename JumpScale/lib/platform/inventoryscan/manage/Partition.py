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
from PartitionRaid import PartitionRaid


class Partition(CMDBSubObject):

    def __init__(self, type, number, start, end, size, mountpoint, used, label='', flag='', devices=''):
        self.type = type
        self.number = int(number)
        self.start = start
        self.end = end
        self.size = int(size)
        self.used = float(used)
        self.mountpoint = mountpoint
        self.label = label
        self.flag = flag

    type = j.basetype.string(doc='partition type', allow_none=False)
    flag = j.basetype.string(doc='partition flag', allow_none=False)
    number = j.basetype.integer(doc='partition number', allow_none=False)
    start = j.basetype.string(doc='partition start location', allow_none=False)
    end = j.basetype.string(doc='partition end location', allow_none=False)
    size = j.basetype.integer(doc='partition size in MB', allow_none=False)
    label = j.basetype.string(doc='partition label', allow_none=False)
    used = j.basetype.float(doc='partition used size in GB', allow_none=False)
    mountpoint = j.basetype.string(doc='partition mountpoint', allow_none=False)
    raid = j.basetype.object(PartitionRaid, doc='raid information', allow_none=True, flag_dirty=True, default=None)

    def __repr__(self):
        return "type: %s, label: %s, flag: %s, number: %s, start: %s, end: %s, size: %sMB" % (self.type, self.label, self.flag, self.number, self.start, self.end, self.size)
