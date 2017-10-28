#coding:utf8
import requests
import threading
import Queue

import time,random
import re

# 设置线程数
concurrent = 3
parse_count = 5

class VideoThread(threading.Thread):

    def __init__(self,task_q,data_q,num):
        #调用父类
        super(VideoThread, self).__init__()

        self.task_q = task_q
        self.data_q = data_q
        self.num = num+1
        self.sess = requests.session()  #创建session
        self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
        }
        self.sess.headers = self.headers #添加请求头

    def run(self):
        print '启动天字%d号' % self.num
        while self.task_q.qsize() > 0: #爬取任务队列
            url = self.task_q.get()
            print '天字%d号采集%s' % (self.num,url)

            time.sleep(random.randint(1,3)) #请求等待
            response = self.sess.get(url)
            html = response.content
            self.data_q.put(html)  #抓取的页面放入采集队列
        print '天字%d号任务完成' % self.num

#解析线程
class UrlThread(threading.Thread):
    def __init__(self,data_q,crawl_list,num,lock):
        super(UrlThread, self).__init__()
        self.data_q = data_q
        self.crawl_list = crawl_list
        self.num = num+1
        self.lock = lock
        self.is_parse = True  #是否解析

    def run(self):
        print '启动地字%d号' % self.num
        while True:
            for crawl in self.crawl_list:
                if crawl.is_alive():  #判断是否在采集
                    break
                else:
                    if self.data_q.qsize() == 0: #数据采集完成
                        self.is_parse = False

            if self.is_parse:
                try:
                    html = self.data_q.get(timeout=1)
                    self.parse(html)
                except Exception,e:
                    pass
            else:
                break
        print '结束地字%d号' % self.num

    #过去页面视频链接
    def parse(self,html):
        with self.lock:
            pattern = re.compile(r'data-mp4="(.*?)"')
            video_list = pattern.findall(html)
            print video_list
            self.video_down(video_list)

    #下载视频
    def video_down(self,video_list):

        a = 1
        for video_url in video_list:
            response = requests.get(video_url)
            if response.status_code == 200:
                fname = video_url.split('/')[-1]
                print response.url
                with open('./budejie/'+fname,'wb') as f:
                    f.write(response.content)
                    print '下载完成%d个' % a
                    a += 1
            else:
                pass

def main(page):

    #任务队列
    task_q = Queue.Queue()
    #数据队列
    data_q = Queue.Queue()
    #锁
    lock = threading.Lock()

    #生成10个队列追加到任务队列
    for x in range(1,page+1):
        base_url = 'http://www.budejie.com/%d'
        url = base_url % x
        task_q.put(url)

    #启动采集线程
    crawl_list  = []
    for num in range(concurrent):
        t = VideoThread(task_q,data_q,num)
        t.start()
        crawl_list.append(t)

    #启动解析线程
    parse_list = []
    for num in range(parse_count):
        t = UrlThread(data_q,crawl_list,num,lock)
        t.start()
        parse_list.append(t)

    #等待所有采集线程运行完毕
    for crawl in crawl_list:
        crawl.join()
    #等待所有 解析线程运行完毕
    for parse in parse_list:
        parse.join()




if __name__ == '__main__':
    start = time.time()
    page = int(raw_input('请输入要下载的页数'))
    main(page)
    print 'down',time.time() - start

