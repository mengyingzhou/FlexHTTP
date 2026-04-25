import os
import sys
import re
import json
import random
import pickle
import numpy as np


class TraceGenerator:
    def __init__(self, use_existing_trace: bool, url_nums: int, trace_length: int, existing_trace="data/trace.pickle") -> None:
        self.use_existing_trace = use_existing_trace
        self.url_nums = url_nums
        self.trace_length = trace_length
        self.existing_trace = existing_trace

    def generate_trace(self) -> list:
        """get websites that needs to be visited"""
        if self.use_existing_trace:
            return self.generate_existing_trace()
        else:
            return self.generate_new_trace()

    def generate_existing_trace(self):
        with open(self.existing_trace, 'rb') as fp:
            trace = pickle.load(fp)
        if len(trace) < self.trace_length:
            print('[warning] The desired trace length is larger than exisitng trace data. Finally generate trace with length of {}'.format(len(trace)))
            return trace
        else:
            return trace[:self.trace_length]

    def generate_new_trace(self):
        assert self.trace_length/self.url_nums == self.trace_length//self.url_nums
        url_repeats = self.trace_length//self.url_nums
        with open('data/pages_list.txt', 'r', encoding='utf-8') as fp:
            urls = fp.readlines()
            assert self.url_nums <= len(urls)

        urls = urls[:self.url_nums]
        trace = list()
        for i in range(self.url_nums):
            trace.extend([urls[i] for _ in range(url_repeats)])

        # random.shuffle(trace)
        return trace


if __name__ == "__main__":
    tg = TraceGenerator(
        use_existing_trace=False,
        url_nums=240,
        trace_length=2400,
    )
    trace = tg.generate_new_trace()
    with open('data/trace.pickle', 'wb') as fp:
        pickle.dump(trace, fp)
