import os
import sys
import re
import json
import numpy as np
import time
import redis
import json

pool = redis.ConnectionPool(host="localhost", port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)

duration = 0
with open(os.path.join(str(os.getenv("FLEXHTTP")), "client", "data", "measurement_configs.json"), "r") as f:
    data = json.load(f)
    duration = data["dynamic_network"]["duration"]


class NetMeasurer:
    def __init__(self, instance, is_fixed_network_instance) -> None:
        self.instance = instance
        self.is_fixed_network_instance = is_fixed_network_instance
        # if it's the first time to measure dynamic network, need to sleep some time waiting for the measurement module to finish
        self.is_first_time = True

        if self.is_fixed_network_instance:
            self.instance_rtt = float(
                self.instance.split('-')[0].replace('ms', ''))
            self.instance_loss = float(
                self._d_string_trans(self.instance.split('-')[1]))
            # self.instance_band = float(self.instance.split('-')[2].replace('m', ''))
            self.instance_band = float(self._d_string_trans(
                self.instance.split('-')[2].replace('m', '')))

            self.instance_network_conditions = {
                'rtt': self.instance_rtt,
                'loss': self.instance_loss,
                'band': self.instance_band
            }
        else:
            self.instance_network_conditions = {
                'rtt': "500",
                'loss': "0d01",
                'band': "10"
            }

    def _d_string_trans(self, string_with_d_char):
        string_with_d_char = string_with_d_char.replace('d', '.')
        return float(string_with_d_char)

    def get_network_conditions(self, server_num):
        """
        :rtype: (int, float, float) 
            (bandwidth, loss_rate, rtt)
        """
        if self.is_fixed_network_instance:
            return self.instance_rtt, self.instance_loss, self.instance_band
        else:
            if self.is_first_time:
                self.is_first_time = False
                time.sleep(3 * duration)

            return r.get("rtt{}".format(server_num)), r.get("loss{}".format(server_num)), r.get("bandwidth{}".format(server_num))
