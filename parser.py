# coding=utf-8

"""各代理网站解析器。"""

from datetime import datetime


class ParserKuai:
    index_url = 'http://www.kuaidaili.com/free/inha/1/'
    name = 'kuai'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'www.kuaidaili.com',
        'User-Agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) '
                      'Chrome / 61.0.3163.100Safari / 537.36'
    }

    @classmethod
    def get_proxies_data(cls, tree):
        return tree.xpath('//div[@id="list"]//tbody/tr')

    @classmethod
    def get_proxies(cls, proxy_data):
        ip = cls.get_ip(proxy_data)
        port = cls.get_port(proxy_data)
        address = cls.get_address(proxy_data)
        protocol = cls.get_protocol(proxy_data)
        response_times = cls.get_response_times(proxy_data)
        src = cls.name

        return (dict(ip=ip, port=port, address=address, protocol=protocol, src=src, response_times=response_times),)

    @classmethod
    def get_ip(cls, proxy_data):
        return proxy_data.xpath('./td[1]/text()')[0]

    @classmethod
    def get_port(cls, proxy_data):
        return proxy_data.xpath('./td[2]/text()')[0]

    @classmethod
    def get_address(cls, proxy_data):
        return proxy_data.xpath('./td[5]/text()')[0]

    @classmethod
    def get_protocol(cls, proxy_data):
        return proxy_data.xpath('./td[4]//text()')[0]

    @classmethod
    def get_response_times(cls, proxy_data):
        try:
            response_times = float(proxy_data.xpath('./td[6]/text()')[0].replace('秒', '')) * 1000
        except ValueError:
            # 响应速度只有「秒」，没写数字
            response_times = 1

        return response_times

    @classmethod
    def get_verify_datetime(cls, proxy_data):
        return datetime.strptime(proxy_data.xpath('./td[7]/text()')[0], '%Y-%m-%d %H:%M:%S')


class ParserXici:
    index_url = 'http://www.xicidaili.com/nn/1'
    name = 'xici'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'www.xicidaili.com',
        'User-Agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) '
                      'Chrome / 61.0.3163.100Safari / 537.36'
    }

    @classmethod
    def get_proxies_data(cls, tree):
        return tree.xpath('//table[@id="ip_list"]/tr[@class]')

    @classmethod
    def get_proxies(cls, proxy_data):
        ip = cls.get_ip(proxy_data)
        port = cls.get_port(proxy_data)
        address = cls.get_address(proxy_data)
        protocol = cls.get_protocol(proxy_data)
        response_times = cls.get_response_times(proxy_data)
        src = cls.name

        return (dict(ip=ip, port=port, address=address, protocol=protocol, src=src, response_times=response_times),)

    @classmethod
    def get_ip(cls, proxy_data):
        return proxy_data.xpath('./td[2]//text()')[0]

    @classmethod
    def get_port(cls, proxy_data):
        return proxy_data.xpath('./td[3]//text()')[0]

    @classmethod
    def get_address(cls, proxy_data):
        return proxy_data.xpath('./td[4]//text()')[1] if proxy_data.xpath('./td[4][./a]') else ''

    @classmethod
    def get_protocol(cls, proxy_data):
        return proxy_data.xpath('./td[6]//text()')[0]

    @classmethod
    def get_response_times(cls, proxy_data):
        return float(proxy_data.xpath('./td[7]/div[@title]/@title')[0].replace('秒', '')) * 1000

    @classmethod
    def get_verify_datetime(cls, proxy_data):
        return datetime.strptime(proxy_data.xpath('./td[10]//text()')[0], '%y-%m-%d %H:%M')


class ParserGoubanjia:
    index_url = 'http://www.goubanjia.com/free/gngn/index1.shtml'
    name = 'goubanjia'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'www.goubanjia.com',
        'User-Agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) '
                      'Chrome / 61.0.3163.100Safari / 537.36',
        'Connection': 'keep-alive'
    }

    @classmethod
    def get_proxies_data(cls, tree):
        return tree.xpath('//tbody/tr')

    @classmethod
    def get_proxies(cls, proxy_data):
        ip = cls.get_ip(proxy_data)
        port = cls.get_port(proxy_data)
        address = cls.get_address(proxy_data)
        protocol = cls.get_protocol(proxy_data)
        response_times = cls.get_response_times(proxy_data)
        src = cls.name

        return (dict(ip=ip, port=port, address=address, protocol=protocol, src=src, response_times=response_times),)

    @classmethod
    def get_ip(cls, proxy_data):
        return ''.join(proxy_data.xpath(
            './td[1]//node()[(@style and (@style!="display: none;" and @style!="display:none;")) or not(@style)]/text() | ./td[1]/text()')).split(
            ':')[0]

    @classmethod
    def get_port(cls, proxy_data):
        def get_port(word):
            num_list = []
            for item in word:
                num = 'ABCDEFGHIZ'.find(item)
                num_list.append(str(num))
            port = int("".join(num_list)) >> 0x3
            return str(port)

        return get_port(proxy_data.xpath('.//node()[contains(@class, "port")]/@class')[0].split()[1])

    @classmethod
    def get_address(cls, proxy_data):
        return ''.join(proxy_data.xpath('./td[4]/a/text()'))

    @classmethod
    def get_protocol(cls, proxy_data):
        return proxy_data.xpath('./td[3]//text()')[0]

    @classmethod
    def get_response_times(cls, proxy_data):
        return float(proxy_data.xpath('./td[6]//text()')[0].replace(' 秒', '')) * 1000


class ParserCoderbusy:
    index_url = 'https://proxy.coderbusy.com/zh-cn/classical/anonymous-type/highanonymous/p1.aspx'
    name = 'coderbusy'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'Host': 'proxy.coderbusy.com',
        'User-Agent': 'Mozilla / 5.0(WindowsNT10.0;Win64;x64) AppleWebKit / 537.36(KHTML, likeGecko) '
                      'Chrome / 61.0.3163.100Safari / 537.36'
    }

    @classmethod
    def get_proxies_data(cls, tree):
        return tree.xpath('//tbody/tr')

    @classmethod
    def get_proxies(cls, proxy_data):
        ip = cls.get_ip(proxy_data)
        port = cls.get_port(proxy_data)
        address = cls.get_address(proxy_data)
        protocol = cls.get_protocol(proxy_data)
        response_times = cls.get_response_times(proxy_data)
        src = cls.name

        if cls.is_suppose_https(proxy_data):
            return (dict(ip=ip, port=port, address=address, protocol=protocol, src=src, response_times=response_times),
                    dict(ip=ip, port=port, address=address, protocol='https', src=src, response_times=response_times))
        else:
            return (dict(ip=ip, port=port, address=address, protocol=protocol, src=src, response_times=response_times),)

    @classmethod
    def get_ip(cls, proxy_data):
        return proxy_data.xpath('./td[1]//text()')[1].strip()

    @classmethod
    def get_port(cls, proxy_data):
        return proxy_data.xpath('./td[2]/text()')[0]

    @classmethod
    def get_address(cls, proxy_data):
        return proxy_data.xpath('./td[3]//text()')[1]

    @classmethod
    def get_protocol(cls, proxy_data):
        return proxy_data.xpath('./td[5]//text()')[0]

    @classmethod
    def get_response_times(cls, proxy_data):
        return float(proxy_data.xpath('./td[10]//text()')[0].replace('秒', '')) * 1000

    @classmethod
    def is_suppose_https(cls, proxy_data):
        if proxy_data.xpath('./td[8]/span'):
            return True
        else:
            return False


parsers = [
    ParserKuai,
    ParserXici,
    # ParserGoubanjia,
    ParserCoderbusy
]
