#!/bin/bash

sudo killall redis-server python3
rm -rf /usr/local/redis_data/dump_agent.rdb
