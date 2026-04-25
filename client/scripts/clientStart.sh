#!/bin/bash
bash "${FLEXHTTP}/client/scripts/clientStop.sh"

# dnsmasq
sudo dnsmasq --conf-file=${FLEXHTTP}/client/scripts/dnsmasq.conf

# redis
redisdir="${HOME}/dependencies/redis"
sleep 5s
nohup ${redisdir}/src/redis-server ${FLEXHTTP}/client/scripts/redis.conf --daemonize yes

# clientStart.sh
sleep 5s
mkdir -p ${HOME}/log
logpath="${HOME}/log"

# get instance information
HOSTNAME=`hostname`
array=(${HOSTNAME//./ })
instance=${array[0]: 6}
echo "network is $instance"

# set experiment name
if [ -z "$2" ]
then
    echo "empty experiment name, using date time as name"
    name=$(date '+%Y-%m-%d-%H-%M-%S') # if experiment name is not set, use current time as name
else
    name=$2
fi
echo "name is $name"

# start Experiment
cd ${FLEXHTTP}/client
python3 -u Experiment.py --instance=${instance} --experiment_name=${name} --bootstrap=${3} 1>${logpath}/python_${instance}.log 2>&1 &

cd ${FLEXHTTP}/client/local_pool
python3 -u local_pool.py 1>${logpath}/agent_${instance}.log 2>&1 &

cd ${FLEXHTTP}/client
python3 -u MeasureDynamicNet.py 1>${logpath}/dynamicnet_${instance}.log 2>&1 &
