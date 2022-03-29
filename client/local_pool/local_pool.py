import requests
import base64
import json
import redis
import redis_connection
import os
import sys
import time
from typing import List
from pprint import pprint
from copy import deepcopy
from local_model_update import update_local_model, format_training_data

sys.path.append(str(os.environ.get("FLEXHTTP")))

from myUtil import RedisTable, RedisRow


def get_not_updated_records() -> (List[dict], List[dict]):
    incr_training_table = RedisTable(redis_connection.redis_pool, redis_connection.table_incr_training)
    incr_training_data = incr_training_table.get_all_rows()
    raw_records = list()
    for primekey in incr_training_data:
        data_row = RedisRow(redis_connection.redis_pool, primekey)
        raw_records.append(data_row.get_val_dict())
    records = deepcopy(raw_records)
    for i, record in enumerate(records):
        grouped_network_conditions = _group_network_conditions(record)
        records[i].update(grouped_network_conditions)

    return raw_records, records


def _group_network_conditions(network_condition_dict):
    """
    :rtype: dict
        key: bandwidth, loss_rate, rtt
    """
    grouped_network_condition_dict = deepcopy(network_condition_dict)
    bandwidth_partitions = [ # 1, 10, 50, 100
        (0, 5), 
        (5, 25), 
        (25, 75), 
        (75, 10000)
    ]
    loss_rate_partitions = [ # 0.01, 0.10, 1.00, 5.00
        (0, 0.05), 
        (0.05, 0.50), 
        (0.50, 2.50), 
        (2.50, 10000)
    ]
    rtt_partitions = [ # 30, 100, 300, 500
        (0, 50), 
        (50, 200), 
        (200, 400), 
        (400, 10000)
    ]
    for (a, b) in bandwidth_partitions:
        if a <= float(grouped_network_condition_dict['bandwidth']) < b:
            grouped_network_condition_dict['bandwidth'] = str((a, b))
            break
    for (a, b) in loss_rate_partitions:
        if a <= float(grouped_network_condition_dict['loss_rate']) < b:
            grouped_network_condition_dict['loss_rate'] = str((a, b))
            break
    for (a, b) in rtt_partitions:
        if a <= float(grouped_network_condition_dict['rtt']) < b:
            grouped_network_condition_dict['rtt'] = str((a, b))
            break
    return grouped_network_condition_dict


def get_primekey_of_not_updated_records(records) -> List[dict]:
    primekeys = []
    for record in records:
        primekeys.append({
            "link": record["link"],
            "bandwidth": record["bandwidth"],
            "loss_rate": record["loss_rate"],
            "rtt": record["rtt"]
        })
    
    # Remove the duplicates
    seen = set()
    primekeys_without_duplicates = []
    for primekey in primekeys:
        t = tuple(primekey.items())
        if t not in seen:
            seen.add(t)
            primekeys_without_duplicates.append(primekey)
    
    return primekeys_without_duplicates


def clear_table_incr_training():
    incr_training_table = RedisTable(redis_connection.redis_pool, redis_connection.table_incr_training)
    incr_training_data = incr_training_table.get_all_rows()
    for primekey in incr_training_data:
        incr_training_table.delete_row(primekey)


def update_table_request_logs():
    incr_training_table = RedisTable(redis_connection.redis_pool, redis_connection.table_incr_training)
    incr_training_data = incr_training_table.get_all_rows()

    request_logs_table = RedisTable(redis_connection.redis_pool, redis_connection.table_request_logs)
    for primekey in incr_training_data:
        request_logs_table.add_row(primekey)


def update_table_incr_training_with_labels(local_trace_records, local_trace_records_primekey, global_trace_records):
    """
    :param global_trace_records: dict
        key: tuple of link and the network features (link, bandwidth, loss_rate, rtt)
        val: dict{'plt_http2': <float>, 'plt_quic': <float>}
    """
    # TODO: 
    # 1. avg_plts的初始化应当使用旧表格里的数据，现在还没有这么用
    # 2. incr_training_with_labels 中旧数据的label没有更新

    # Compute avg_plts as the final label of the (link, network_condition) instance
    avg_plts = dict()
    for primekey in local_trace_records_primekey: # initialize with the global trace records
        primekey_network_conditions = {
            'link': primekey['link'],
            'bandwidth': primekey['bandwidth'],
            'loss_rate': primekey['loss_rate'],
            'rtt': primekey['rtt']
        }
        plt_http2 = global_trace_records[tuple(primekey_network_conditions.items())]['plt_http2']
        plt_quic = global_trace_records[tuple(primekey_network_conditions.items())]['plt_quic']
        avg_plts[tuple(primekey_network_conditions.items())] = {
            'plt_http2': plt_http2,
            'plt_quic': plt_quic
        }

    for record in local_trace_records: # compute the average plts using local trace records
        primekey = tuple({
            "link": record["link"],
            "bandwidth": record["bandwidth"],
            "loss_rate": record["loss_rate"],
            "rtt": record["rtt"]
        }.items())

        if record['protocol'] == 'http2':
            if avg_plts[primekey]['plt_http2'] is None:
                avg_plts[primekey]['plt_http2'] = float(record['PLT'])
            else:
                avg_plts[primekey]['plt_http2'] = (float(avg_plts[primekey]['plt_http2']) + float(record['PLT']))/2
        elif record['protocol'] == 'quic':
            if avg_plts[primekey]['plt_quic'] is None:
                avg_plts[primekey]['plt_quic'] = float(record['PLT'])
            else:
                avg_plts[primekey]['plt_quic'] = (float(avg_plts[primekey]['plt_quic']) + float(record['PLT']))/2
    

    # Update the table of the training data with labels
    incr_training_table = RedisTable(redis_connection.redis_pool, redis_connection.table_incr_training)
    incr_training_data = incr_training_table.get_all_rows()
    incr_training_with_labels_table = RedisTable(redis_connection.redis_pool, redis_connection.table_incr_training_with_labels)
    for primekey in incr_training_data:
        record = RedisRow(redis_connection.redis_pool, primekey).get_val_dict()
        network_condition_group = _group_network_conditions({
            "bandwidth": record["bandwidth"],
            "loss_rate": record["loss_rate"],
            "rtt": record["rtt"]
        })
        grouped_primekey = tuple({
            "link": record["link"],
            "bandwidth": network_condition_group["bandwidth"],
            "loss_rate": network_condition_group["loss_rate"],
            "rtt": network_condition_group["rtt"]
        }.items())
        if grouped_primekey not in avg_plts:
            continue
        if (avg_plts[grouped_primekey]['plt_http2'] is None) or (avg_plts[grouped_primekey]['plt_quic'] is None):
            continue

        incr_training_with_labels_table.add_row('label_{}'.format(primekey))
        incr_training_with_labels_row = RedisRow(redis_connection.redis_pool, 'label_{}'.format(primekey))
        incr_training_with_labels_row.update_val({ # The label row
            "link": record["link"],
            "time": record["time"],
            "protocol": record["protocol"],
            "bandwidth": record["bandwidth"],
            "loss_rate": record["loss_rate"],
            "rtt": record["rtt"],
            "all_cnt": record['all_cnt'],
            "all_size": record['all_size'],
            "text_cnt": record['text_cnt'],
            "text_size": record['text_size'],
            "css_cnt": record['css_cnt'],
            "css_size": record['css_size'],
            "js_cnt": record['js_cnt'],
            "js_size": record['js_size'],
            "img_cnt": record['img_cnt'],
            "img_size": record['img_size']
        })

        if avg_plts[grouped_primekey]['plt_http2'] < avg_plts[grouped_primekey]['plt_quic'] + 2*float(record["rtt"])*0.001:
            incr_training_with_labels_row.update_val({'label': 0})
        else:
            incr_training_with_labels_row.update_val({'label': 1})
    

def get_dicts_incr_training_with_labels():
    incr_training_with_labels_table = RedisTable(redis_connection.redis_pool, redis_connection.table_incr_training_with_labels)
    incr_training_with_labels_data = incr_training_with_labels_table.get_all_rows()
    incr_training_with_labels_data_dicts = list()
    for primekey in incr_training_with_labels_data:
        record = RedisRow(redis_connection.redis_pool, primekey).get_val_dict()    
        incr_training_with_labels_data_dicts.append(record)
    return incr_training_with_labels_data_dicts



if __name__ == "__main__":
    # API地址

    # url = "http://10.20.0.3:12345/pooltrans"
    url = "http://" + str(os.environ.get("AGENTIP")) + ":12345/pooltrans"

    # 发送post请求到服务器端
    # input: URL和net condition
    # output: web features, label, avg PLT for H3 and H2


    urls_counter = 0
    while True:
        raw_not_updated_records, not_updated_records = get_not_updated_records()  # list 
        primekey_of_not_updated_records = get_primekey_of_not_updated_records(not_updated_records)  # list 
        data = {"key":primekey_of_not_updated_records, "trace": not_updated_records, "raw_trace": raw_not_updated_records}
        res = requests.post(url, json=data)

        print(res.status_code)
        # print(res.content)


        if not res.status_code == 200:
            print("[error] trace transfer failed")
            continue
        else:
            update_table_request_logs()
        

        # 读取global trace
        global_trace_plt_result = eval(res.content)
        # 根据返回的global avg PLT和本地的local PLT 构建本地label，
        update_table_incr_training_with_labels(not_updated_records, primekey_of_not_updated_records, global_trace_plt_result)

        # 更新本地模型
        urls_counter += len(not_updated_records)
        print(urls_counter)
        if urls_counter >= 50:
            incr_training_with_labels_data_dicts = get_dicts_incr_training_with_labels()
            update_local_model(local_train_data=format_training_data(incr_training_with_labels_data_dicts), global_url=str(os.environ.get("AGENTIP")))
            urls_counter = 0
        
        # 清除 incr_training
        clear_table_incr_training()

        time.sleep(50)
