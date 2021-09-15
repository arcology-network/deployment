import json
from pexpect import pxssh
import subprocess
import time
import threading
import requests
import datetime
import toml
import logging
from rich.console import Console

TMPPATH = "/tmp"

def _init():
    global _global_dict
    _global_dict = {}


def set_value(key,value):
    _global_dict[key] = value


def get_value(key,defValue=None):
    try:
        return _global_dict[key]
    except KeyError:
        return defValue


def print_command(shfile,command):
      shfile.write(command)
      shfile.write('\n')


def printSection(msg):
  logger=get_value('log')
  console=get_value('console')

  print('')
  console.rule("[bold]Section ["+ msg+"] ", align='left',characters='*')
  logger.debug('Section ['+ msg +'] *****************************************************************************')

def printLog(msg,newLine=True):
  logger=get_value('log')
  console=get_value('console')

  if newLine:
    console.print(msg)
  else:
    console.print(msg,end="")

  logger.debug(msg)

def initLog(name,logfile):
    logger = logging.getLogger(name)
    logger.setLevel(level=logging.DEBUG)

    handler = logging.FileHandler(logfile)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    #console = logging.StreamHandler()
    #console.setLevel(logging.WARNING)

    logger.addHandler(handler)
    #logger.addHandler(console)
    set_value('log',logger)
    set_value('console',Console())
    return logger

def createCoinbase(infile,outfile):
  with open(infile) as json_file:
    data = json.load(json_file)
    fout = open(outfile,'w+')
    for validator in data['validators']:
      addr=validator['address']
      fout.write('0000,0x'+addr.lower()+',0\n')
    fout.close()

def getPeerList(tomlfile):
  with open(tomlfile, mode='rb') as f:
    content = f.read()
    if content.startswith(b'\xef\xbb\xbf'): 
      content = content[3:]
    dic = toml.loads(content.decode('utf8'))
    return dic['p2p']['persistent_peers'].strip()

def file_replace(filename,src,dest):
  file1 = open(filename, 'r')
  content=file1.read()
  file1.close()

  t = content.replace(src,dest)
  with open(filename,"w") as f2:
    f2.write(t)

  #print('txt replace completed')

def print_output(result):
  logger=get_value('log')
  
  if result!=b'':
    logger.debug(result)
    print(result)

def get_output(ssh_client, command):
  logger=get_value('log')

  ssh_client.sync_original_prompt()
  ssh_client.sendline(command)
  ssh_client.prompt()
  strs = bytes.decode(ssh_client.before)
  if len(strs)>0: 
    logger.debug('\n'.join(strs.split('\n')[:-1]))
  return '\n'.join(strs.split('\n')[:-1])

def stop_concrete_process(ssh_client, name):
  ret = get_output(ssh_client, 'kill -9 `pidof -s ' + name + '`')

def print_pid(result,svc,ip):
  printLog(svc +' on '+ ip +' started ',False)
  if result[0]=='[' and (result[2]==']' or result[3]==']'):
    if result[2]==']':
      printLog('successfully   PID ='+result[3:])
    else:
      printLog('successfully   PID ='+result[4:])
  else:
    printLog('failed Err='+result)
  

def start_concrete_svcs(ssh_client,conn,ppstr1,ppstr2,lanes,p2p_listenaddr,debugmode,basecfg,shfile):
  logger=get_value('log')

  svcs=conn['svcs']
  mqaddr=conn['mqaddr']
  mqaddr2=conn['mqaddr2']
  nidx=conn['nidx']
  nname=conn['nname']
  rpm=basecfg['rpm'] 
  nthread=conn['nthread']
  insid=conn['insid']
  remotepath=conn['remotepath']
  zkUrl=conn['zkUrl']
  localip=conn['localip']
  execAddrs=conn['execAddrs']
  
  outputmod=' 2>'+remotepath+'nohup.out '
  if debugmode:
    outputmod=' >'+remotepath+'nohup.out 2>&1'

  for svc in svcs:
    if len(svc)==0:
      continue
    
    if svc=='eshing-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml  --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='consensus-svc':
      logger.debug('consensus-svc delay start ...')
    elif svc=='p2p-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr  +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --persistent_peers=' + ppstr2 + '  --laddr='+ p2p_listenaddr + ' --node_key='+ nodeKeyPath + outputmod+' &' 
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='storage-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --zkUrl='+ zkUrl +' --localIp='+ localip +' --logcfg='+ remotepath +'svcs/bin/log.toml --af='+ remotepath +'svcs/af  --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='frontend-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' '+ remotepath +'svcs/bin/config.yml '+ outputmod +' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='exec-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --localIp='+localip+' --logcfg='+ remotepath +'svcs/bin/log.toml --insid='+ insid +' --nthread='+ nthread +' --execlog=true --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='scheduling-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --batchs=500 --zkUrl='+zkUrl+' --localIp='+ localip +' --execAddrs='+execAddrs+' --nthread='+ nthread +' --conflictfile='+ remotepath +'svcs/bin/conflictlist  --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + ' ' +outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,'sleep 3')
        print_command(shfile,command)
    elif svc=='pool-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + ' --rpm='+ rpm +outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='arbitrator-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --zkUrl='+ zkUrl +' --localIp='+ localip +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='gateway-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --zkUrl='+ zkUrl +' --localIp='+ localip +' --waits=3600  --txnums=1000 --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='ppt-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='core-svc'   or svc=='generic-hashing-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
    elif svc=='feeder':
      continue
    
    else:
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      logger.debug(command)
      if shfile==None:
        ret = get_output(ssh_client, command)
        print_pid(ret,svc,conn['ip'])
      else:
        print_command(shfile,command)
def mergeFile(path,monacoTmp,genesisFile):
    
  args = [path+"bins/consensus-svc", "merge"]
  args.append("--filea="+genesisFile)
  args.append("--fileb="+monacoTmp+"/coinbase")
  args.append("--filec="+monacoTmp+"/af")
  result = subprocess.check_output(args, stderr=subprocess.STDOUT)
  print_output(result)
  


def init_ssh_clients(connection_info):  
  printSection('Connect to host')

  ssh_clients = {}
  #for hostname, conn in connection_info.iteritems():
  for conn in connection_info:
    client = pxssh.pxssh(timeout=600,echo=False,maxread=80000)

    printLog('Try to connect to host '+ conn['ip'] +' through ssh ... ',False)
    if conn['ispwd']:
      if not client.login(conn['ip'], conn['username'], conn['password'], port=int(conn['port'])):
        printLog('Failed')
        exit(1)
      else:
        printLog('Established')
    else:
      if not client.login(conn['ip'], conn['username'], ssh_key=str(conn['password']), port=int(conn['port'])):
        printLog('Failed')
        exit(1)
      else:
        printLog('Established')
        
    ssh_clients[conn['name']] = client
  return ssh_clients  

def do_clean(connection_info,ssh_clients):
  printSection('Clear History Temp Files')

  monacoTmp = TMPPATH+'/monaco'
  subprocess.check_output(["rm", "-Rf", monacoTmp], stderr=subprocess.STDOUT)

  #for hostname, conn in connection_info.iteritems():
  for conn in connection_info:
    # remove config files if exist
    command = 'rm -rf  '+conn['remotepath']+'svcs' 
    ret = get_output(ssh_clients[conn['name']], command)

    command = 'rm -rf  '+conn['remotepath']+'nohup.out' 
    ret = get_output(ssh_clients[conn['name']], command)

    printLog(conn['ip'] +' ... cleared')

def stopall(connection_info,ssh_clients):
  printSection('Stoping Existing Services')
  #for hostname, conn in connection_info.iteritems():
  for conn in connection_info: 
    for svc in conn['svcs']:
      printLog('Terminating '+ svc + ' on '+ conn['ip'] +' ... ',False)
      stop_concrete_process(ssh_clients[conn['name']],svc)
      stop_concrete_process(ssh_clients[conn['name']],svc)
      printLog('Service stopped')

def findSvc(svcname,conn):
  for svc in conn['svcs']:
    if svc==svcname:
      return True
  return False

def deploy(path,conn,ssh_client,monacoTmp,rootdir):

  user=conn['username']
  #pwd=conn['password']
  remotepath=conn['remotepath']
  
  remoteBase=remotepath+'svcs'
  command = 'mkdir -p '+remoteBase
  ret = get_output(ssh_client, command)
  

  remoteBaseBin=remotepath+'svcs/bin'
  command = 'mkdir -p '+remoteBaseBin
  ret = get_output(ssh_client, command)
  

  commands = scpCommands(False,conn['ispwd'],conn['password'],path + "log.toml",user+"@" + conn['ip'] + ":" + remoteBaseBin, conn['port'])
  result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
  print_output(result)
  
  #copy starter
  commands = scpCommands(False,conn['ispwd'],conn['password'],path + "bins/starter",user+"@" + conn['ip'] + ":" + remoteBaseBin, conn['port'])
  result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
  print_output(result)

  for svc in conn['svcs']:
    if len(svc)==0:
      continue
    commands = scpCommands(False,conn['ispwd'],conn['password'],path + "bins/"+svc,user+"@" + conn['ip'] + ":" + remoteBaseBin, conn['port'])
    result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
    print_output(result)
	
    if svc=='frontend-svc':
      result = subprocess.check_output(["cp" , "-r", path + "config_template.yml",monacoTmp + "/config.yml"], stderr=subprocess.STDOUT)
      print_output(result)
      result = subprocess.check_output(["sed" , "-i", "s/zkUrl/"+conn['zkUrl']+"/g",monacoTmp + "/config.yml"], stderr=subprocess.STDOUT)
      print_output(result)
      commands = scpCommands(False,conn['ispwd'],conn['password'],monacoTmp + "/config.yml",user+"@" + conn['ip'] + ":" + remoteBaseBin, conn['port'])
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print_output(result)
    elif svc=='p2p-svc':
      commands = scpCommands(True,conn['ispwd'],conn['password'],rootdir + "/node" + str(conn['nidx']+"/config"),user+"@" + conn['ip'] + ":" + remoteBase, conn['port'])
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print_output(result)
    elif svc=='consensus-svc':
      commands = scpCommands(True,conn['ispwd'],conn['password'],rootdir + "/node" + str(conn['nidx']+"/config"),user+"@" + conn['ip'] + ":" + remoteBase, conn['port'])
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print_output(result)
      commands = scpCommands(True,conn['ispwd'],conn['password'],rootdir + "/node" + str(conn['nidx']+"/data"),user+"@" + conn['ip'] + ":" + remoteBase, conn['port'])
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print_output(result)
    elif svc=='storage-svc':
      commands = scpCommands(False,conn['ispwd'],conn['password'],monacoTmp + "/af",user+"@" + conn['ip'] + ":" + remoteBase, conn['port'])
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print_output(result)
    elif svc=='scheduling-svc':
      commands = scpCommands(False,conn['ispwd'],conn['password'],path + "conflictlist",user+"@" + conn['ip'] + ":" + remoteBaseBin, conn['port'])
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print_output(result) 

    printLog(svc + ' is ready on '+ conn['ip'] ) 
  return 


def startSvcs(ppstr1,ppstr2,conn,ssh_client,lanes,p2p_listenaddr,debugmode,basecfg,shfile):
  if len(conn['svcs'])==0:
    return

  start_concrete_svcs(ssh_client, conn, ppstr1,ppstr2,lanes,p2p_listenaddr,debugmode,basecfg,shfile)

def startCluster(name, mnodes, pnodes, connection_info,lanes,ssh_clients,debugmode,basecfg,shfile=None):  
  logger=get_value('log')

  printSection('Starting the service')

  monacoTmp = TMPPATH+'/monaco'
  rootdir = monacoTmp + '/' + name
  
  ppstr=getPeerList(rootdir+"/node0/config/config.toml")
  
  ppstr1 = ppstr 
  # rewrite ppstr
  for mnode in mnodes:
    if shfile==None:
      ppstr1 = ppstr1.replace('node' + str(mnode['index']),mnode['ip'] )
    else:
      ppstr1 = ppstr1.replace('node' + str(mnode['index']),mnode['localip'] )


  logger.debug('p2p.persistent_peers in consensus-svc = '+ppstr1)

  ppstr2 = ppstr 
  # rewrite ppstr
  for pnode in pnodes:
    if shfile==None:
      pnode['p2p_listenaddr'] ='tcp://'+ pnode['ip'] + ':36656'
      ppstr2= ppstr2.replace('node' + str(pnode['index']),pnode['ip'] )
    else:
      pnode['p2p_listenaddr'] ='tcp://'+ pnode['localip'] + ':36656'
      ppstr2= ppstr2.replace('node' + str(pnode['index']),pnode['localip'] )

  ppstr2= ppstr2.replace('26656','36656')
  logger.debug('persistent_peers in p2p-svc = '+ppstr2)
  
  idx=0
  for conn in connection_info:
    ssh_client=ssh_clients[conn['name']]
    nidx=int(conn['nidx'])-1
    if len(pnodes)>0:
      p2p_listenaddr=pnodes[nidx]["p2p_listenaddr"]
    else:
      p2p_listenaddr=""
    logger.debug('p2p_listenaddr='+p2p_listenaddr)
    idx=idx+1
    t = threading.Thread(target=startSvcs,name=str(idx) ,args=(ppstr1,ppstr2,conn,ssh_client,lanes,p2p_listenaddr,debugmode,basecfg,shfile,))  
    t.start() 
    t.join()


  
  
  if shfile==None:  
    #check services start state
    printSection('Checking Services Status')
    queryIp=""
    checkList =[]
    for conn in connection_info:
      for svc in conn['svcs']:
        if svc=='frontend-svc':
          queryIp=conn['ip']
        if svc=='consensus-svc':
          continue
        if len(svc)==0:
          continue
        checkItem = {}
        checkItem['client'] = ssh_clients[conn['name']]
        checkItem['svc'] = svc
        checkItem['ip'] = conn['ip']
        checkList.append(checkItem)
  
    queryCounter=0
    while len(checkList)>0:
      queryCounter=queryCounter+1
      time.sleep(2)
      checkListNext =[]
      for checkItem in checkList:
        ret = get_output(checkItem['client'], 'pidof -s ' + checkItem['svc'])
        if len(ret)>0:
          printLog(checkItem['svc'] + ' is ready on '+ checkItem['ip'] +'   PID = '+ret)
        else:
          checkListNext.append(checkItem)
      checkList=checkListNext
      if queryCounter>4:
        for checkItem in checkList:
          #console.print_exception(checkItem['svc'] + ' on '+ checkItem['ip'] +' error')
          printLog(checkItem['svc'] + ' on '+ checkItem['ip'] +' error')
          logger.debug(checkItem['svc'] + ' on '+ checkItem['ip'] +' error')

        printLog('Please check detail,or retry')
        return
  
  printSection('Start Node')
  addminites=len(mnodes)//60+1
  now=datetime.datetime.now()
  delta=datetime.timedelta(minutes=addminites)
  n_minites=now+delta
  startTime=n_minites.strftime('%Y-%m-%d_%H:%M:%S')
  startTime1 = str(startTime).replace('_',' ')
  printLog('Consensus-svc  is scheduled to start at '+startTime1)


  
  for node in mnodes:
    conn=node['conn']
    ssh_client=ssh_clients[conn['name']]    
    idx=idx+1
    threadConsensus = threading.Thread(target=startConsensus,name=str(idx) ,args=(ssh_client,conn,ppstr1,lanes,debugmode,startTime,shfile,))  
    threadConsensus.start() 
    threadConsensus.join()

  if shfile==None:  
    printSection('Checking Testnet Status')
    #check query state
    if len(queryIp)>0:
      queryUrl='http://'+ queryIp +':8080/blocks/latest?access_token=access_token&transactions=false'
      logger.debug('QueryUrl >> '+queryUrl)
      willQuery=True
  
      while willQuery:
        time.sleep(5)
        printLog('Try to query Testnet status ... ',False)
        res = requests.get(queryUrl)
        logger.debug(res.text)
        if res.text.startswith('{"block"'):
          printLog('Ready!!!')
          willQuery=False
        else:
          printLog('Not yet')
  
  printLog('Testnet setup completed')
  
  return

def create(path,name, n, pnodes, connection_info,ssh_clients,genesisFile):
  logger=get_value('log')

  # prepare config files
  monacoTmp = TMPPATH+'/monaco'
  result =subprocess.check_output(["mkdir", "-p", monacoTmp], stderr=subprocess.STDOUT)
  print_output(result)

  rootdir = monacoTmp + '/' + name
  result =subprocess.check_output(["mkdir", "-p", rootdir], stderr=subprocess.STDOUT)
  print_output(result)

  printSection('Initializing Validators')
  result = subprocess.check_output([path +'bins/consensus-svc', 'testnet','--v='+str(n),'--o='+rootdir], stderr=subprocess.STDOUT)
  result = result.decode('utf-8')
  print_output('\n'.join(result.split('\n')[:-1]))

  createCoinbase(rootdir+"/node0/config/genesis.json",monacoTmp+"/coinbase")
  
  ###create genesis address file
  mergeFile(path,monacoTmp+'/',genesisFile)

  printSection('Deploy the service')
  idx=0
  for conn in connection_info:
    ssh_client=ssh_clients[conn['name']]
    nidx=int(conn['nidx'])-1
    if len(pnodes)>0:
      p2p_listenaddr=pnodes[nidx]["p2p_listenaddr"]
    else:
      p2p_listenaddr=""
    logger.debug('p2p_listenaddr='+p2p_listenaddr)
    idx=idx+1
    t = threading.Thread(target=deploy,name=str(idx) ,args=(path,conn,ssh_client,monacoTmp,rootdir,))  
    t.start() 
    t.join()
  
  return

def startConsensus(ssh_client,conn,ppstr1,lanes,debugmode,startTime,shfile):
  logger=get_value('log')

  mqaddr=conn['mqaddr']
  mqaddr2=conn['mqaddr2']
  nidx=conn['nidx']
  nname=conn['nname']
  remotepath=conn['remotepath']
  
  outputmod=' 2>'+remotepath+'nohup.out '
  if debugmode:
    outputmod=' >'+remotepath+'nohup.out 2>&1'

  
  if shfile==None:
    command ='nohup '+ remotepath +'svcs/bin/starter '+ startTime +' nohup '+ remotepath +'svcs/bin/consensus-svc start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --instrumentation.prometheus=true --instrumentation.prometheus_listen_addr=:19001  --p2p.persistent_peers=\'' + ppstr1 + '\'' +' --concurrency='+ lanes + outputmod+' &'
    logger.debug(command)    
    ret = get_output(ssh_client, command)
    print_pid(ret,'consensus-svc',conn['ip'])
  else:  
    command = 'nohup '+ remotepath +'svcs/bin/consensus-svc start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --instrumentation.prometheus=true --instrumentation.prometheus_listen_addr=:19001  --p2p.persistent_peers=\'' + ppstr1 + '\'' +' --concurrency='+ lanes + outputmod+' &'
    logger.debug(command)    
    print_command(shfile,command)
  
  

def setupkafkas(path, connection_info,ssh_clients):

  printSection('Install kafka')

  idx=0
  for conn in connection_info:
    if conn['kafka']=='false':
      continue
    
    ssh_client=ssh_clients[conn['name']]
    
    idx=idx+1
    thread = threading.Thread(target=setupkafka,name='k'+str(idx) ,args=(path,conn,ssh_client,))  
    thread.start() 
    thread.join()

def startkafkas(connection_info,ssh_clients,shfile=None):

  printSection('Start kafka')

  idx=0
  for conn in connection_info:
    if conn['kafka']=='false':
      continue
    
    ssh_client=ssh_clients[conn['name']]
    
    idx=idx+1
    thread = threading.Thread(target=startkafka,name='k'+str(idx) ,args=(conn,ssh_client,shfile,))  
    thread.start() 
    thread.join()
    
def scpCommands(copyDirector,isPwd,pwd,local,remote,port):
    commands = []
    if isPwd:
      commands.append("sshpass")
      commands.append("-p")
      commands.append(pwd)
      commands.append("scp")
      commands.append("-P")
      commands.append(port)
    else:
      commands.append("scp")
      commands.append("-P")
      commands.append(port)
      commands.append("-i")
      commands.append(str(pwd))
    
    if copyDirector:
      commands.append("-r")
    
    commands.append(local)
    commands.append(remote)
    return commands

def setupkafka(path,conn,ssh_client):   
  command = 'mkdir -p '+conn['remotepath']
  ret = get_output(ssh_client, command)
  
  localdir = path + 'kafka'

  commands = scpCommands(True,conn['ispwd'],conn['password'],localdir,conn['username']+"@" + conn['ip'] + ":" + conn['remotepath'], conn['port'])
  result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
  print_output(result)

  destPath=conn['remotepath']+'kafka'

  command = 'cd '+conn['remotepath']+'kafka;chmod 755 *.sh'
  ret = get_output(ssh_client, command)
  
  printLog('[bold]Setting up kafka ... ',False)
  command = 'echo -e "'+destPath+'\\n1\\n'+conn['localip']+'\\n" | '+destPath+'/installkfk.sh'
  ret = get_output(ssh_client, command)
  printLog(' OK ')


  printLog('Kafka on ' + conn['ip'] + '  installed')
  


def startkafka(conn,ssh_client,shfile): 
  printLog('[bold]Starting kafka ... ',False)
  destPath=conn['remotepath']+'kafka'
  command = destPath+'/kafka/start.sh'
  if shfile==None:  
    ret = get_output(ssh_client, command)
  else:
    print_command(shfile,command)
    print_command(shfile,'sleep 1')
  #printLog(ret)
  time.sleep(1)
  printLog(' OK ')

  printLog('[bold]Creating Topics on Kafka ... ')
  #printSubSection('Start Creating Topics on Kafka')
  command = destPath+'/kafka/maketopic.sh '+ str(conn["partitions"])
  if shfile==None:  
    ret = get_output(ssh_client, command)
    printLog(ret)
  else:
    print_command(shfile,command)
  

  
  printLog('Kafka on ' + conn['ip'] + '  started')
  print('')

def clearkafkas(connection_info,ssh_clients):

  printSection('Stop Existing Kafka')

  idx=0
  for conn in connection_info:
    if conn['kafka']=='false':
      continue
    
    ssh_client=ssh_clients[conn['name']]
    idx=idx+1
    thread = threading.Thread(target=clearkafka,name=str(idx) ,args=(conn,ssh_client,))  
    thread.start() 
    thread.join()


def clearkafka(conn,ssh_client):  
  
  destPath=conn['remotepath']+'kafka'

  command = destPath+'/kafka/stop.sh'
  ret = get_output(ssh_client, command)
  
  command = destPath+'/kafka/stop.sh'
  ret = get_output(ssh_client, command)
  
  command = 'rm -rf  '+destPath+' /tmp/zookeeper/' 
  ret = get_output(ssh_client, command)
  
  printLog('kafka on ' + conn['ip'] + ' ... cleared')
  
def loadConfig(filename,ispwd):
  logger=get_value('log')

  connection_info =[] #{}
  mnodes = []
  pnodes = []
  execs = {}
  ppts = {}
  basecfg = {}
  name = 'TBD'

  with open(filename) as config_file:
    config = json.load(config_file)
    name = config['name']
    
    logger.debug('testnet name = ' + name)

    basecfg['rpm']=config['rpm']

    mindex = 0
    pindex = 0
    for host in config['hosts']:
      ci = {}
      ci['name'] = host['name']
      ci['ip'] = host['ip']
      ci['port'] = host['port']
      ci['localip'] = host['localip']
      ci['username'] = host['username']
      ci['password'] = host['password']
      ci['mqaddr'] = host['mqaddr']
      ci['mqaddr2'] = host['mqaddr2']
      svcs = host['svcs']
      nsvcs = []
      for svc in svcs:
        if svc.startswith('ammolite'):
          continue
        else:
          nsvcs.append(svc)
      ci['svcs'] = nsvcs
      ci['nidx'] = host['nidx']
      ci['nname'] = host['nname']
      ci['nthread'] = host['nthread']
      ci['insid'] = host['insid']
      ci['zkUrl'] = host['zkUrl']
      ci['ispwd'] = ispwd
      ci['execAddrs'] = ''
      ci['remotepath'] = host['remotepath']
      ci['kafka'] = host['kafka']
      if 'exec-svc' in ci['svcs'] :
        if len(execs)>0 and ci['nname'] in execs:
          execs[ci['nname']]=execs[ci['nname']]+","+ci['localip']
        else:
          execs[ci['nname']]=ci['localip']
      if 'ppt-svc' in ci['svcs'] :
        if len(ppts)>0 and ci['nname'] in ppts:
          ppts[ci['nname']]=ppts[ci['nname']]+1
        else:
          ppts[ci['nname']]=1

      if 'consensus-svc' in ci['svcs'] :
        mnode = {}
        mnode['ip'] = ci['ip']
        mnode['index'] = mindex
        mnode['conn']=ci
        mnode['localip']=ci['localip']
        mindex += 1
        mnodes.append(mnode)
      if 'p2p-svc' in ci['svcs'] :
        pnode = {}
        pnode['ip'] = ci['ip']
        pnode['index'] = pindex
        pnode['localip']=ci['localip']
        pindex += 1
        pnodes.append(pnode)
      connection_info.append(ci)
    
    logger.debug('connection_info = '+str(connection_info))
    logger.debug('mnodes = '+str(mnodes))

    n = mindex
    logger.debug('node nums = '+str(n))

  for conn in connection_info:
    if 'scheduling-svc' in conn['svcs'] and conn['nname'] in execs:
      conn["execAddrs"]=execs[conn['nname']]

  for conn in connection_info:
    if conn['kafka']=='true' and conn['nname'] in ppts:
      conn["partitions"]=ppts[conn['nname']]

  return connection_info,mnodes,pnodes,basecfg,name,n