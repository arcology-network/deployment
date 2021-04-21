import sys
import json
from pexpect import pxssh
import os
import subprocess
import shutil
import socket
import fcntl
import struct
import time
import threading
import chardet
import requests
import datetime
import toml

TMPPATH = "/tmp"

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

  print('txt replace completed')


def get_output(ssh_client, command):
  ssh_client.sync_original_prompt()
  ssh_client.sendline(command)
  ssh_client.prompt()
  strs = bytes.decode(ssh_client.before)
  print('#' + strs + '#')
  return '\n'.join(strs.split('\n')[:-1])

def stop_concrete_process(ssh_client, name):
  ret = get_output(ssh_client, 'kill -9 `pidof -s ' + name + '`')
  print(ret)

def start_concrete_svcs(ssh_client,conn,ppstr1,ppstr2,lanes,p2p_listenaddr,debugmode,basecfg):
  
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
  nodeKeyPath=remotepath+'svcs/config/node_key.json'
  p2plog=remotepath+'svcs/log/p2p.log'

  cfgfilea= remotepath+"svcs/hpmtAccount/config.json"
  cfgfiles= remotepath+"svcs/hpmtStorage/config.json"
  
  outputmod=' 2>'+remotepath+'nohup.out '
  if debugmode:
    outputmod=' >'+remotepath+'nohup.out 2>&1'

  for svc in svcs:
    if len(svc)==0:
      continue

    if svc=='eshing-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml  --cfga='+ cfgfilea +'  --cfgs='+ cfgfiles +'  --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='consensus-svc':
      #command = 'BCHOME=' + remotepath  + 'svcs' + ' nohup '+ remotepath +'svcs/bin/'+svc+' start --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --p2p.persistent_peers=\'' + ppstr1 + '\'' +' --concurrency='+ lanes + outputmod+' &'
      #print(command)
      #ret = get_output(ssh_client, command)
      #print(ret)
      print('consensus-svc delay start ...')
    elif svc=='p2p-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr  +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --persistent_peers=' + ppstr2 + '  --laddr='+ p2p_listenaddr + ' --node_key='+ nodeKeyPath + outputmod+' &' 
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='storage-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --zkUrl='+ zkUrl +' --localIp='+ localip +' --logcfg='+ remotepath +'svcs/bin/log.toml --af='+ remotepath +'svcs/af  --cacheSizeMax=20 --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='frontend-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' '+ remotepath +'svcs/bin/config.yml '+ outputmod +' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='exec-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --localIp='+localip+' --logcfg='+ remotepath +'svcs/bin/log.toml --nthread='+ nthread +' --insid='+ insid +' --execlog=true --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='scheduling-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --batchs=2000 --zkUrl='+zkUrl+' --localIp='+ localip +' --execAddrs='+execAddrs+'  --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + ' ' +outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='pool-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + ' --waits=3600 --rpm='+ rpm +outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='arbitrator-svc':
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --zkUrl='+ zkUrl +' --localIp='+ localip +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='client-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --zkUrl='+ zkUrl +' --localIp='+ localip +' --insid='+ insid +' --txnums=1000 --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='ppt-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --waits=3600 --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)
    elif svc=='core-svc'   or svc=='generic-hashing-svc' :
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)

    elif svc=='feeder':
      continue
    
    else:
      command = 'nohup '+ remotepath +'svcs/bin/'+svc+' start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --concurrency='+ lanes + outputmod+' &'
      print(command)
      ret = get_output(ssh_client, command)
      print(ret)

def mergeFile(path,monacoTmp,genesisFile):
    
  args = [path+"bins/consensus-svc", "merge"]
  args.append("--filea="+genesisFile)
  args.append("--fileb="+monacoTmp+"/coinbase")
  args.append("--filec="+monacoTmp+"/af")
  result = subprocess.check_output(args, stderr=subprocess.STDOUT)
  print(result)
  


def init_ssh_clients(connection_info):
  ssh_clients = {}
  #for hostname, conn in connection_info.iteritems():
  for conn in connection_info:
    client = pxssh.pxssh(timeout=600,echo=False,maxread=80000)
    if conn['ispwd']:
      print('try connect to %s through ssh' % conn['ip'])
      if not client.login(conn['ip'], conn['username'], conn['password']):
        print('failed to connect to %s through ssh' % conn['name'])
        exit(1)
    else:
      if not client.login(conn['ip'], conn['username'], ssh_key=str(conn['password'])):
        print('failed to connect to %s through ssh' % conn['name'])
        exit(1)	
    ssh_clients[conn['name']] = client
  return ssh_clients  

def do_clean(ssh_clients):
  monacoTmp = TMPPATH+'/monaco'
  subprocess.check_output(["rm", "-Rf", monacoTmp], stderr=subprocess.STDOUT)

  #subprocess.check_output(["rm", "-Rf", path+name], stderr=subprocess.STDOUT)
  #subprocess.check_output(["rm", "-Rf", path+"af"], stderr=subprocess.STDOUT)
  #subprocess.check_output(["rm", "-Rf", path+"config.yml"], stderr=subprocess.STDOUT)
  #subprocess.check_output(["rm", "-Rf", path+"coinbase"], stderr=subprocess.STDOUT)

  #for hostname, conn in connection_info.iteritems():
  for conn in connection_info:
    # remove config files if exist
    command = 'rm -rf  '+conn['remotepath']+'svcs' 
    ret = get_output(ssh_clients[conn['name']], command)

    command = 'rm -rf  '+conn['remotepath']+'nohup.out' 
    ret = get_output(ssh_clients[conn['name']], command)


def stopall(connection_info,ssh_clients):
  #for hostname, conn in connection_info.iteritems():
  for conn in connection_info: 
    for svc in conn['svcs']:
      stop_concrete_process(ssh_clients[conn['name']],svc)
      stop_concrete_process(ssh_clients[conn['name']],svc)


def findSvc(svcname,conn):
  for svc in conn['svcs']:
    if svc==svcname:
      return True
  return False

def deploy(path,ppstr1,ppstr2,conn,ssh_client,lanes,p2p_listenaddr,debugmode,basecfg,monacoTmp,rootdir):

  user=conn['username']
  pwd=conn['password']
  remotepath=conn['remotepath']
  

  if findSvc('eshing-svc',conn):
    #hpmt storage
    datadira = rootdir + '/node' + str(conn['nidx']) + '/hpmtAccount'
    datadirs = rootdir + '/node' + str(conn['nidx']) + '/hpmtStorage'

    result =subprocess.check_output(["mkdir", "-p","-m","777", datadira+"/db-1"], stderr=subprocess.STDOUT)
    print(result)
    result =subprocess.check_output(["mkdir", "-p","-m","777", datadirs+"/db-1"], stderr=subprocess.STDOUT)
    print(result)

    shutil.copyfile( path + "config.json", datadira + "/config.json")
    shutil.copyfile( path + "shard-1.json", datadira + "/shard-1.json")
    file_replace(datadira + "/config.json","sharePath",remotepath+"svcs/hpmtAccount/shard-1.json")
    file_replace(datadira + "/shard-1.json","dbPathContext",remotepath+"svcs/hpmtAccount/db-1/lvdb_")

    shutil.copyfile( path + "config.json", datadirs + "/config.json")
    shutil.copyfile( path + "shard-1.json", datadirs + "/shard-1.json")
    file_replace(datadirs + "/config.json","sharePath",remotepath+"svcs/hpmtStorage/shard-1.json")
    file_replace(datadirs + "/shard-1.json","dbPathContext",remotepath+"svcs/hpmtStorage/db-1/lvdb_")

  remoteBase=remotepath+'svcs'
  command = 'mkdir -p '+remoteBase
  ret = get_output(ssh_client, command)
  print(ret)

  remoteBaseBin=remotepath+'svcs/bin'
  command = 'mkdir -p '+remoteBaseBin
  ret = get_output(ssh_client, command)
  print(ret)

  commands = scpCommands(False,conn['ispwd'],conn['password'],path + "log.toml",user+"@" + conn['ip'] + ":" + remoteBaseBin)
  result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
  print(result)
  
  #copy starter
  commands = scpCommands(False,conn['ispwd'],conn['password'],path + "bins/starter",user+"@" + conn['ip'] + ":" + remoteBaseBin)
  result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
  print(result)

  for svc in conn['svcs']:
    print(svc)
    if len(svc)==0:
      continue
    commands = scpCommands(False,conn['ispwd'],conn['password'],path + "bins/"+svc,user+"@" + conn['ip'] + ":" + remoteBaseBin)
    result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
    print(result)
	
    if svc=='eshing-svc':
      datadira = rootdir + '/node' + str(conn['nidx']) + '/hpmtAccount'
      datadirs = rootdir + '/node' + str(conn['nidx']) + '/hpmtStorage'

      commands = scpCommands(True,conn['ispwd'],conn['password'],datadira,user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
      commands = scpCommands(True,conn['ispwd'],conn['password'],datadirs,user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
    elif svc=='frontend-svc':
      result = subprocess.check_output(["cp" , "-r", path + "config_template.yml",monacoTmp + "/config.yml"], stderr=subprocess.STDOUT)
      print(result)
      result = subprocess.check_output(["sed" , "-i", "s/zkUrl/"+conn['zkUrl']+"/g",monacoTmp + "/config.yml"], stderr=subprocess.STDOUT)
      print(result)
      commands = scpCommands(False,conn['ispwd'],conn['password'],monacoTmp + "/config.yml",user+"@" + conn['ip'] + ":" + remoteBaseBin)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
    elif svc=='p2p-svc':
      commands = scpCommands(True,conn['ispwd'],conn['password'],rootdir + "/node" + str(conn['nidx']+"/config"),user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
    elif svc=='consensus-svc':
      commands = scpCommands(True,conn['ispwd'],conn['password'],rootdir + "/node" + str(conn['nidx']+"/config"),user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
      commands = scpCommands(True,conn['ispwd'],conn['password'],rootdir + "/node" + str(conn['nidx']+"/data"),user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
    elif svc=='feeder':
      commands = scpCommands(False,conn['ispwd'],conn['password'],monacoTmp + "/af",user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)
    elif svc=='storage-svc':
      commands = scpCommands(False,conn['ispwd'],conn['password'],monacoTmp + "/af",user+"@" + conn['ip'] + ":" + remoteBase)
      result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
      print(result)      
    
    
  if len(conn['svcs'])==0:
    return

  start_concrete_svcs(ssh_client, conn, ppstr1,ppstr2,lanes,p2p_listenaddr,debugmode,basecfg)

  print( ' '+ ','.join(conn['svcs'])+ ' in ' + conn['ip'] + '  install completed ... ')
  return

def create(path,name, n, mnodes, pnodes, connection_info,lanes,ssh_clients,debugmode,basecfg,genesisFile):
  # prepare config files
  monacoTmp = TMPPATH+'/monaco'
  result =subprocess.check_output(["mkdir", "-p", monacoTmp], stderr=subprocess.STDOUT)
  print(result)

  rootdir = monacoTmp + '/' + name
  result =subprocess.check_output(["mkdir", "-p", rootdir], stderr=subprocess.STDOUT)
  print(result)

  result = subprocess.check_output([path +'bins/consensus-svc', 'testnet','--v='+str(n),'--o='+rootdir], stderr=subprocess.STDOUT)
  print(result)

  createCoinbase(rootdir+"/node0/config/genesis.json",monacoTmp+"/coinbase")

  ppstr=getPeerList(rootdir+"/node0/config/config.toml")

  print(ppstr)
  
  ppstr1 = ppstr 
  # rewrite ppstr
  for mnode in mnodes:
    print(mnode)
    ppstr1 = ppstr1.replace('node' + str(mnode['index']),mnode['ip'] )

  print(ppstr1)

  ppstr2 = ppstr 
  # rewrite ppstr
  for pnode in pnodes:
    pnode['p2p_listenaddr'] ='tcp://'+ pnode['ip'] + ':36656'

    print(pnode)
    ppstr2= ppstr2.replace('node' + str(pnode['index']),pnode['ip'] )

  ppstr2= ppstr2.replace('26656','36656')
  print(ppstr2)
  
  #result =subprocess.check_output(["mkdir", "-p", path+"/bin"], stderr=subprocess.STDOUT)
  #print(result)

  
  ###create genesis address file
  mergeFile(path,monacoTmp+'/',genesisFile)

  #initNums=str(int(txnums)+n)
  idx=0
  for conn in connection_info:
    ssh_client=ssh_clients[conn['name']]
    nidx=int(conn['nidx'])-1
    if len(pnodes)>0:
      p2p_listenaddr=pnodes[nidx]["p2p_listenaddr"]
    else:
      p2p_listenaddr=""
    print(p2p_listenaddr)
    idx=idx+1
    t = threading.Thread(target=deploy,name=str(idx) ,args=(path,ppstr1,ppstr2,conn,ssh_client,lanes,p2p_listenaddr,debugmode,basecfg,monacoTmp,rootdir,))  
    t.start() 
    t.join()
  
  #check services start state
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
    print("waiting......") 
    time.sleep(2)
    checkListNext =[]
    for checkItem in checkList:
      ret = get_output(checkItem['client'], 'pidof -s ' + checkItem['svc'])
      if len(ret)>0:
        print('service '+ checkItem['svc'] + ' in '+ checkItem['ip'] +' is ready')
      else:
        checkListNext.append(checkItem)
    checkList=checkListNext
    if queryCounter>4:
      for checkItem in checkList:
         print('service '+ checkItem['svc'] + ' in '+ checkItem['ip'] +' error')
      print('please check detail,or retry')
      return
  

  addminites=len(mnodes)//60+1
  print(addminites)
  now=datetime.datetime.now()
  delta=datetime.timedelta(minutes=addminites)
  n_minites=now+delta
  startTime=n_minites.strftime('%Y-%m-%d_%H:%M:%S')
  print(startTime)

  for node in mnodes:
    conn=node['conn']
    ssh_client=ssh_clients[conn['name']]    
    idx=idx+1
    threadConsensus = threading.Thread(target=startConsensus,name=str(idx) ,args=(ssh_client,conn,ppstr1,lanes,debugmode,startTime,))  
    threadConsensus.start() 
    threadConsensus.join()

  #check query state
  if len(queryIp)>0:
    queryUrl='http://'+ queryIp +':8080/blocks/latest?access_token=access_token&transactions=false'
    print(queryUrl)
    willQuery=True

    while willQuery:
      time.sleep(5)
      res = requests.get(queryUrl)
      print(res.text)
      if res.text.startswith('{"block"'):
        willQuery=False
  
  print("cluster start completed ...")
  
  return

def startConsensus(ssh_client,conn,ppstr1,lanes,debugmode,startTime):
  mqaddr=conn['mqaddr']
  mqaddr2=conn['mqaddr2']
  nidx=conn['nidx']
  nname=conn['nname']
  remotepath=conn['remotepath']
  
  outputmod=' 2>'+remotepath+'nohup.out '
  if debugmode:
    outputmod=' >'+remotepath+'nohup.out 2>&1'

  command = remotepath +'svcs/bin/starter '+ startTime +' nohup '+ remotepath +'svcs/bin/consensus-svc start --home='+ remotepath +'svcs --mqaddr='+ mqaddr +' --mqaddr2='+ mqaddr2 +' --nidx='+ nidx +' --nname='+ nname +' --logcfg='+ remotepath +'svcs/bin/log.toml --instrumentation.prometheus=true --instrumentation.prometheus_listen_addr=:19001  --p2p.persistent_peers=\'' + ppstr1 + '\'' +' --concurrency='+ lanes + outputmod+' &'
  
  print(command)
  ret = get_output(ssh_client, command)
  print(ret)

def setupkafkas(path, connection_info,ssh_clients):
  idx=0
  for conn in connection_info:
    if conn['kafka']=='false':
      continue
    print(conn['ip'])
    
    ssh_client=ssh_clients[conn['name']]
    
    idx=idx+1
    thread = threading.Thread(target=setupkafka,name='k'+str(idx) ,args=(path,conn,ssh_client,))  
    thread.start() 
    thread.join()
    
def scpCommands(copyDirector,isPwd,pwd,local,remote):
    commands = []
    if isPwd:
      commands.append("sshpass")
      commands.append("-p")
      commands.append(pwd)
      commands.append("scp")
    else:
      commands.append("scp")
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

  commands = scpCommands(True,conn['ispwd'],conn['password'],localdir,conn['username']+"@" + conn['ip'] + ":" + conn['remotepath'])
  result = subprocess.check_output(commands, stderr=subprocess.STDOUT)
  print(result)

  
  destPath=conn['remotepath']+'kafka'

  command = 'cd '+conn['remotepath']+'kafka;chmod 755 *.sh'
  ret = get_output(ssh_client, command)

  command = 'echo -e "'+destPath+'\\n1\\n'+conn['localip']+'\\n" | '+destPath+'/installkfk.sh'
  ret = get_output(ssh_client, command)

  command = destPath+'/kafka/start.sh'
  ret = get_output(ssh_client, command)

  command = destPath+'/kafka/maketopic.sh '+ str(conn["partitions"])
  ret = get_output(ssh_client, command)

  print('kafka in ' + conn['ip'] + '  install completed ... ')
  

def clearkafkas(connection_info,ssh_clients):
  idx=0
  for conn in connection_info:
    if conn['kafka']=='false':
      continue
    print(conn['ip'])
    
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

  print('kafka in ' + conn['ip'] + '  clear completed ... ')

# hostname -> {ip, username, password}
connection_info =[] #{}

n = 0
name = 'TBD'

action = sys.argv[1]
filename = sys.argv[2]



mnodes = []
pnodes = []
execs = {}
ppts = {}
basecfg = {}

ispwd=True
debugmod=False
for arg in sys.argv:
  if arg=='-debugmod':
    debugmod=True
  elif arg=='-sshkey':
    ispwd=False

print(ispwd)
print(debugmod)


with open(filename) as config_file:
  config = json.load(config_file)
  name = config['name']
  print(name)

  basecfg['rpm']=config['rpm']

  mindex = 0
  pindex = 0
  for host in config['hosts']:
    ci = {}
    ci['name'] = host['name']
    ci['ip'] = host['ip']
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
      mindex += 1
      mnodes.append(mnode)
    if 'p2p-svc' in ci['svcs'] :
      pnode = {}
      pnode['ip'] = ci['ip']
      pnode['index'] = pindex
      pindex += 1
      pnodes.append(pnode)
    connection_info.append(ci)
  print(connection_info)

  print(mnodes)
  n = mindex
  print(n)


for conn in connection_info:
  if 'scheduling-svc' in conn['svcs'] and conn['nname'] in execs:
    conn["execAddrs"]=execs[conn['nname']]

for conn in connection_info:
  if conn['kafka']=='true' and conn['nname'] in ppts:
    conn["partitions"]=ppts[conn['nname']]

ssh_clients = init_ssh_clients(connection_info)


if action == 'start':
  
  path = os.getcwd()+'/' 
  lanes = sys.argv[3]
  genesisFile=sys.argv[4]

  setupkafkas(path,connection_info,ssh_clients)
  create(path,name, n, mnodes,pnodes, connection_info,lanes,ssh_clients,debugmod,basecfg,genesisFile)
elif action == 'restart':
  path = os.getcwd()+'/' 
  lanes = sys.argv[3]
  genesisFile=sys.argv[4]
  
  stopall(connection_info,ssh_clients)
  do_clean(ssh_clients)
  clearkafkas(connection_info,ssh_clients)


  setupkafkas(path,connection_info,ssh_clients)
  create(path,name, n, mnodes,pnodes, connection_info,lanes,ssh_clients,debugmod,basecfg,genesisFile)

elif action == 'stop':
  stopall(connection_info,ssh_clients)
elif action == 'stopall':
  stopall(connection_info,ssh_clients)
  path = os.getcwd()+'/' 
  do_clean(ssh_clients)
  clearkafkas(connection_info,ssh_clients)
