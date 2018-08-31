# coding=utf-8

"""
代理池，实现自动抓取、更新、验证代理。
"""
import time
import json

from . import checker
from .utils import get_redis, redis_http_usable, redis_https_usable


class ProxyPool:
    def __init__(self):
        self._redis = get_redis()
        self._checker = checker.Checker()
        self._checker.start()

    def is_ready(self):
        proxies_http_num = self._redis.scard(redis_http_usable)
        proxies_https_num = self._redis.scard(redis_https_usable)

        if proxies_http_num == 0 or proxies_https_num == 0:
            return False

        return True

    def quit_scheduler(self):
        self._checker.quit_scheduler()

    @property
    def http(self):
        while not self.is_ready():
            time.sleep(0.5)

        proxy_str = self._redis.srandmember(redis_http_usable)
        proxy = json.loads(proxy_str)

        return '{}:{}'.format(proxy['ip'], proxy['port'])

    @property
    def https(self):
        while not self.is_ready():
            time.sleep(0.5)

        proxy_str = self._redis.srandmember(redis_https_usable)
        proxy = json.loads(proxy_str)

        return '{}:{}'.format(proxy['ip'], proxy['port'])


if __name__ == '__main__':
    p = ProxyPool()

    for i in range(10):
        print(p.http, p.https, sep=', ')
        time.sleep(0.5)
