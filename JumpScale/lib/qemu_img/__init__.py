from JumpScale import j
j.base.loader.makeAvailable(j, 'system.platform')
from qemu_img import QemuImg
j.system.platform.qemu_img = QemuImg()

