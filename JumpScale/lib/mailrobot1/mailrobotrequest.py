from JumpScale import j

descr = """
Parses and executes a mailrobot auto-deployment request 
"""

name = "mailrobotrequest"
category = "mailrobot"
organization = "jumpscale"
author = "zains@codescalers.com"
license = "bsd"
version = "1.0"
async = True

def action(appkwargs, hrd):
    import JumpScale.lib.ms1
    j.tools.ms1.setSecret(appkwargs['appdeck.secret'], True)
    j.tools.ms1.deployAppDeck(appkwargs['appdeck.location'], appkwargs['appdeck.app.name'], appkwargs['appdeck.app.memsize'],
                              appkwargs['appdeck.app.ssdsize'], appkwargs['appdeck.app.vsansize'], appkwargs['appdeck.app.jpdomain'],
                              appkwargs['appdeck.app.jpname'], config=hrd, description=appkwargs['appdeck.app.description'])
    return True