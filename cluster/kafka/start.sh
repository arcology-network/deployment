#!/usr/bin/env bash

#basepath=/home/monaco-s7/wei/kafka


$basepath/bin/zookeeper-server-start.sh -daemon $basepath/config/zookeeper.properties

$basepath/bin/kafka-server-start.sh -daemon $basepath/config/server.properties
