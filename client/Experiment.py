import os
import sys
import re
import json
import time
import pickle
import numpy as np
import random
import argparse

from ClientBrowser import SeleniumBrowser, ChromeBrowser
from LocalCache import LocalCache
from ModelManager import ModelManager
from TraceGenerator import TraceGenerator
from NetMeasurer import NetMeasurer


class Experiment:
    def __init__(self, args) -> None:

        self.server_n = len(str(os.getenv("SERVERIPS")).split(","))
        self.experiment_name = args.experiment_name + \
            ("_bootstrap" if args.bootstrap == "True" else "")
        self.instance = args.instance
        self.repeat_count = 1
        self.methods = ['flexhttp', 'quic', 'http2']
        self.bootstrap = True if args.bootstrap == "True" else False
        self.online = False
        self.model_num_classes = 'two_classes'  # or 'three_classes'
        self.local_update = False
        self.results_save_rootdir = os.path.join(
            str(os.getenv("HOME")), 'exp_results', 'FlexHTTP_results')
        self.harfiles_save_rootdir = os.path.join(
            str(os.getenv("HOME")), 'exp_results', 'har_results')

        with open(os.path.join(str(os.getenv("HOME")), "FlexHTTP", "myUtil", "ai_model", "RF.pkl"), 'rb') as fp:
            self.selection_res = pickle.load(fp)

        # Settings for ClientBrowser
        self.client_type = 'selenium'  # or 'chrome'
        self.timeout = 400  # Timeout for single page
        self.way_of_get_metric = 'lighthouse'  # lighthouse, chrome-har-capturer
        self.way_of_get_page_features = 'static_file'
        self.chromedriver_dir = os.path.join(
            str(os.getenv("FLEXHTTP")), "client", 'chromedriver')
        if self.client_type == 'selenium':
            self.client_browser = SeleniumBrowser(
                timeout=self.timeout,
                experiment_name=self.experiment_name,
                instance=self.instance,
                harfiles_save_rootdir=self.harfiles_save_rootdir,
                way_of_get_metric=self.way_of_get_metric,
                way_of_get_page_features='static_file',
                chromedriver_dir=self.chromedriver_dir)
        elif self.client_type == 'chrome':
            # TODO: Add pure Chrome as client browser
            pass

        # Settings for LocalCache
        self.local_cache = LocalCache()

        # Settings for ModelManager
        self.model_manager = ModelManager()

        # Settings for NetMeasurer
        self.is_fixed_network_instance = True
        self.net_measurer = NetMeasurer(
            self.instance, self.is_fixed_network_instance)

        # Settings for NetChanger
        # if not self.is_fixed_network_instance:
        #    self.net_changer = NetChanger(self.instance)

        # Settings for TraceGenerator
        self.use_existing_trace = True
        self.existing_trace = "data/trace.pickle"
        self.url_nums = 240
        self.trace_length = 2400
        self.trace_generator = TraceGenerator(
            use_existing_trace=self.use_existing_trace,
            url_nums=self.url_nums,
            trace_length=self.trace_length,
            existing_trace=self.existing_trace
        )

    def start_experiment(self):
        print('Experiment name: {}'.format(self.experiment_name))
        print('Instance: {}'.format(self.instance))
        print('Method: {}'.format(self.methods))
        print('Bootstrap: {}'.format(self.bootstrap))
        print('Online: {}'.format(self.online))
        print('Local update: {}'.format(self.local_update))
        self._make_experiment_log_dir()
        trace = self.trace_generator.generate_trace()

        for experiment_index in range(self.repeat_count):
            self.experiment_start_time = time.time()

            for method in self.methods:
                print('[info] {}'.format(method))
                self.workflow(experiment_index+1, method, trace)
                time.sleep(2)

            self.experiment_end_time = time.time()

            self._write_single_workflow_log(experiment_index)

    def workflow(self, experiment_index, method, trace):
        self.client_browser.init_browser()

        plts = list()  # Record the plts

        for index, url in enumerate(trace):
            print('[{}]'.format(index), end=' ')
            self.workflow_for_url(index, url, method, plts)

            if len(plts) % 30 == 0:  # record every 30 results
                with open(os.path.join(self.results_save_rootdir, self.experiment_name, self.instance, 'plts_{}_{}.json'.format(method, experiment_index)), 'w', encoding='utf-8') as fp:
                    json.dump(plts, fp, indent=4)

        self._write_plt_json(plts, method, experiment_index)

    def _write_plt_json(self, plts, method, experiment_index):
        # Write plts log
        with open(os.path.join(self.results_save_rootdir, self.experiment_name, self.instance, 'plts_{}_{}.json'.format(method, experiment_index)), 'w', encoding='utf-8') as fp:
            json.dump(plts, fp, indent=4)

    def workflow_for_url(self, index, url, method, plts: list) -> None:
        self.client_browser.clean_cache()

        # the server to send request to
        server_num = 0
        domain, link = self._get_domain_link_from_url(url)
        rtt, loss_rate, bandwidth = self.net_measurer.get_network_conditions(
            server_num)
        print("rtt: {}, loss_rate: {}, bandwidth: {}, server_num: {}".format(
            rtt, loss_rate, bandwidth, server_num))

        if method == 'http2':
            request_result = self.workflow_for_url_http2(
                index, domain, link, rtt, loss_rate, bandwidth)
        elif method == 'quic':
            request_result = self.workflow_for_url_quic(
                index, domain, link, rtt, loss_rate, bandwidth)
        elif method == "flexhttp":
            (request_result_1, selected_protocol) = self.workflow_for_url_flexhttp(
                index, domain, link, rtt, loss_rate, bandwidth, server_num)
            request_result_1["selected"] = True
            request_result_1["rtt"] = rtt
            request_result_1["loss"] = loss_rate
            request_result_1["band"] = bandwidth
            request_result_1["server_num"] = self.client_browser.server_dict[server_num]

            plts.append(request_result_1)
            if selected_protocol == "http2":
                request_result_2 = self.workflow_for_url_quic(
                    index, domain, link, rtt, loss_rate, bandwidth, server_num=server_num)
            else:
                request_result_2 = self.workflow_for_url_http2(
                    index, domain, link, rtt, loss_rate, bandwidth, server_num=server_num)

            request_result_2["selected"] = False
            request_result_2["rtt"] = rtt
            request_result_2["loss"] = loss_rate
            request_result_2["band"] = bandwidth
            request_result_2["server_num"] = self.client_browser.server_dict[server_num]
            plts.append(request_result_2)
            return
        elif method == 'flexhttp_static':
            request_result = self.workflow_for_url_flexhttp_static(
                index, domain, link, rtt, loss_rate, bandwidth)

        plts.append(request_result)

    def workflow_for_url_flexhttp_static(self, index, domain, link, rtt, loss_rate, bandwidth):
        selected_protocol = self.selection_res[index]
        print(selected_protocol)
        plt, timing = self.client_browser.send_request(
            domain, link, protocol=selected_protocol)
        if plt == -1:
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'plt': plt,
                'error': 'Error in sending request'
            }
        else:
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'plt': plt,
                'timing': timing
            }
        return request_result

    def workflow_for_url_flexhttp(self, index, domain, link, rtt, loss_rate, bandwidth, server_num):
        self.local_cache.update_table_domain_features(
            domain=domain,
            time=time.time(),
            bandwidth=bandwidth,
            loss_rate=loss_rate,
            rtt=rtt
        )
        if self.local_cache.is_table_link_features_hit(link):
            web_features = self.local_cache.get_web_features_cache(link)
            web_features.update({
                'band': bandwidth,
                'loss': loss_rate,
                'rtt': rtt
            })
            if self.bootstrap is True:
                selected_protocol = 'http2' if (
                    random.randint(0, 1) == 0) else 'quic'
            elif self.online is False:
                if self.model_num_classes == 'two_classes':
                    selected_protocol = self.model_manager.predict_protocol(
                        model=self.model_manager.clf_dt_2rtt,
                        features=web_features,
                        feature_category='all'
                    )
                elif self.model_num_classes == 'three_classes':
                    selected_protocol = self.model_manager.predict_protocol(
                        model=self.model_manager.clf_dt_multi,
                        features=web_features,
                        feature_category='all_multi'
                    )
                    if selected_protocol == 'random':
                        # selected_protocol = 'random/http2' if (random.randint(0, 1) == 0) else 'random/quic'
                        selected_protocol = 'random/http2'
            else:
                if self.local_update is True:
                    if index % 20 == 0:
                        self.model_manager.read_is_model_update_needed()
                        print(self.model_manager.is_model_update_needed)
                        if self.model_manager.is_model_update_needed == 1:
                            self.model_manager.update_RF_model()
                            self.model_manager.reset_is_model_update_needed()
                            print('[info] Model updated.')
                    selected_protocol = self.model_manager.predict_protcocol(
                        model=self.model_manager.clf_dt,
                        features=web_features,
                        feature_category='all'
                    )
                else:
                    if index % 40 == 0:
                        self.model_manager.update_RF_global_model()
                    selected_protocol = self.model_manager.predict_protocol(
                        model=self.model_manager.clf_dt_global,
                        features=web_features,
                        feature_category='all'
                    )

            print(selected_protocol)
            self.local_cache.update_table_select_res(
                link=link, time=time.time(), protocol=selected_protocol)
            selected_protocol = selected_protocol.replace('random/', '')
            plt, res = self.client_browser.send_request(
                domain, link, protocol=selected_protocol, server_num=server_num)
        else:  # The first time to request this url
            selected_protocol = 'http2' if (
                random.randint(0, 1) == 0) else 'quic'
            print("no cache hit")
            print(selected_protocol)
            plt, res = self.client_browser.send_request(
                domain, link, protocol=selected_protocol, server_num=server_num)
            try:
                web_features = self.client_browser.get_page_features(domain)
                print(web_features)
                self.local_cache.update_table_link_features(
                    link, domain, web_features)
            except:
                plt = -2

        if plt == -1:  # Error in sending request
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'error': 'Error in sending request'
            }
        elif plt == -2:  # Error finding the webpage features
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'error': 'Error finding the webpage features'
            }
        else:  # Successfully request the url
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'res': res
            }
            self.local_cache.update_table_incr_training(link=link, time=time.time(), protocol=selected_protocol, plt=plt, bandwidth=bandwidth,
                                                        loss_rate=loss_rate, rtt=rtt, web_features=web_features)

        return (request_result, selected_protocol)

    def workflow_for_url_http2(self, index, domain, link, rtt, loss_rate, bandwidth, server_num=1):
        selected_protocol = 'http2'
        plt, res = self.client_browser.send_request(
            domain, link, protocol=selected_protocol, server_num=server_num)
        if plt == -1:
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'error': 'Error in sending request'
            }
        else:
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'res': res
            }
        return request_result

    def workflow_for_url_quic(self, index, domain, link, rtt, loss_rate, bandwidth, server_num=1):
        selected_protocol = 'quic'
        plt, res = self.client_browser.send_request(
            domain, link, protocol=selected_protocol, server_num=server_num)
        if plt == -1:
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'error': 'Error in sending request'
            }
        else:
            request_result = {
                'link': link,
                'time': int(time.time()*1e6),
                'protocol': selected_protocol,
                'res': res
            }
        return request_result

    def _get_domain_link_from_url(self, url):
        url_splits = url.strip().split(',')
        domain = url_splits[0]
        link = url_splits[1]
        return domain, link

    def _make_experiment_log_dir(self):
        try:
            os.makedirs(os.path.join(
                self.results_save_rootdir, self.experiment_name, self.instance))
        except Exception as err:
            pass

        try:
            os.makedirs(os.path.join(self.harfiles_save_rootdir,
                                     self.experiment_name, self.instance))
        except Exception as err:
            pass

    def _write_single_workflow_log(self, experiment_index):
        with open(os.path.join(self.results_save_rootdir, self.experiment_name, self.instance, 'info_{}.json'.format(experiment_index+1)), 'w', encoding='utf-8') as fp:
            json.dump([self.experiment_end_time -
                       self.experiment_start_time], fp, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--instance', type=str,
                        default='100ms-0d01-100M', help="The machine pair instance")
    parser.add_argument('--bootstrap', type=str, default='False',
                        help="Is bootstrap experiment or not")
    parser.add_argument('--experiment_name', type=str,
                        default='20211101', help="Name for this experiment")
    args = parser.parse_args()

    experiment = Experiment(args=args)
    experiment.start_experiment()
