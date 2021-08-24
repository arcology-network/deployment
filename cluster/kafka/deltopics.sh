#!/usr/bin/env bash

#/home/wei/work/kafka/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic local-txs
#/home/wei/work/kafka/bin/kafka-topics.sh --delete --topic log --zookeeper localhost:2181


host=localhost:2181

$exec --delete --zookeeper $host --topic msgexch

$exec --delete --zookeeper $host --topic local-txs
$exec --delete --zookeeper $host --topic remote-txs
$exec --delete --zookeeper $host --topic block-txs

$exec --delete --zookeeper $host --topic chkd-message

$exec --delete --zookeeper $host --topic exec-rcpt-hash
$exec --delete --zookeeper $host --topic inclusive-txs
$exec --delete --zookeeper $host --topic local-block

$exec --delete --zookeeper $host --topic genesis-apc
$exec --delete --zookeeper $host --topic reaping-list

$exec --delete --zookeeper $host --topic euresults
$exec --delete --zookeeper $host --topic receipts
$exec --delete --zookeeper $host --topic access-records


$exec --delete --zookeeper $host --topic executing-logs
$exec --delete --zookeeper $host --topic meta-block

$exec --delete --zookeeper $host --topic selected-txs
$exec --delete --zookeeper $host --topic selected-msgs

$exec --delete --zookeeper $host --topic spawned-relations

$exec --delete --zookeeper $host --topic checked-txs
