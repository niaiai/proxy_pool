# proxy_pool
## 功能
* 从网络抓取免费代理，并检查可用性
* 定时检查、补充代理，保证代理池数量
* 支持扩展代理抓取模块

## 安装依赖
```
pip3 install -r requirements.txt
```

## 运行
```
from proxy_pool.ProxyPool import ProxyPool
pool = ProxyPool()
pool.http
# 45.55.132.29:3128
pool.http
# 45.76.1.94:8080
pool.https
# 47.52.222.65:3128
pool.https
# 42.115.91.82:52225
```

## 说明
代理池包括如下几个模块：
* ProxyPool.py：对外接口，用户通过该模块取得代理
* parser.py：解析器，对各代理网站解析方法的封装，可扩展
* crawler.py：抓取器，根据parser.py中的定义对代理网站进行抓取和解析，并将初步抓取到的代理送到验证器
* tester.py：验证器，对代理进行验证，检查可用性，将可用代理缓存下来
* checker.py：检查器，定时检查缓存代理是否失效，若失效代理超过一定数量则启动抓取器补充代理

#### parser
该模块将各个代理网站的解析方法封装成对应的parser类，并将类注册在parsers列表中，crawler会读取该列表执行抓取任务。

parser类要求包含index_url、name、headers属性和get_proxies_data、get_proxies类方法。

index_url属性存储代理网站的首页地址，如'http://www.xicidaili.com/nn/1’；name属性存储代理网站的名称，如’xici’；
headers属性存储代理网站的请求头部；
get_proxies_data方法获取代理列表，列表类型为lxml节点；
get_proxies方法解析上述方法返回列表中的lxml节点，获取代理。返回类型为元组，存储从各节点中解析到的代理，代理类型为字典，包含ip、port、address、protocol、src、response_times字段。

之所以get_proxies方法返回类型为元组是由于有可能一个代理即支持http协议又支持https协议，此时会将其作为两个独立的代理返回。在代理池内部，http代理和https代理是分开存储的。

#### tester
该模块进行代理可用性的验证，内部有单独的工作线程，在工作线程中使用一个包含100个线程的线程池进行代理的验证。

验证方法为根据代理支持的协议，对 [http://httpbin.org/get](http://httpbin.org/get) 和[https://httpbin.org/get](https://httpbin.org/get)发送get请求，每次请求超时时间为5s，若5次请求均成功则将代理存入'proxies_http'或'proxies_https'缓存中。请求成功的定义是状态码200，无重定向，并且返回的json内容中'origin'字段值和代理地址一致。

#### crawler
该模块进行代理的抓取，内部维护一个抓取线程和一个解析线程。抓取线程会从待抓取url队列中获取url进行网页的抓取，并将取得的文本放入待解析队列；解析线程从待解析队列中获取文本，并使用对应的parser进行解析，之后会讲取得的代理送给验证器，同时将下一页url放入待抓取队列。

抓取代理网页时也会从之前抓取到的代理池中循环取代理使用，避免代理网站的封锁。

#### checker
该模块进行代理的定时复检，每10分钟将代理池中的代理取出来送给验证器检查可用性，若可用代理少于10个则启动抓取器进行代理抓取。

#### ProxyPool
用户入口，通过http或https接口获取代理，要注意的是在创建ProxyPool实例的时候会阻塞一会进行代理的抓取。
