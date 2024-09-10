import os
import sys
import re
import json
import redis
import numpy as np

sys.path.append(str(os.environ.get("FLEXHTTP") + '/myUtil'))
from myRedis import RedisTable, RedisRow

class LocalCache:
    def __init__(self) -> None:
        self.redis_pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)

        self.table_link_features = "table_link_features"
        self.table_domain_features = "table_domain_features"
        self.table_select_res = "table_select_res"
        self.table_incr_training = "table_incr_training"

    def is_table_select_res_hit(self, link):
        res_table = RedisTable(self.redis_pool, self.table_select_res)
        return res_table.search_row('res_' + link)


    def get_protocol_selection_cache(self, link):
        link_res_row = RedisRow(self.redis_pool, prime_key='res_' + link)
        return link_res_row.get_val_of_key(key="protocol")


    def is_table_link_features_hit(self, link):
        link_features_table = RedisTable(self.redis_pool, self.table_link_features)
        return link_features_table.search_row(link)


    def get_web_features_cache(self, link):
        res_table = RedisRow(self.redis_pool, prime_key=link)
        web_features_cache = res_table.get_val_dict()
        web_features_cache.pop('link')
        web_features_cache.pop('domain')

        # The values' type in the return dict are all string, 
        # so change them into int.
        for key, val in web_features_cache.items():
            web_features_cache[key] = int(val)
        return web_features_cache    

    def update_table_link_features(self, link, domain, web_features):
        link_table = RedisTable(self.redis_pool, self.table_link_features)
        link_table.update_row(link)

        link_row = RedisRow(self.redis_pool, link)
        link_row.update_val({
            "link": link,
            "domain": domain,
            "all_cnt": web_features['all_cnt'],
            "all_size": web_features['all_size'],
            "text_cnt": web_features['text_cnt'],
            "text_size": web_features['text_size'],
            "css_cnt": web_features['css_cnt'],
            "css_size": web_features['css_size'],
            "js_cnt": web_features['js_cnt'],
            "js_size": web_features['js_size'],
            "img_cnt": web_features['img_cnt'],
            "img_size": web_features['img_size']
        })


    def update_table_domain_features(self, domain, time, bandwidth, loss_rate, rtt):
        domain_table = RedisTable(self.redis_pool, self.table_domain_features)
        domain_table.update_row(domain)

        domain_row = RedisRow(self.redis_pool, domain)
        domain_row.update_val({
            "time": time,
            "bandwidth": bandwidth,
            "loss_rate": loss_rate,
            "rtt": rtt
        })


    def update_table_select_res(self, link, time, protocol):
        select_res_table = RedisTable(self.redis_pool, self.table_select_res)
        select_res_table.update_row('res_' + link)

        select_res_row = RedisRow(self.redis_pool, 'res_' + link)
        select_res_row.update_val({
            "link": link,
            "time": time,
            "protocol": protocol
        })


    def update_table_incr_training(self, link, time, protocol, plt, bandwidth, loss_rate, rtt, web_features):
        incr_training_table = RedisTable(self.redis_pool, self.table_incr_training)
        incr_training_table.update_row('incr_' + link + '_' + str(time))

        incr_training_row = RedisRow(self.redis_pool, 'incr_' + link + '_' + str(time))
        incr_training_row.update_val({
            "link": link,
            "time": time,
            "protocol": protocol,
            "PLT": plt,
            "bandwidth": bandwidth,
            "loss_rate": loss_rate,
            "rtt": rtt,
            "all_cnt": web_features['all_cnt'],
            "all_size": web_features['all_size'],
            "text_cnt": web_features['text_cnt'],
            "text_size": web_features['text_size'],
            "css_cnt": web_features['css_cnt'],
            "css_size": web_features['css_size'],
            "js_cnt": web_features['js_cnt'],
            "js_size": web_features['js_size'],
            "img_cnt": web_features['img_cnt'],
            "img_size": web_features['img_size']
        })

