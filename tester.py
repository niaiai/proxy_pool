# coding=utf-8

"""代理验证器，通过连接http://httpbin.org/get进行验证。"""

import json
import logging
import threading
import concurrent.futures
from queue import Queue

import requests
from .utils import get_redis, redis_http_https


class Tester:
    def __init__(self, test_times, queue=None):
        """初始化验证器。

        :param test_times: 验证次数，指使用某个代理进行测试连接的次数。
        """
        self._proxies_queue_to_test = Queue() if queue is None else queue
        self._test_times = test_times
        self._valid_proxies = get_redis()
        self._logger = logging.getLogger('pool.tester')
        self._worker = None

    def start(self):
        """通过此接口启动验证器，结束一轮验证后，再次使用要重新启动。"""
        self._worker = threading.Thread(target=self._work)
        self._worker.setDaemon(True)
        self._worker.start()

    def test(self, proxy):
        """代理验证接口。

        待验证代理会被放入'_proxies_queue_to_test'队列中，交由工作线程进行验证。

        :param proxy: 代理字典的json字符串表示，传入'end'结束本轮验证。
        """
        self._proxies_queue_to_test.put(proxy)

    def is_done(self):
        """验证器是否完成了所有代理的验证。"""
        if self._worker:
            return not self._worker.is_alive()

    def _test_single_proxy(self, requests_session, proxy):
        """验证代理的工作接口。

        验证器会根据代理支持的协议，对'http://httpbin.org/get'或'https://httpbin.org/get'进行'test_times'此请求，每次请求超时
        时间为5s，若5次请求均成功则将代理存入'proxies_http'或'proxies_https'缓存中。请求成功的定义是状态码200，无重定向，并且返回的json
        内容中'origin'字段值和代理地址一致。

        :param requests_session: requests session对象。
        :param proxy: 待验证代理字典的json字符串表示。
        """
        proxy_protocol = proxy['protocol'].lower()
        proxy_str = '{}://{}:{}'.format(proxy_protocol, proxy['ip'], proxy['port'])

        try:
            for i in range(self._test_times):
                with requests_session.get('{}://httpbin.org/get'.format(proxy_protocol),
                                          proxies={proxy_protocol: proxy_str}, timeout=5) as resp:
                    if resp.status_code != 200 or resp.history:
                        break
                    if resp.json()['origin'] != proxy['ip']:
                        break
            else:
                self._logger.info("test %s ok", proxy_str)
                self._valid_proxies.sadd(redis_http_https[proxy_protocol], json.dumps(proxy))
        except requests.exceptions.RequestException:
            pass

        self._logger.debug('test %s done', proxy['ip'])

    def _work(self):
        """验证器工作线程，创建一个包含100个线程的线程池，从'_proxies_queue_to_test'中获取代理进行验证。
        当从队列中取到无效json字符串的时候会清空'_proxies_queue_to_test'队列并等待当前待验证代理全部验证结束后退出。
        """
        tasks = []

        with requests.Session() as requests_session:
            with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
                while True:
                    try:
                        if self._proxies_queue_to_test.empty():
                            continue
                        proxy_to_test = json.loads(self._proxies_queue_to_test.get())
                    except json.decoder.JSONDecodeError:
                        concurrent.futures.wait(tasks)
                        with self._proxies_queue_to_test.mutex:
                            self._proxies_queue_to_test.queue.clear()
                        self._logger.info('test quit')
                        break
                    else:
                        self._logger.debug('get proxy to test: %s', proxy_to_test['ip'])
                        tasks.append(executor.submit(self._test_single_proxy, requests_session, proxy_to_test))
