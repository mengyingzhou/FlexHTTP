"""
Get dynamic network status: rtt, loss rate, and bandwidth

This file is run independently from the experiment python script.

One big problem regarding dynamic network measurement is that the price for bandwidth is too high, so an idle interval must be set.

rtt and loss rate are got through `ping`, ping server by `duration` and record them into tmp_json_path, with the help of the script `ping_to_json.sh` from https://github.com/richardimaoka/ping-to-json. Then the json file is parsed by `jq` and rtt and loss rate are saved into redis.

bandwidth is got through `iperf2`, and the bandwidth is also saved into redis.
"""

import os
import time
import redis
import multiprocessing
import json


# load interval and duration configurations from measurement_configs.json
with open(os.path.join(str(os.getenv("FLEXHTTP")), "client", "data", "measurement_configs.json"), 'r') as f:
    data = json.load(f)
    interval = data["dynamic_network"]["interval"]
    duration = data["dynamic_network"]["duration"]

# connect to redis
pool = redis.ConnectionPool(host="localhost", port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)


def get_rtt_loss_rate(info):
    """
    get rtt and loss rate by ping and ping_to_json.sh
    results saved to redis "loss" and "rtt"
    info: {'ip_addr': ip_addr, 'index': index}, use dict rather than two parameters to bypass multiprocessing library's one-parameter rule
    """
    ip_addr = info['ip_addr']
    index = info['index']

    json_script_path = os.path.join(
        str(os.getenv("FLEXHTTP")), "client", "ping-to-json", "ping_to_json.sh")
    # tmp files save text ping results, and will be deleted after use
    tmp_json_path = os.path.join(
        str(os.getenv("FLEXHTTP")), "client", "ping{}.json".format(index))
    tmp_txt_path = os.path.join(
        str(os.getenv("FLEXHTTP")), "client", "ping{}.txt".format(index))

    os.system("ping -c {} {} | {} > {}".format(duration, ip_addr,
              json_script_path, tmp_json_path))
    os.system("cat {} | jq '.rtt_summary' | jq '.packet_loss_percentage' >> {}".format(
        tmp_json_path, tmp_txt_path))
    # get loss rate from tmp text file and save to redis
    if os.path.exists(tmp_txt_path):
        fp = open(tmp_txt_path, "r")
        output = fp.read()
        fp.close()
        os.remove(tmp_txt_path)
        r.set("loss{}".format(index), int(output))

    os.system("cat {} | jq '.rtt_statistics' | jq '.avg'  | jq '.value' >> {}".format(
        tmp_json_path, tmp_txt_path))
    # get rtt from tmp text file and save to redis
    if os.path.exists(tmp_txt_path):
        fp = open(tmp_txt_path, "r")
        output = fp.read()
        fp.close()
        os.remove(tmp_txt_path)
        r.set("rtt{}".format(index), float(output[1:-2]))
    os.remove(tmp_json_path)


def get_bandwidth(info):
    """
    get bandwidth to ip_addr by iperf2
    results saved to redis "bandwidth"
    info: {'ip_addr': ip_addr, 'index': index}, use dict rather than two parameters to bypass multiprocessing library's one-parameter rule
    """
    ip_addr = info['ip_addr']
    index = info['index']

    tmp_txt_path_1 = os.path.join(
        str(os.getenv("FLEXHTTP")), "client", "bandtmp{}.txt".format(index))
    tmp_txt_path_2 = os.path.join(
        str(os.getenv("FLEXHTTP")), "client", "band{}.txt".format(index))
    awk_script_path = os.path.join(
        str(os.getenv("FLEXHTTP")), "client", "awk.py")

    # get bandwidth from iperf2, results saved to tmp files, which will be deleted after use
    os.system("iperf --format MBytes -c {} -i 1 -t {} | tee {}".format(ip_addr,
                                                                       duration, tmp_txt_path_1))
    os.system(
        "python3 {} {} {}".format(awk_script_path, tmp_txt_path_1, tmp_txt_path_2))

    avg = 0
    with open(tmp_txt_path_2, "r") as f:
        lines = f.readlines()
        lines = lines[:-1]  # remove last line which is total bandwdith
        n = len(lines)
        tot = 0
        for line in lines:
            tot += float(line)
        avg = tot / n
    band = avg
    r.set("bandwidth{}".format(index), band)
    os.remove(tmp_txt_path_1)
    os.remove(tmp_txt_path_2)


while True:
    ip_addrs = str(os.getenv("SERVERIPS")).split(
        ",")  # like SERVERIPS=1.1.1.1,2.2.2.2,3.3.3.3
    for index, ip_addr in enumerate(ip_addrs):
        multiprocessing.Process(target=get_rtt_loss_rate,
                                args=({'ip_addr': ip_addr, 'index': index + 1},)).start()
        multiprocessing.Process(target=get_bandwidth,
                                args=({'ip_addr': ip_addr, 'index': index + 1},)).start()

    time.sleep(interval)
