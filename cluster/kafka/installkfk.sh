#!/bin/bash

currentTime=$(date '+%Y-%m-%d %H:%M:%S')
#echo -e "********** please input kafka install path,if not exists auto create"
read kafkainstallpath

if [ ! -d $kafkainstallpath ]; then
   mkdir -p $kafkainstallpath
fi 
if [ ! -d $kafkainstallpath ]; then
  echo "create path $kafkainstallpath is failt！please check permission"
  exit
fi

currentdir=$(cd $(dirname $0); pwd)
ls | grep 'kafka.*[gz]$'
if [ $? -ne 0 ]; then
   echo "********** not found kafka*.tar.gz in $currentdir,please upload!"
   exit
else
   tar -zxvf $currentdir/$(ls | grep 'kafka.*[gz]$') -C $kafkainstallpath
fi

kafkapath=`ls $kafkainstallpath| grep 'kafka.*' | grep -v *.tgz`

echo $kafkapath 
 
mv $kafkapath $kafkainstallpath/kafka
 
confpath=$kafkainstallpath/kafka/config
binpath=$kafkainstallpath/kafka/bin

#echo -e "********** please input kafka node id：unique, such as 1"
read kafkanodename

sed -i "s/^broker.id=0/broker.id=${kafkanodename}/g" $confpath/server.properties

sed -i 's/^#listeners=PLAINTEXT:\/\/:9092/listeners=PLAINTEXT:\/\/:9092/g' $confpath/server.properties
 
cd $kafkainstallpath/kafka
mkdir klogs-1


bak_dir='log.dirs=/tmp/kafka-logs'
new_dir='log.dirs='$kafkainstallpath/kafka/klogs-1

sed -i "s!${bak_dir}!${new_dir}!g" $confpath/server.properties

#sed -i 's/^#delete.topic.enable=true/delete.topic.enable=true/g' $confpath/server.properties

sed -i '56i log.cleanup.policy=delete' $confpath/server.properties

sed -i '57i delete.topic.enable=true' $confpath/server.properties


#echo -e "********** please input localhost ip ：such as 192.168.1.107"
read localip

sed -i '58i advertised.listeners=PLAINTEXT://'$localip':9092' $confpath/server.properties

#sed -i '59i zookeeper.session.timeout.ms =3000' $confpath/server.properties

#sed -i '60i rebalance.max.retries =4' $confpath/server.properties

#sed -i '61i rebalance.backoff.ms =1000' $confpath/server.properties

sed -i '59i message.max.bytes=200000000' $confpath/server.properties

sed -i '60i replica.fetch.max.bytes=204857600' $confpath/server.properties

sed -i '61i fetch.message.max.bytes=204857600' $confpath/server.properties
 
sed -i 's/^#log.retention.bytes=1073741824/log.retention.bytes=1073741824/g' $confpath/server.properties

sed -i 's/^log.retention.hours=168/log.retention.hours=24/g' $confpath/server.properties
 
sed -i 's/^#log.flush.interval.messages=10000/log.flush.interval.messages=10000/g' $confpath/server.properties
 
sed -i 's/^#log.flush.interval.ms=1000/log.flush.interval.ms=1000/g' $confpath/server.properties

param=`cat /proc/cpuinfo | grep "cpu cores"| uniq`
 
bak_count="num.network.threads=3"
new_count="num.network.threads="$((${param:0-1:1}+1))
sed -i "s!${bak_count}!${new_count}!g" $confpath/server.properties
 
bak_io="num.network.threads=3"
new_io="num.network.threads="$((${param:0-1:1}+${param:0-1:1}))
sed -i "s!${bak_io}!${new_io}!g" $confpath/server.properties

#start kafka
sed -i 's/export KAFKA_HEAP_OPTS="-Xmx1G -Xms1G"/export KAFKA_HEAP_OPTS="-Xmx32G -Xms32G"/g' $binpath/kafka-server-start.sh

#maketopic sh

sed -i '6i exec='$kafkainstallpath'/kafka/bin/kafka-topics.sh' $kafkainstallpath/maketopic.sh
mv $kafkainstallpath/maketopic.sh $kafkainstallpath/kafka/maketopic.sh
chmod 755 $kafkainstallpath/kafka/maketopic.sh

#sed -i '6i exec='$kafkainstallpath'/kafka/bin/kafka-topics.sh' $kafkainstallpath/maketopic-2.sh
#mv $kafkainstallpath/maketopic-2.sh $kafkainstallpath/kafka/maketopic-2.sh
#chmod 755 $kafkainstallpath/kafka/maketopic-2.sh

#deltopic.sh
sed -i '7i exec='$kafkainstallpath'/kafka/bin/kafka-topics.sh' $kafkainstallpath/deltopics.sh
mv $kafkainstallpath/deltopics.sh $kafkainstallpath/kafka/deltopics.sh
chmod 755 $kafkainstallpath/kafka/deltopics.sh

#restrat.sh
sed -i '4i basepath='$kafkainstallpath'/kafka' $kafkainstallpath/start.sh
mv $kafkainstallpath/start.sh $kafkainstallpath/kafka/start.sh
chmod 755 $kafkainstallpath/kafka/start.sh

sed -i '4i basepath='$kafkainstallpath'/kafka' $kafkainstallpath/stop.sh
mv $kafkainstallpath/stop.sh $kafkainstallpath/kafka/stop.sh
chmod 755 $kafkainstallpath/kafka/stop.sh

#echo -e "****************************ok,kafka install terminated***********************************************"
