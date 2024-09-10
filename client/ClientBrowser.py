import os
import sys
import re
import json
import time
import pandas as pd
import numpy as np

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service


class ClientBrowser:
    def __init__(self, timeout, experiment_name, instance, harfiles_save_rootdir, way_of_get_metric='chrome-har-capturer', way_of_get_page_features='static_file') -> None:
        self.timeout = timeout
        self.experiment_name = experiment_name
        self.instance = instance
        self.harfiles_save_rootdir = harfiles_save_rootdir
        self.way_of_get_metric = way_of_get_metric
        self.way_of_get_page_features = way_of_get_page_features

        self.page_features_static = pd.read_csv('data/web_features_raw.csv')

        self.server_dict = {0: "", 1: "as.", 2: "au.", 3: "eu.", 4: "sa.", 5: "us."}
        self.http2_port = 10001
        self.quic_port = 10002

    def get_ttfb_from_har(self, filename):
        file_try_count = 0
        while True:
            if os.path.exists(filename):
                with open(filename, 'r') as fin:
                    data = json.load(fin)
                    try:
                        return data["log"]["entries"][0]["timings"]["wait"]
                    except:
                        return -1
            if file_try_count > 400:
                return -1
            file_try_count += 1
            time.sleep(1)

    def get_plt_from_har(self, data, metric='LatestOKTime'):
        try:
            if metric == 'LatestOKTime':
                return self._LatestOKTime(data)
            elif metric == 'onLoadTime':
                return self._onLoadTime(data)
            elif metric == 'onContentLoadTime':
                return self._onContentLoadTime(data)
        except Exception as err:
            print(err)
            return -1

    def _onLoadTime(self, data):
        res = data["pages"][0]["pageTimings"]["onLoad"]
        if res is None:
            return -1
        return res

    def _onContentLoadTime(self, data):
        res = data["pages"][0]["pageTimings"]["onContentLoad"]
        if res is None:
            return -1
        return res

    def _LatestOKTime(self, data):
        start = self._transfer(data["pages"][0]["startedDateTime"])
        end = start
        count = 0
        for entry in data["entries"]:
            code = entry["response"]["status"]
            if code == 404:
                continue
            count += 1
            t = self._transfer(entry["startedDateTime"])+entry["time"]
            dns = entry["timings"]["dns"]
            if dns != -1:
                t -= dns
            end = max(end, t)
            # print(entry["startedDateTime"], entry["time"], t)
        if count == 0:
            return -1
        else:
            return end-start

    def _transfer(self, st):  # unit: ms
        p = st.index('.')
        numeric = "0"+st[p:-1]
        timestamp = (self._toTimestamp(st[:p])+float(numeric))*1000
        return timestamp

    def _toTimestamp(self, strtime):
        timeformat = "%Y-%m-%dT%H:%M:%S"
        localOffset = -int(time.mktime(
            # begin time for different os:
            # Linux: 1970-01-01T00:00:00
            # Windows: 1970-01-01T08:00:00
            # Choose the respective begin time for the os you're running
            time.strptime('1970-01-01T00:00:00', timeformat)))
        # Beijing: localOffset=28800

        offset = localOffset
        return int(time.mktime(time.strptime(strtime, timeformat)))+localOffset-offset


class SeleniumBrowser(ClientBrowser):
    def __init__(self, timeout, experiment_name, instance, harfiles_save_rootdir, way_of_get_metric, way_of_get_page_features, chromedriver_dir) -> None:
        super().__init__(timeout, experiment_name, instance,
                         harfiles_save_rootdir, way_of_get_metric, way_of_get_page_features)
        self.chromedriver_dir = chromedriver_dir

    def init_browser(self):
        # Quit existing client browser
        try:
            self.driver.quit()
            print('[info] Selenium webdriver quit successful')
            os.system(
                "ps -ef | grep chrome | awk '{print $2}' | xargs kill -9")
        except:
            print(
                '[warning] Selenium webdriver quit failed. There might be no existing selenium webdriver.')
            os.system(
                "ps -ef | grep chrome | awk '{print $2}' | xargs kill -9")

        try:
            # Start a new selenium webdriver
            option = webdriver.ChromeOptions()
            option.add_argument('headless')
            option.add_argument('disable-gpu')
            option.add_argument('--remote-debugging-port=9222')
            option.add_argument('--enable-quic')
            option.add_argument('--origin-to-force-quic-on=example.com:10002')
            # chromedriver_dir = '/usr/local/bin/chromedriver'
            self.driver = webdriver.Chrome(
                executable_path=self.chromedriver_dir, chrome_options=option)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.set_script_timeout(self.timeout)
            self.driver.execute_cdp_cmd(
                "Network.setCacheDisabled", dict({'cacheDisabled': True}))
        except:
            self.init_browser()

    def clean_cache(self):
        self.driver.execute_cdp_cmd("Network.clearBrowserCookies", dict({}))
        self.driver.execute_cdp_cmd("Network.clearBrowserCache", dict({}))

    def send_request(self, domain, link, protocol, server_num=0, with_performance_timing=False):
        self.http2_url_header = "https://{}example.com:".format(self.server_dict[server_num]) + \
            str(self.http2_port) + "/alexa_top240/"
        self.quic_url_header = "https://{}example.com:".format(self.server_dict[server_num]) + \
            str(self.quic_port) + "/alexa_top240/"

        if protocol == 'quic':
            url = self.quic_url_header + domain + '/' + link
        else:
            url = self.http2_url_header + domain + '/' + link
        print(url)
        try:
            if self.way_of_get_metric == 'chrome-har-capturer':
                filename = os.path.join(self.harfiles_save_rootdir, self.experiment_name, self.instance, '{}_{}_{}.har'.format(
                    protocol, link[:-1], str(time.time() * 1e7)))
                os.system("{} --url {} --output {}".format(
                    os.path.join(str(os.environ.get("FLEXHTTP")),
                                 "client", "browse_and_cap_har.js"),
                    url,
                    filename
                ))
                timing = self.get_timing_from_har(filename)
                plt = timing['tplt']
                ttfb = self.get_ttfb_from_har(filename)

                # Delete the har file to save disk space
                os.system("rm -rf {}".format(filename))
                if with_performance_timing:
                    performance_timing = self.driver.execute_script(
                        "return window.performance.timing")
                    timing.update(performance_timing)
                return plt, (timing, ttfb)
            elif self.way_of_get_metric == 'lighthouse':
                os.makedirs(os.path.join(str(os.getenv("HOME")), 'exp_results',
                            'json_results', self.experiment_name, self.instance), exist_ok=True)
                filename = os.path.join(str(os.getenv("HOME")), 'exp_results', 'json_results', self.experiment_name,
                                        self.instance, '{}_{}_{}.json'.format(protocol, link[:-1], str(time.time() * 1e7)))
                os.system("{} --url {} --output {}".format(
                    os.path.join(str(os.environ.get("FLEXHTTP")),
                                 'client', 'browse_with_lighthouse.js'),
                    url,
                    filename
                ))
                timing = self.get_timing_from_lighthouse_json(filename)
                # Delete the json file to save disk space
                # os.system("rm -rf {}".format(filename))
                si = timing['speed_index']
                return si, timing  # si used as warning when -1

        except Exception as err:
            print(err)
            self.init_browser()
            plt = -1
            ttfb = -1
            timing = {}
            return plt, (timing, ttfb)

    def get_timing_from_har(self, filename):
        file_try_count = 0
        while True:
            if os.path.exists(filename):
                with open(filename, 'r') as fin:
                    data = json.load(fin)
                    data = data['log']

                tplt = self.get_plt_from_har(data=data, metric='onLoadTime')
                nplt = self.get_plt_from_har(
                    data=data, metric='LatestOKTime')
                tplt = tplt/1000 if tplt != -1 else tplt
                nplt = nplt/1000 if tplt != -1 else nplt
                break

            if file_try_count > 400:
                tplt, nplt = 400, 400
                break
            file_try_count += 1
            time.sleep(1)
        timing = {
            'nplt': nplt,
            'tplt': tplt,
            'filename': filename
        }
        return timing

    def get_timing_from_lighthouse_json(self, filename):
        file_try_count = 0
        while True:
            if os.path.exists(filename):
                with open(filename, 'r') as fin:
                    data = json.load(fin)
                    data = data['audits']

                first_contentful_paint = data['first-contentful-paint']['numericValue']
                speed_index = data['speed-index']['numericValue']
                interactive = data['interactive']['numericValue']
                page_load_time = data['metrics']['details']['items'][0]['observedLoad']
                break

            if file_try_count > 400:
                first_contentful_paint = -1
                speed_index = -1
                interactive = -1
                break
            file_try_count += 1
            time.sleep(1)

        timing = {
            'speed_index': speed_index,
            'first_contentful_paint': first_contentful_paint,
            'interactive': interactive,
            'plt': page_load_time,
            'filename': filename
        }
        return timing

    def get_page_features(self, link):
        if self.way_of_get_page_features == 'static_file':
            link_row = self.page_features_static[self.page_features_static['site'] == link]
            page_features = link_row.to_dict('records')[0]
            return page_features
        elif self.way_of_get_page_features == 'browser':
            # TODO: add function to get page features from current browser
            pass


class ChromeBrowser(ClientBrowser):
    # TODO:
    def __init__(self) -> None:
        pass

    def init_browser(self):
        pass


if __name__ == "__main__":
    client_browser = SeleniumBrowser(
        timeout=400,
        experiment_name="goodluck",
        instance="100ms-0d01-100M",
        way_of_get_metric="chrome-har-capturer",
        way_of_get_page_features="static_file")

    client_browser.init_browser()
    client_browser.clean_cache()
    time.sleep(86400)