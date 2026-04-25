#!/bin/bash

redisdir="${HOME}/dependencies/redis"

sudo mkdir -p /usr/local/redis_data
sudo chmod -R 777 /usr/local/redis_data

sleep 2s
nohup ${redisdir}/src/redis-server ${FLEXHTTP}/agent/redis.conf --daemonize yes &
cd ${FLEXHTTP}/agent
nohup python3 "${FLEXHTTP}/agent/global_pool.py" &
nohup python3 "${FLEXHTTP}/agent/global_model_update.py" &
