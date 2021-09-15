#!/usr/bin/env bash

cp -r env/login_template.txt env/login.txt

sed -i 's/hostip/'$1'/g' env/login.txt
sed -i 's/hostusername/'$2'/g' env/login.txt
sed -i 's/hostuserpwd/'$3'/g' env/login.txt
sed -i 's!hostpath!'$4'!g' env/login.txt

cp -r cluster/testnet_template.json cluster/testnet.json

sed -i 's/hostip/'$1'/g' cluster/testnet.json
sed -i 's/hostusername/'$2'/g' cluster/testnet.json
sed -i 's/hostuserpwd/'$3'/g' cluster/testnet.json
sed -i 's!hostpath!'$4'!g' cluster/testnet.json
