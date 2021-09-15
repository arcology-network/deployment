import sys
import os
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


logger.debug('action = setup')
path = os.getcwd()+'/' 
lanes = sys.argv[2]
genesisFile=sys.argv[3]

installsvclib.setupkafkas(path,connection_info,ssh_clients)
installsvclib.create(path,name, n, pnodes, connection_info,ssh_clients,genesisFile)

print('')
installsvclib.printLog('Deploy kafka and service completed')