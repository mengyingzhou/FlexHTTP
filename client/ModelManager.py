import os
import sys
import pickle

sys.path.append(str(os.environ.get("FLEXHTTP")))

from myUtil import get_RF_model, dt_predict


class ModelManager:
    def __init__(self) -> None:

        self.reset_is_model_update_needed()

        # flexhttp features for all features
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "RF.pkl")
        self.clf_dt = get_RF_model(filedir=_file)
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "global_model.pkl")
        self.clf_dt_global = get_RF_model(
            filedir=_file)

        # flexhttp features for all features - 2RTT two classes
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "RF_2RTT_SI.pkl")
        self.clf_dt_2rtt = get_RF_model(filedir=_file)

        # the initial default model in global
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "global_model.pkl")
        self.clf_dt_global_default = get_RF_model(filedir=_file)

        # flexhttp features for network features
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "RF_network_only.pkl")
        self.clf_dt_network = get_RF_model(filedir=_file)

    def predict_protocol(self, model, features, feature_category):
        """
        :rtype: string, 'http2' or 'quic'
        """
        return dt_predict(
            clf=model,
            features=features,
            feature_category=feature_category
        )

    def update_RF_model(self):
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "RF.pkl")
        self.clf_dt = get_RF_model(filedir=_file)

    def update_RF_global_model(self):
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "global_model.pkl")
        self.clf_dt_global = get_RF_model(
            filedir=_file)

    def reset_is_model_update_needed(self):
        self.is_model_update_needed = 0
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "is_model_update_needed.pickle")
        with open(_file, 'wb') as fp:
            pickle.dump(self.is_model_update_needed, fp)

    def read_is_model_update_needed(self):
        _file = os.path.join(str(os.environ.get("FLEXHTTP")),
                             "myUtil", "ai_model", "is_model_update_needed.pickle")
        with open(_file, 'rb') as fp:
            self.is_model_update_needed = pickle.load(fp)
        return self.is_model_update_needed
