# Network Deployment

## 1. Prerequisites

1. Ubuntu 20.04
2. Python 3.x
3. sshpass
4. ansible

## 2. Install Dependencies

### 2.1. On Premises

Modify login.txt manually according to your network setup.

| Field            | Description     |
| ---------------- | --------------- |
| ip               | host ip address |
| ansible_ssh_user | ssh user        |
| ansible_ssh_pass | ssh passwd      |

Under the env directory of the network installer directory, run the command below to install dependencies on the hosting machines.

```shell
$ ansible-playbook -i login.txt install.yml
```

### 2.2. On AWS

Under the aws directory of the network installer directory, use genhosts.py to create the login.txt automatically.

```shell
$ python3 genhosts.py host.json ubuntu ../env/login.txt
```

| Argument         | Description   |
| ---------------- | ------------- |
| ubuntu           | AWS user name |
| ../env/login.txt | output file   |

Under the env directory of the network installer directory, run the command below to install dependencies on the hosting machines

```shell
$ ansible-playbook -i login.txt install.yml
```

After the execution of the above commands, the system will prompt you to copy the transaction files to the docker container in which Ammolite is installed.

```shell
$ scp -i private_key_file -r ../txs root@x.x.x.x:/data
$ ssh -p 32768 root@x.x.x.x
```

## 3. Starting the Network

### 3.1. On Premises

Modify testnet.json manually according to your network setup.

|Field| Description  |
|---|---|
|"name":"s6",						|Host name|
|"ip":"192.168.1.106",				|External IP|
|"localip":"192.168.1.106",			|Internal IP|
|"username":"ansible",				|Username|
|"password":"ansible",				|Password or A Private key file|
|"mqaddr2":"192.168.1.108:9092",	|MQ server for transactions|
|"mqaddr":"192.168.1.109:9092",		|MQ server for control messages|
|"nidx":"1",						|Node cluster ID|
|"nname":"node1",					|Node cluster name|
|"nthread":"4",						|Number of threads|
|"insid":"1",						|Instance ID（only for exec-svc）|
|"zkUrl":"192.168.1.108:2181",		|zookeeper address|
|"remotepath":"/home/monaco/",		|Target path|
|"kafka":"false",					|Is this a kafka server|
|"svcs":["exec-svc","generic-hashing-svc"] |Services to install|

Under the cluster directory of the network installer directory,run the command below to install testnet and start it.

```shell
$ python3 svcsInstaller.py restart testnet.json 4 ../genesis_accounts_5m.txt
```

| Argument                   | Description                            |
| -------------------------- | -------------------------------------- |
| restart                    | action type:stop/stopall/atart/restart |
| testnet.json               | configuration file for testnet         |
| 4                          | concurrency                            |
| ../genesis_accounts_5m.txt | genesis account file                   |

### 3.2. On AWS

Under the aws directory of the network installer directory,use gentestnet.py to create the testnet.json automatically.

```shell
$ python3 gentestnet.py host.json ubuntu ../cluster/testnet.json 50000 testnet 2 4 /data
```

|Argument| Description|
|---|---|
|ubuntu                     |aws user name|
|../cluster/testnet.json    |output file|
|50000                      |max txs per block|
|2                          |number of node clusters on the testnet|
|4                          |concurrency|
|data                       |remote path|

Under the cluster directory of the network installer directory,run the command below to install testnet and start it.

```shell
$ python svcsInstaller.py restart testnet.json 4 ../genesis_accounts_5m.txt -sshkey
```

| Argument                   | Description                            |
| -------------------------- | -------------------------------------- |
| restart                    | action type:stop/stopall/atart/restart |
| testnet.json               | configuration file for testnet         |
| 4                          | concurrency                            |
| ../genesis_accounts_5m.txt | genesis account file                   |
| -sshkey                    | flag for aws                           |

