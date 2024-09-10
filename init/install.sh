#!/bin/bash
echo "export FLEXHTTP=${HOME}/FlexHTTP" >> ~/.bashrc
echo "export SERVERIP=10.10.0.1" >> ~/.bashrc
echo "export AGENTIP=10.20.0.3" >> ~/.bashrc
source ~/.bashrc

# Python 3.6
sudo add-apt-repository -y ppa:deadsnakes/ppa 
sudo apt-get update
sudo apt-get remove -y python3.8
sudo apt-get install -y python3.6
sudo apt-get install -y python3-pip
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1

# Python packages
sudo apt install -y python3-dev python3-pip
pip3 install wheel
pip3 install -r ${FLEXHTTP}/init/requirements.txt

# some packages
sudo apt install -y cmake
sudo apt install -y wget
sudo apt install -y psmisc # for command: killall
sudo apt install -y jq # for parsing json
sudo apt install -y iperf # for bandwidth measurement
sudo apt install -y iperf3 # for bandwidth measurement
sudo apt install -y p7zip-full
sudo apt install -y rsync
sudo apt install -y gcc libpq-dev
sudo apt install -y tmux
sudo apt install -y htop


# Node.js v16.13.1
# npm v6.4.1
cd ~
if [ ! -d "dependencies" ]; then
    mkdir dependencies
fi
cd ${HOME}/dependencies
if [ ! -f "node-v16.13.1-linux-x64.tar.xz" ]; then
    wget https://nodejs.org/dist/v16.13.1/node-v16.13.1-linux-x64.tar.xz
    if [ ! -d "node" ] && [ ! -d "node-v16.13.1-linux-x64" ]; then
        tar -xvf node-v16.13.1-linux-x64.tar.xz
        mv node-v16.13.1-linux-x64 node
    fi
fi
sudo cp -frp node/bin/* /usr/bin/
sudo cp -frp node/include/* /usr/include/
sudo cp -frp node/lib/* /usr/lib/
sudo cp -frp node/share/* /usr/share/

# chrome-har-capturer
sudo apt-get -y install npm 
sudo chown -R $(whoami) "$HOME/.npm"
cd $FLEXHTTP/client
if [ ! -d "node_modules" ]; then
    npm install
fi

# install latest nodejs
sudo npm cache clean -f
sudo npm install -g n
sudo n stable

#redis
sudo apt-get install -y pkg-config
cd ${HOME}/dependencies
if [ ! -f "redis-6.0.9.tar.gz" ]; then
    wget http://download.redis.io/releases/redis-6.0.9.tar.gz
    if [ ! -d "redis" ] && [ ! -d "redis-6.0.9" ]; then
        tar -xvf redis-6.0.9.tar.gz
        mv redis-6.0.9 redis
        cd redis/
        make
        make install
    fi
fi

# Caddy
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo tee /etc/apt/trusted.gpg.d/caddy-stable.asc
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy


# Chrome
cd ${HOME}/dependencies
if [ ! -f "google-chrome-stable_current_amd64.deb" ]; then
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
fi
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# Chrome driver
sudo apt-get install unzip
cd $FLEXHTTP/client
ver=$(curl https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
if [ ! -f "chromedriver_linux64.zip" ]; then
    wget "https://chromedriver.storage.googleapis.com/${ver}/chromedriver_linux64.zip"
    if [ ! -f "chromedriver" ]; then
        unzip chromedriver_linux64.zip
    fi
fi

# SSL certification
sudo apt-get install libnss3-tools
cd $HOME/dependencies
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.3/mkcert-v1.4.3-linux-amd64
mv mkcert-v1.4.3-linux-amd64 mkcert
chmod +x mkcert
if [ ! -f "~/.local/share/mkcert" ]; then
    mkdir $HOME/.local/share/mkcert
fi
cp $FLEXHTTP/server/cert/rootCA-key.pem $FLEXHTTP/server/cert/rootCA.pem $HOME/.local/share/mkcert
./mkcert -install
# ./mkcert example.com
# cp ./example.com-key.pem $FLEXHTTP/server/cert/key.pem
# cp ./example.com.pem $FLEXHTTP/server/cert/cert.pem


# dnsmasq
sudo systemctl stop systemd-resolved
sudo apt-get install -y dnsmasq