
import logging  # 引入logging模块
import redis


log_format = '%(asctime)s - %(name)s[line:%(lineno)d] - %(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)

# redis可用队列
redis_http_usable = 'proxies_http_usable'
redis_https_usable = 'proxies_https_usable'
# redis测试队列
redis_http = 'proxies_http'
redis_https = 'proxies_https'
redis_http_https = {'http': redis_http, 'https': redis_https}

# 缓存http个
cache_http_number = 20
# 缓存https个
cache_https_number = 1

redis_pool = redis.ConnectionPool()


def get_redis():
    return redis.Redis(connection_pool=redis_pool)


def proxy_info():
    r = get_redis()
    http_usable = r.scard(redis_http_usable)
    https_usable = r.scard(redis_https_usable)
    http = r.scard(redis_http)
    https = r.scard(redis_https)
    print(http_usable, https_usable, http, https)


class RedisAction:
    def __init__(self):
        self._redis = get_redis()

    def redis_move(self):
        pipe = self._redis.pipeline()
        for i in range(self._redis.scard(redis_http_usable)):
            pipe.spop(redis_http_usable)
        for proxy in self._redis.sscan_iter(redis_http):
            pipe.smove(redis_http, redis_http_usable, proxy)
        for i in range(self._redis.scard(redis_https_usable)):
            pipe.spop(redis_https_usable)
        for proxy in self._redis.sscan_iter(redis_https):
            pipe.smove(redis_https, redis_https_usable, proxy)
        pipe.execute()

    def check_enough(self):
        http_enough = self._redis.scard(redis_http) < cache_http_number
        https_enough = self._redis.scard(redis_https) < cache_https_number
        return http_enough or https_enough
