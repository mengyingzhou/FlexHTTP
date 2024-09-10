import pandas as pd
import numpy as np
import pickle
import os
import sys
import time
import numpy as np
from sklearn.model_selection import cross_validate
from collections import Counter
from imblearn.over_sampling import RandomOverSampler
import redis_connection

sys.path.append(str(os.environ.get("FLEXHTTP")) + "/client")
sys.path.append(str(os.environ.get("FLEXHTTP")))
from myUtil import RedisTable, RedisRow, sortFImp


def train_RF(data_X, data_Y, max_depth=4, n_jobs=12, out=False):
    ros = RandomOverSampler(random_state=0)

    data_X, data_Y = ros.fit_resample(data_X, data_Y)
    print(Counter(data_Y))
    print(data_X.shape)

    # need a per-trained global model
    # clf = RandomForestClassifier(max_depth=max_depth, n_jobs=12)
    _file = os.path.join(str(os.environ.get("FLEXHTTP")), "myUtil", "global_pool", "global_model.pkl")
    clf = pickle.load(open(_file, 'rb'))
    scores = cross_validate(clf, data_X, data_Y,
                            scoring=['accuracy', 'precision',
                                     'recall', 'f1', 'roc_auc'],
                            cv=10,
                            return_train_score=False)
    clf.fit(data_X, data_Y)
    fImp = sortFImp(clf.feature_importances_)

    return scores, clf


def update_global_model(global_train_data):
    data_X = global_train_data.values[:, 2:].astype(np.float64)
    print("data_X length: {}".format(len(data_X)))
    if len(data_X) == 0:
        print("Available trace list is empty!")
        return
    data_Y = global_train_data.values[:, 0].astype(np.int32)
    scores, global_model = train_RF(data_X, data_Y, max_depth=8)

    # store local model to file
    _file = os.path.join(str(os.environ.get("FLEXHTTP")), "myUtil", "global_pool", "global_model.pkl")
    pickle.dump(global_model, open(_file, 'wb'))

    return global_model


def get_format_training_data():
    global_trace_table = RedisTable(redis_connection.redis_pool, redis_connection.table_global_trace)
    global_trace_rows = global_trace_table.get_all_rows()
    global_trace_dicts = list()
    for primekey in global_trace_rows:
        data_row = RedisRow(redis_connection.redis_pool, primekey)
        data_dict = data_row.get_val_dict()
        label = _get_label_of_trace(data_dict)
        if label is None:
            continue
        else:
            data_dict.update({'label': label})
            global_trace_dicts.append(data_dict)

    return pd.DataFrame(global_trace_dicts, columns=[
        "label",
        "link",
        "all_cnt",
        "all_size",
        "text_cnt",
        "text_size",
        "css_cnt",
        "css_size",
        "js_cnt",
        "js_size",
        "img_cnt",
        "img_size",
        "rtt",
        "loss_rate",
        "bandwidth"
    ])


bandwidth_partitions = [  # 1, 10, 50, 100
    (0, 5),
    (5, 25),
    (25, 75),
    (75, 10000)
]
loss_rate_partitions = [  # 0.01, 0.10, 1.00, 5.00
    (0, 0.05),
    (0.05, 0.50),
    (0.50, 2.50),
    (2.50, 10000)
]
rtt_partitions = [  # 30, 100, 300, 500
    (0, 50),
    (50, 200),
    (200, 400),
    (400, 10000)
]


def _get_label_of_trace(trace):
    for (a, b) in bandwidth_partitions:
        if a <= float(trace['bandwidth']) < b:
            bandwidth_str = str((a, b))
            break
    for (a, b) in loss_rate_partitions:
        if a <= float(trace['loss_rate']) < b:
            loss_rate_str = str((a, b))
            break
    for (a, b) in rtt_partitions:
        if a <= float(trace['rtt']) < b:
            rtt_str = str((a, b))
            break

    try:
        global_trace_with_label_row = RedisRow(redis_connection.redis_pool, "label_{}_{}_{}_{}".format(
            trace['link'], bandwidth_str, loss_rate_str, rtt_str
        ))
        if float(global_trace_with_label_row.get_val_of_key('plt_http2')) < float(global_trace_with_label_row.get_val_of_key('plt_quic')) + 2*float(trace['rtt'])*0.001:
            return 0
        else:
            return 1
    except Exception as err:
        return None


if __name__ == "__main__":
    while True:
        time.sleep(600)  # sleep 10 minutes
        x = get_format_training_data()
        update_global_model(x)
        print('updated')
