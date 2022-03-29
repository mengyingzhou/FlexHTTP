#!/bin/bash

caddypath="/usr/local/caddy"

sudo killall caddy 1>/dev/null 2>&1

# use "-E" flag to preserve environment variable when using sudo
caddy run --config "${FLEXHTTP}/server/CaddyfileHttp2" 1>/dev/null 2>&1 &
caddy run --config "${FLEXHTTP}/server/CaddyfileQuic" 1>/dev/null 2>&1 &

sudo killall iperf iperf3 1>/dev/null 2>&1
nohup iperf -s 1>/dev/null 2>&1 &

echo "caddy running"
