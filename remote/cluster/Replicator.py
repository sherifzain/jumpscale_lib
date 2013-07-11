from openwizzy import *
import time
import os
import re

class Replicator():

    def __init__(self):
        self.recipe=[]
        self.dirs2monitor={}
        #self.excludes=["/test"]
        self.excludes=[]
        self.replicationIncludeRegexes=[".*\.py",".*\.cfg",".*\.rscript"]  #@todo have to make sure pyc are not copied
        self.baseDir="/opt/qbase3debug"
        self.taskletDirs = ['apps/workflowengine/tasklets/actor', 'apps/workflowengine/tasklets/rootobject', 'apps/applicationserver/services/wizard_engine/tasklets']
        self._createddirs=[]
        
    def loadRecipe(self):
        self.recipe = []
        lines=i.codemgmt._getRecipeLines()
        # check that we dont have double link targets!
        linktargets = []
        for line in lines:
            if line.strip() == '':
                continue
            if len(line.split(","))==6:
                items=line.split(",")
                items=[item.strip() for item in items]
                [connectionname,reponame,branchname,pathinrepo,pathinqbase,sync2nodes]= items
                if pathinqbase in linktargets:
                    raise RuntimeError('duplicate link target found in specified recipe')
                linktargets += [pathinqbase]
            else:
                raise RuntimeError("recipe not well structured, line: " + line)
            
        for line in lines:
            if line.strip() == '':
                continue
            self.recipe.append(RecipeLine(line))
           
        for recipeLine in self.recipe:
            if o.system.fs.joinPaths("%s_%s"%(self.baseDir,recipeLine.sync2nodes), recipeLine.pathinqbase) not in self.dirs2monitor.itervalues():
                if self.dirs2monitor.has_key(recipeLine.sync2nodes):
                    self.dirs2monitor[recipeLine.sync2nodes].append(o.system.fs.joinPaths("%s_%s"%(self.baseDir,recipeLine.sync2nodes),recipeLine.pathinqbase))
                else:
                    self.dirs2monitor[recipeLine.sync2nodes]=[o.system.fs.joinPaths("%s_%s"%(self.baseDir,recipeLine.sync2nodes),recipeLine.pathinqbase),]
    
    def _copyDir(self, path, cluster, nodetype):
        for dir in o.system.fs.listDirsInDir(path,True):
            self._copyDir(dir, cluster, nodetype)
        for file in o.system.fs.listFilesInDir(path,True):
            self._copyFile(file, cluster, nodetype)

    def _copyFile(self, path, cluster, type=None):
        if o.codetools.regex.matchMultiple(self.replicationIncludeRegexes, path):
            #print "PATH:%s" % path
            #if event==1:
            print "copy %s to cluster .... \n" % (path),
            #@todo call cluster to push changed file
            if not type:
                for nodetype,dirs in self.dirs.iteritems():
                    if o.system.fs.getDirName(path).rstrip('/') in dirs:
                        type=nodetype
                        break
            destpath=path.replace("qbase3debug_%s"%type,"qbase3")
            if destpath not in self._createddirs:
                cluster.mkdir(o.system.fs.getDirName(destpath),hostnames=cluster.listnodes(type=type) )
                self._createddirs.append(destpath)
            cluster.sendfile(path,destpath,hostnames=cluster.listnodes(type=type))
            taskletDir = filter(lambda x: re.search(x,destpath), self.taskletDirs)
            for dir in taskletDir:
                print "Touching %s/%s"%(dir,'tasklets_updated')
                cluster.execute('touch %s'%o.system.fs.joinPaths(o.dirs.baseDir, dir, 'tasklets_updated'), hostnames=cluster.listnodes(type=type))
                
                
    def start(self,clustername="", copyFiles=True):
            
        if not o.system.fs.exists("/opt/qbase3/lib/libgamin-1.so.0"):
            #means gamin not installed
            o.system.platformtype.ubuntu.installFileMonitor()
        sys.path.append("/usr/lib/pymodules/python2.6/")
        import gamin
        
        answer,cluster = False,None
        if len(q.cluster.list()) == 0:
            print "No cluster found, creating one"
            clustername = o.gui.dialog.askString("Name for the new cluster")
            cluster = q.cluster.create(clustername=clustername)
        if clustername=="":
            clustername=o.console.askChoice(q.cluster.list(),"Choose cluster")
        answer=o.console.askYesNo("Are you sure you want to replicate to cluster %s" %clustername)
        if not answer:
            print "Exiting replicator . . ."
            return
        if copyFiles:
            copyFiles = o.console.askYesNo("Do you want to synchronize the complete development sandbox to %s now" %clustername)
        cluster = q.cluster.get(clustername)
        self.loadRecipe()
        if not 'all' in self.dirs2monitor.keys(): self.dirs2monitor['all'] = []
        self.dirs2monitor['all'].append(o.system.fs.joinPaths("%s_all"%self.baseDir,"lib","openwizzy"))
        self.dirs2monitor['all'].append(o.system.fs.joinPaths("%s_all"%self.baseDir,"utils"))

        if copyFiles:
            #Make sure our basedir is rsyncShared
            modulename = o.system.fs.getBaseName(self.baseDir)
            o.codemgmt.rsyncShareQbaseDebug(clustername, modulename)
            localip = o.manage.rsync.cmdb.ipaddress
            for nodetype in ['all', 'master']:
                cluster.execute('/usr/bin/rsync -aL %s::%s/%s_%s/* %s'%(localip, modulename, modulename, nodetype, o.dirs.baseDir),hostnames=cluster.listnodes(nodetype))

        def callback(path,event,data):
            if start==False:
                return 
            if event==1:
                #print "Modidied: %s/%s" % (data,path)
                pass
            elif event==2:
                #print "Delete: %s/%s" % (data,path)
                pass
            elif event==5:
                print "Added: %s/%s" %(data,path)
                if o.system.fs.isDir("%s/%s" %(data,path)):
                    for type,typedirs in self.dirs.iteritems():
                        if data in typedirs:
                            self.dirs[type].append("%s/%s" %(data,path))
                            self.monitors[-1].watch_directory("%s/%s" %(data,path), callback, "%s/%s" %(data,path))
                pass
            else:
                print "??? %s, %s/%s" % (event,data,path)
            path="%s/%s" % (data,path)
            path=path.strip()
            if o.system.fs.exists(path) and start and (event==1 or event==2):
                #if o.system.fs.exists(path) and start:
                #if path[-3:]==".py":
                self._copyFile(path, cluster)
                        
        start=False     
        
        excludes=self.excludes
        self.dirs={}

        starttime=o.base.time.getTimeEpoch()
        for nodetype,directoryList in self.dirs2monitor.iteritems():
            for basedir in directoryList:
                if not o.system.fs.exists(basedir):
                    raise RuntimeError(
"""Did not find directory which needs to be monitored. Has the code already been checked out on your filesystem? 
Use i.codemgmt.checkoutSSOInSandbox(...
Directory not found is %s
""" % basedir)

                subdirs=o.system.fs.listDirsInDir(basedir,True)
                if nodetype in self.dirs.keys():
                    self.dirs[nodetype].append(basedir)
                else:
                    self.dirs[nodetype] = [basedir,]
                for item in subdirs:
                    skip=False
                    for excl in excludes:
                        if item.find(excl)<>-1:
                            skip=1
                    if skip==False:
                        self.dirs[nodetype].append(item)

        #make sure dirs are unique
        alluniquedirs = []
        for nodetype,dirlist in self.dirs.iteritems():
            uniquedirs=[]
            for item in dirlist:
                if item not in uniquedirs and item not in alluniquedirs:
                    #print "Adding %s"%item
                    uniquedirs.append(item)
            alluniquedirs += uniquedirs
            self.dirs[nodetype] = uniquedirs
        nrofdirs = sum(map(lambda l: len(l), self.dirs.itervalues()))
        if nrofdirs>5000:
            raise RuntimeError("Dir Monitor System max supports 5000 dirs, found %s" % len(dirs))
        self.monitors=[]
        self.monitors.append(gamin.WatchMonitor())

        counter=0
        localcounter=0
        for nodetype,dirlist in self.dirs.iteritems():
            for item in dirlist:
                # If we need to copy do it here
                #if copyFiles:
                #    self._copyDir(item, cluster, nodetype)
                counter+=1
                localcounter+=1
                if localcounter==200:  # a new monitor is needed per 200 otherwise can lock
                    o.logger.log( "Create new monitor",2)
                    self.monitors.append(gamin.WatchMonitor())        
                    #time.sleep(2)
                    localcounter=0
                o.logger.log( "%s/%s: add dir %s to monitor %s" % (counter,len(dirlist),item,len(self.monitors)),2)
                self.monitors[-1].watch_directory(item, callback,item)

        o.console.echo('replicating ' + str(nrofdirs) + ' directories')

        while True:
            #print "w"
            time.sleep(1)
            #mon.event_pending()
            #ipshell()
            #mon.handle_one_event()            
            for mon in self.monitors:
                mon.handle_events()
            if o.base.time.getTimeEpoch()>starttime+5:
                start=True
        for mon in self.monitors:
            mon.stop_watch(".")
        self.monitors=[]
        
class RecipeLine():
    def __init__(self,recipeline=""):
        if recipeline<>"":
            if len(recipeline.split(","))==6:
                items=recipeline.split(",")  
                items =[item.strip() for item in items]
                self.mercurialconnectionname=items[0]
                self.reponame=items[1]
                self.branchname=items[2]
                self.pathinrepo=items[3]
                self.pathinqbase=items[4]
                self.sync2nodes=items[5]
            else:
                raise RuntimeError("recipe not well structured, recipeline: " + recipeline)
            
        else:
            self.mercurialconnectionname=""
            self.reponame=""
            self.branchname=""
            self.pathinrepo=""
            self.pathinqbase=""
            self.sync2nodes=""
            
    def __str__(self):
        return "%s %s %s %s %s %s" % (self.mercurialconnectionname,self.reponame,self.branchname,self.pathinrepo,self.pathinqbase,self.sync2nodes)
    
    __repr__=__str__
        
