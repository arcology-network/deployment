import sys
import os
from rich.console import Console
import installsvclib


n = 0
name = 'TBD'

filename = sys.argv[1]

ispwd=True
debugmod=False
for arg in sys.argv:
  if arg=='-debugmod':
    debugmod=True
  elif arg=='-sshkey':
    ispwd=False

installsvclib._init()
logger = installsvclib.initLog('monaco','cluster.log')

logger.debug('---------------------------------------------------------------------------------------------------------------------------- ')

logger.debug('ispwd = '+ str(ispwd))
logger.debug('debugmod = '+str(debugmod))

connection_info,mnodes,pnodes,basecfg,name,n=installsvclib.loadConfig(filename,ispwd)
ssh_clients = installsvclib.init_ssh_clients(connection_info)


logger.debug('action = start')
path = os.getcwd()+'/' 
lanes = sys.argv[2]
genesisFile=sys.argv[3]

installsvclib.startkafkas(connection_info,ssh_clients)
installsvclib.startCluster(name,mnodes,pnodes,connection_info,lanes,ssh_clients,debugmod,basecfg)

