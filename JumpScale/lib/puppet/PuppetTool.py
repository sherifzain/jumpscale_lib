from JumpScale import j


class PuppetTool():

    def __init__(self):
        self.do = j.develtools.installer._do

    def install(self):
        codename, descr, id, release = j.system.platform.ubuntu.getVersion()
        do = j.develtools.installer._do
        j.system.fs.changeDir("/tmp")
        if codename == "olivia" or "raring":
            do.download("http://apt.puppetlabs.com/puppetlabs-release-raring.deb", "puppetlabs.deb")
        else:
            do.download("http://apt.puppetlabs.com/puppetlabs-release-%s.deb" % codename, "puppetlabs.deb")

        do.execute("dpkg -i puppetlabs.deb")
        do.execute("apt-get update")
        do.execute("apt-get install puppet-common -y")

        do.symlink("/usr/lib/ruby/vendor_ruby/puppet/", "/opt/puppet")

    def findmodule(self, name):
        print self.do.execute("puppet module search %s" % name)

    def install(self, name, version=None):
        if version != None:
            cmd = "puppet module install %s --version %s" % (name, version)
        else:
            cmd = "puppet module install %s " % (name)
        self.do.execute(cmd)
