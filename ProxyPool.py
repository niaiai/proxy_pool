# coding=utf-8

"""
代理池，实现自动抓取、更新、验证代理。
"""
import time
import json

import redis

from . import checker


class ProxyPool:
    def __init__(self):
        self._redis = redis.Redis()
        self._checker = checker.Checker()
        self._checker.start()

    def is_ready(self):
        proxies_http_num = self._redis.scard('proxies_http_usable')
        proxies_https_num = self._redis.scard('proxies_https_usable')

        if proxies_http_num == 0 or proxies_https_num == 0:
            return False

        return True

    @property
    def http(self):
        while not self.is_ready():
            time.sleep(0.01)

        proxy_str = self._redis.spop('proxies_http_usable')
        self._redis.sadd('proxies_http_usable', proxy_str)
        proxy = json.loads(proxy_str)

        return '{}:{}'.format(proxy['ip'], proxy['port'])

    @property
    def https(self):
        while not self.is_ready():
            time.sleep(0.01)

        proxy_str = self._redis.spop('proxies_https_usable')
        self._redis.sadd('proxies_https_usable', proxy_str)
        proxy = json.loads(proxy_str)

        return '{}:{}'.format(proxy['ip'], proxy['port'])

if __name__ == '__main__':
    p = ProxyPool()

    for i in range(10):
        print(p.http, p.https, sep=', ')
        time.sleep(0.5)
