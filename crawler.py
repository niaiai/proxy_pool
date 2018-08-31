# coding=utf-8

"""代理页抓取。"""

import re
import json
import time
import logging
import threading
from queue import Queue

import requests
from lxml import html

from . import tester
from .utils import get_redis, redis_http, redis_https


class Crawler:
    def __init__(self, parser, work_q):
        self._PROXY_NAME = parser.name
        self._urls_to_crawl = Queue()
        self._urls_crawled = Queue()
        self._pages_to_parse = Queue()
        self._redis = get_redis()
        self._sentinel = object()  # 抓取终止信号
        self._logger = logging.getLogger('pool.crawler.{}'.format(self._PROXY_NAME))
        self._parser = parser
        self._work_q = work_q
        self._tester = tester.Tester(5)

    def start(self):
        """爬虫执行器。

        该函数需在单独线程中调用，并只调用一次。执行的动作由work_q队列控制。队列中取到'start'时，会启动爬虫进行代理的抓取和验证，并将有效
        代理存入redis中；队列中取到'end'时，会退出爬虫。在退出爬虫时，代理验证其仍然会等到待验证代理都被验证后才会退出。
        """
        while True:
            work = self._work_q.get()
            if work == 'start':
                self._logger.info('crawler start')
                self._tester.start()
                self._urls_to_crawl.put(self._parser.index_url)

                session = requests.Session()
                session.headers = self._parser.headers

                # 启动抓取和解析线程
                crawler = threading.Thread(target=self._crawl, args=(session, 3))
                parser = threading.Thread(target=self._parse, args=(5000,))
                parser.start()
                crawler.start()
            elif work == 'end':
                self._urls_to_crawl.put(self._sentinel)
                self._pages_to_parse.put(self._sentinel)
            elif work == 'quit':
                self._logger.info("main crawler quit")
                self._logger.info("test is done %s", self._tester.is_done())
                break

    def _parse(self, response_times_allow):
        """代理页面解析。

        从待解析队列中取一个页面进行解析，并将响应时间大于response_times_allow值的代理送给代理验证器。
        解析完该页所有代理后，会再解析出下一页的url，并放入待抓取队列中。

        :param response_times_allow: 允许的代理响应时间，响应时间低于该值的代理会被过滤掉。
        """
        while True:
            page_to_parse = self._pages_to_parse.get()
            self._logger.debug('get page to parse')

            if page_to_parse is self._sentinel:
                # 停止解析，并清空解析队列
                with self._pages_to_parse.mutex:
                    self._pages_to_parse.queue.clear()

                self._tester.test('end')
                self._logger.info('parse spider quit')
                break

            tree = html.fromstring(page_to_parse)

            proxies_data = self._parser.get_proxies_data(tree)
            for proxy_data in proxies_data:
                proxies = self._parser.get_proxies(proxy_data)
                for proxy in proxies:
                    if proxy['response_times'] <= response_times_allow and proxy['protocol'].lower() in {'http', 'https'}:
                        self._logger.debug('put proxy to test: %s', proxy)
                        self._tester.test(json.dumps(proxy))
                    else:
                        self._logger.debug('pass proxy: %s', proxy)
            else:
                # 本页代理解析完毕，提取下一页url放入待抓取队列
                current_page_number = int(re.match(r'.*?(\d+).*?', self._urls_crawled.get()).group(1))
                next_url_to_crawl = re.sub(r'(\d+)', str(current_page_number + 1), self._parser.index_url)
                self._logger.debug('put url to crawl: %s', next_url_to_crawl)
                self._urls_to_crawl.put(next_url_to_crawl)

    def _crawl(self, session, retry_count_limit):
        """代理页面抓取。

        从待抓取队列中取一个url进行抓取，并将抓取结果放入待解析队列。当某页抓取失败时，会进行重试，最大重试次数为retry_count_limit，超过
        该值时会跳过此url。
        每个url抓取间隔为0.5s。

        :param session: requests session。
        :param retry_count_limit: 抓取重试次数，某个页面抓取失败时会进行重试，当重试次数超过该值时会跳过此url。
        """

        # 使用过进行抓取并且无效的代理.某些代理虽然通过了验证，但是使用时仍然可能有问题；另一种情况就是，西刺提供的代理都是无法抓取西刺的
        proxies_used_useless = set()
        while True:
            url_to_crawl = self._urls_to_crawl.get()
            self._logger.debug('get url to crawl: %s', url_to_crawl)

            if url_to_crawl is self._sentinel:
                # 停止抓取，并清空抓取队列
                with self._urls_to_crawl.mutex:
                    self._urls_to_crawl.queue.clear()

                with self._urls_crawled.mutex:
                    self._urls_crawled.queue.clear()

                self._logger.info('crawl spider quit')
                break

            retry_count = 0
            while True:
                proxy_str = self._redis.spop(redis_http)
                if proxy_str:
                    self._redis.sadd(redis_http, proxy_str)
                    proxy = json.loads(proxy_str)
                    p = '{}:{}'.format(proxy['ip'], proxy['port'])

                try:
                    if proxy_str and (p not in proxies_used_useless) and proxy['src'] != self._parser.name:
                        self._logger.debug('use proxy to crawl proxies: %s', p)
                        r = session.get(url_to_crawl, proxies={'http': p}, timeout=5)
                        r.raise_for_status()
                    else:
                        self._logger.debug('use local ip to crawl proxies')
                        r = session.get(url_to_crawl, timeout=5)
                        r.raise_for_status()
                except requests.exceptions.RequestException:
                    if retry_count < retry_count_limit:
                        retry_count += 1

                        if proxy_str and proxy['src'] != self._parser.name:
                            self._logger.warning('proxy %s is useless', p)
                            proxies_used_useless.add(p)
                    else:
                        time.sleep(5)
                else:
                    self._logger.debug('put page to parse')
                    self._pages_to_parse.put(r.text)
                    self._urls_crawled.put(url_to_crawl)
                    time.sleep(1)
                    break


if __name__ == '__main__':
    logger = logging.getLogger('pool')
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    fmt = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"
    datefmt = "%a %d %b %Y %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    import parser
    import json

    q = Queue()
    c = Crawler(parser.parsers[3], q)
    r = get_redis()

    worker = threading.Thread(target=c.start)
    worker.start()

    q.put('start')

    l_http = r.scard(redis_http)
    l_https = r.scard(redis_https)
    while l_http < 5 or l_https < 5:
        time.sleep(0.01)
        l_http = r.scard(redis_http)
        l_https = r.scard(redis_https)

    q.put('end')
    print(l_http)
    for proxy in r.sscan_iter(redis_http):
        p = json.loads(proxy)
        print('{}:{}'.format(p['ip'], p['port']), end=', ')
    print()
    print(l_https)
    for proxy in r.sscan_iter(redis_https):
        p = json.loads(proxy)
        print('{}:{}'.format(p['ip'], p['port']), end=', ')
