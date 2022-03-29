import os
import sys
import csv
import time
import numpy as np
from datetime import datetime


timeformat = "%Y-%m-%dT%H:%M:%S"
localOffset = -int(time.mktime(
    # begin time for different os:
    # Linux: 1970-01-01T00:00:00
    # Windows: 1970-01-01T08:00:00
    # Choose the respective begin time for the os you're running
    time.strptime('1970-01-01T08:00:00', timeformat)))
# Beijing: localOffset=28800


def toDatetime(timestamp, offset=localOffset):
    return datetime.utcfromtimestamp(timestamp+offset).strftime(timeformat)
# Beijing: offset=28800
# toDateTime(timestamp): timestamp->localtime
# toDateTime(timestamp, 0): timestamp->utc time


def toTimestamp(strtime, offset=localOffset):
    return int(time.mktime(time.strptime(strtime, timeformat)))+localOffset-offset
# Beijing: offset=28800
# toTimestamp(strtime): localtime->timestamp
# toTimestamp(strtime, 0): utc time->timestamp


netcond = ['rtt', 'loss', 'band']
webstruct = ['all_cnt',
             'all_size',
             'text_cnt',
             'text_size',
             'css_cnt',
             'css_size',
             'js_cnt',
             'js_size',
             'img_cnt',
             'img_size']
allAttrs = webstruct + netcond
Features = [netcond, webstruct, allAttrs]


def readMLFile(filename, keys, label='time'):
    data_X = []
    data_Y = []
    with open(filename, "r") as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            line = []
            for key in keys:
                line.append(int(row[key]))
            data_X.append(line)
            data_Y.append(int(row[label]))
    return (np.asarray(data_X), np.asarray(data_Y))


def sortFImp(v):
    n = len(v)
    fImp = []
    for i in range(0, n, 1):
        fImp.append((i, v[i]))
    fImp.sort(key=lambda x: x[1], reverse=True)
    return fImp
