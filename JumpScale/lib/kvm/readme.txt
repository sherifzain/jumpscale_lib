* Check to which networks you like to connect:
virsh net-list 
e.g public, management, privategw
* Check volume path

Example xml:
<domain type='kvm'>
  <name>base64</name>
  <memory unit='G'>8</memory>
  <vcpu placement='static'>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc-i440fx-1.5'>hvm</type>
    <boot dev='cdrom'/>
    <boot dev='hd'/>
  </os>
  <features>
    <acpi/>
    <apic/>
    <pae/>
  </features>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none' io='native'/>
      <source file='/mnt/sd/vmstor/base-64/base64bit.qcow2'/>
      <target dev='sda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x09' function='0x0'/>
    </disk>
    <disk type='file' device='cdrom'>
      <driver name='qemu' type='raw'/>
      <target dev='hdc' bus='ide'/>
      <readonly/>
      <address type='drive' controller='0' bus='1' target='0' unit='0'/>
    </disk>
    <controller type='usb' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x2'/>
    </controller>
    <controller type='pci' index='0' model='pci-root'/>
    <controller type='scsi' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x07' function='0x0'/>
    </controller>
    <controller type='ide' index='0'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
    </controller>
    <interface type='network'>
      <source network='management'/>
      <model type='virtio'/>
  </interface>  
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
    <input type='mouse' bus='ps2'/>
    <graphics type='vnc' port='-1' autoport='yes'/>
    <sound model='ich6'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x06' function='0x0'/>
    </sound>
    <video>
      <model type='cirrus' vram='9216' heads='1'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
    </video>
    <memballoon model='virtio'>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x08' function='0x0'/>
    </memballoon>
  </devices>
</domain>

IMPORTANT:

  <name>base64</name>
  <memory unit='G'>8</memory>
  <vcpu placement='static'>1</vcpu>


E.g change name, memory, #cpus

<disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none' io='native'/>
      <source file='/mnt/sd/vmstor/mymachine/mymachine.qcow2'/>
      <target dev='sda' bus='virtio'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x09' function='0x0'/>
    </disk>

E.g change image path to the correct qcow2 file.


Network, add in the correct order the needed networks: network is one of the available networks 

    <interface type='network'>
      <source network='management'/>
      <model type='virtio'/>
  </interface>  

The order will determine the naming in the vm!

How to use the file:


virsh define test.xml
virsh start test.xml

And machine is created.

This can also be done via python:

import libvirt
conn = libvirt.open() #open local connction to local libvirt deamon
xml = j.sysstem.fs.fileGetContents(xml)
conn.defineXML(xml)
dom = conn.lookupByName(name)
dom.start()
#this can contain some small error i didn't test it