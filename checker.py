# coding=utf-8

import time
import logging
import threading
import itertools
from queue import Queue

import redis
from apscheduler.schedulers.background import BackgroundScheduler

from . import crawler
from . import parser
from .tester import Tester


class Checker:
    def __init__(self):
        self._logger = logging.getLogger('pool.checker')
        self._redis = redis.Redis()
        self._tester = Tester(5)

        self._crawlers = []
        for p in parser.parsers:
            queue = Queue()
            c = crawler.Crawler(p, queue)
            worker = threading.Thread(target=c.start)
            worker.start()

            self._crawlers.append(queue)

        self._check()

    def start(self):
        sched = BackgroundScheduler()
        sched.add_job(self._check, 'cron', minute='*/10')
        sched.start()

    def _check(self):
        """检查可用代理，若数量过少，则更新代理。

        以http代理为例，实际用的代理存放在proxies_http_usable中，开始检查后会将其中的代理送给验证器，验证可用的代理存在proxies_http中，
        若数量过少会启动爬虫，直到proxies_http中可用代理的数量大于某个值之后，再将proxies_http_usable清空，把刚抓取的代理填充进去。
        """
        self._logger.info('start checking proxies')
        self._tester.start()
        # 获取当前可用代理
        proxies_http_usable = []
        for proxy in self._redis.sscan_iter('proxies_http_usable'):
            proxies_http_usable.append(proxy)

        proxies_https_usable = []
        for proxy in self._redis.sscan_iter('proxies_https_usable'):
            proxies_https_usable.append(proxy)

        self._logger.debug('http proxies number: %d', self._redis.scard('proxies_http_usable'))
        self._logger.debug('https proxies number: %d', self._redis.scard('proxies_https_usable'))

        # 清空检查结果缓存，因为在停止爬虫之后验证器稍后才会退出，因此队列中可能用残留的代理
        for i in range(self._redis.scard('proxies_http')):
            self._redis.spop('proxies_http')

        for i in range(self._redis.scard('proxies_https')):
            self._redis.spop('proxies_https')

        # 对可用代理进行验证
        for proxy in itertools.chain(proxies_http_usable, proxies_https_usable):
            self._tester.test(proxy)
        self._tester.test('end')

        while not self._tester.is_done():
            time.sleep(0.01)

        self._logger.debug('usable http proxies number: %d', self._redis.scard('proxies_http'))
        self._logger.debug('usable https proxies number: %d', self._redis.scard('proxies_https'))

        # 可用代理数过少，进行更新
        if self._redis.scard('proxies_http') < 10 or self._redis.scard('proxies_https') < 10:
            [c.put('start') for c in self._crawlers]

            while self._redis.scard('proxies_http') < 10 or self._redis.scard('proxies_https') < 10:
                time.sleep(0.01)
            [c.put('end') for c in self._crawlers]

            pipe = self._redis.pipeline()
            for i in range(self._redis.scard('proxies_http_usable')):
                pipe.spop('proxies_http_usable')
            for proxy in self._redis.sscan_iter('proxies_http'):
                pipe.smove('proxies_http', 'proxies_http_usable', proxy)
            for i in range(self._redis.scard('proxies_https_usable')):
                pipe.spop('proxies_https_usable')
            for proxy in self._redis.sscan_iter('proxies_https'):
                pipe.smove('proxies_https', 'proxies_https_usable', proxy)
            pipe.execute()

if __name__ == '__main__':
    logger = logging.getLogger('pool')
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    fmt = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
    datefmt = "%a %d %b %Y %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    c = Checker()
    c.start()
