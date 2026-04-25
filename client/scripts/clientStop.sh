echo "[info]Run Kill on client"
sudo killall clientInit.sh clientStart.sh python3 iperf iperf3 1>/dev/null 2>&1
ps -ef | grep chrome | awk '{print $2}' | xargs sudo kill -9 1>/dev/null 2>&1
sudo killall redis-server 1>/dev/null 2>&1
sudo killall dnsmasq 1>/dev/null 2>&1
