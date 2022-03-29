import os
import numpy as np
import pickle
import requests
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score, precision_score, recall_score
from copy import deepcopy



def update_local_model(local_train_data, global_url='10.20.0.3'):
    # fetch  global model
    url = 'http://' + global_url + ':12345/download/global_model.pkl'
    r = requests.get(url, allow_redirects=True)
    print(type(r.content))
    _ = open('/usr/local/ai_model/global_model.pkl', 'wb').write(r.content)
    # with open('/usr/local/ai_model/global_model.pkl', 'wb') as fp:
    #     pickle.dump(r.content, fp)
    global_model = pickle.load(open('/usr/local/ai_model/global_model.pkl','rb'))


    # retraining
    data_X = local_train_data.values[:,2:].astype(np.float64)
    if len(data_X) == 0:
        return 
    data_Y = local_train_data.values[:,0].astype(np.int32)
    local_model = deepcopy(global_model)
    local_model.fit(data_X, data_Y)

    # store local model to file
    pickle.dump(local_model, open('/usr/local/ai_model/RF.pkl','wb+'))

    # set is_model_update_needed flag
    is_model_update_needed = 1
    with open('/usr/local/ai_model/is_model_update_needed.pickle', 'wb') as fp:
        pickle.dump(is_model_update_needed, fp)

    return local_model


def format_training_data(data_dicts):
    return pd.DataFrame(data_dicts, columns=[
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
