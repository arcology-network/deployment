#!/usr/bin/env bash

#/home/wei/work/kafka/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic local-txs

#exec=/home/monaco-s7/wei/kafka/bin/kafka-topics.shexec=/home/wei/work/kafka/bin/kafka-topics.sh

host=localhost:2181


$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic msgexch

$exec --create --zookeeper $host --replication-factor 1 --partitions 3 --topic local-txs
$exec --create --zookeeper $host --replication-factor 1 --partitions 3 --topic remote-txs
$exec --create --zookeeper $host --replication-factor 1 --partitions 3 --topic block-txs

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic chkd-message

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic exec-rcpt-hash
$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic inclusive-txs
$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic local-block

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic genesis-apc
$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic reaping-list

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic euresults
$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic receipts

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic executing-logs
$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic meta-block

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic selected-txs
$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic selected-msgs

$exec --create --zookeeper $host --replication-factor 1 --partitions 1 --topic spawned-relations
