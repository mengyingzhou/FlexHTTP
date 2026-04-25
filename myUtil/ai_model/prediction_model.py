import pickle

_webstruct = ['all_cnt', 'all_size', 'text_cnt', 'text_size', 'css_cnt', 'css_size',
             'js_cnt', 'js_size', 'img_cnt', 'img_size']

_network_condition = ['rtt', 'loss', 'band']

_all_features = _webstruct + _network_condition

def get_RF_model(filedir):
    with open(filedir, 'rb') as fp:
        model = pickle.load(fp)
    return model


def dt_predict(clf, features, feature_category='all'):
    data_X = _webfeatures_transform_dict_to_list(features, feature_category)
    if feature_category == 'all_multi':
        predict_y = clf.predict([data_X])[0]
        if predict_y == 1:
            return "random"
        elif predict_y == 2:
            return "http2"
        elif predict_y == 3:
            return "quic"
    else:
        predict_y = clf.predict([data_X])[0]
        if predict_y == 1:
            return "quic"
        else:
            return "http2"

def _webfeatures_transform_dict_to_list(web_features, feature_category):
    import numpy as np
    data_X = list()
    if feature_category == 'all':
        for feature in _all_features:
            data_X.append(web_features[feature])
    elif feature_category == 'all_multi':
        for feature in _all_features:
            data_X.append(web_features[feature])
    elif feature_category == 'network':
        for feature in _network_condition:
            data_X.append(web_features[feature])
    elif feature_category == 'webpage':
        for feature in _webstruct:
            data_X.append(web_features[feature])
    return np.asarray(data_X)
