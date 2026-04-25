#!/bin/bash

bash "${FLEXHTTP}/client/scripts/clientStop.sh"
# sudo sh -c "echo ${SERVERIP}'\texample.com\n' >> '/etc/hosts'"
sudo bash -c "echo -e '127.0.0.1\tlocalhost\n::1\tlocalhost\n${SERVERIP}\texample.com'> /etc/hosts"

sudo sh -c "echo 'nameserver 127.0.0.1' > /etc/resolv.conf"  1>/dev/null 2>&1
echo "updated hosts & resolv.conf"

sudo mkdir -p /usr/local/redis_data
sudo chmod -R 777 /usr/local/redis_data/
sudo mkdir -p /usr/local/ai_model
sudo chmod -R 777 /usr/local/ai_model/

rm -rf /usr/local/ai_model/RF.pkl
cp ${FLEXHTTP}/myUtil/ai_model/global_model.pkl /usr/local/ai_model/RF.pkl
echo "client inited"
