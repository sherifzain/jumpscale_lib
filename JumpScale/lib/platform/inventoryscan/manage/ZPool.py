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
from JumpScale.core.baseclasses.CMDBSubObject import CMDBSubObject


class ZPool(CMDBSubObject):

    name = j.basetype.string(doc='Zpool name', allow_none=False)
    CAP = j.basetype.string(doc='Zpool capacity percentage', allow_none=False)
    availableSize = j.basetype.string(doc='Size of the available storage', allow_none=False)
    size = j.basetype.string(doc='Zpool overall size', allow_none=False)
    used = j.basetype.string(doc='Size of the used storage', allow_none=False)
    health = j.basetype.string(doc='Zpool health,e.g ONLINE, OFFLINE', allow_none=False)
    mirrors = j.basetype.list(doc='List of available mirrors, their status and disks', allow_none=False, default=list())
    disks = j.basetype.list(doc='List of all available disks, and their status', allow_none=False, default=list())
    errors = j.basetype.string(doc='Zpool errors as returned by get status', allow_none=False)

    def __repr__(self):
        return "name: %(name)s, CAP: %(CAP)s, availableSize: %(availablesize)s, Used: %(used)s, size: %(size)s, Health: %(health)s" % {'name': self.name, 'CAP': self.CAP, 'availablesize': self.availableSize, 'used': self.used, 'size': self.size, 'health': self.health}
