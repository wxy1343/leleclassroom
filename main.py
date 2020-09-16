import os
import sys
from threading import Lock
from multiprocessing.dummy import Pool
import requests
import re
from lxml import etree

pool = Pool(100)
lock = Lock()


def get_stages_info(stages_url):
    r = requests.get(stages_url, headers=headers)
    html = etree.HTML(r.text)
    length = len(html.xpath("//a[contains(@class, 'kn_one') and contains(@class, ' ')]/@href"))
    url = 'http://www.leleketang.com/cr/' + \
          html.xpath("//a[contains(@class, 'kn_one') and contains(@class, ' ')]/@href")[0]
    title = html.xpath('//div[@class="knowledge_name"]/text()')[0]
    titles = html.xpath("//div[contains(@class, 'kn_o_name') and contains(@class, 'ellipsis')]/@title")
    r = requests.get(url, headers=headers)
    url, first_video_id = re.search('m4v: "//(v.leleketang.com/dat/.*/.*/k/video/(.*?).mp4)",', r.text).groups()
    url = 'http://' + url.replace(first_video_id, '{video_id}')
    first_video_id = int(first_video_id)
    return url, first_video_id, length, title, titles


def get_video_url(*args):
    global video_list
    video_list = []
    url, first_video_id, length, title, titles = args
    i = 0
    j = length
    while length:
        mp4 = url.format(video_id=first_video_id + i)
        ogv = mp4[:-3] + 'ogv'
        r = requests.head(mp4, headers=headers)
        if r.status_code == 200:
            n = j - length
            length -= 1
            size = float(r.headers['media-length']) / 1024 / 1024
            print(f'{n + 1}.{titles[n]}：' + mp4 + ' {:.1f}MB MD5:{}'.format(size, r.headers['Content-MD5']))
            video_list.append(
                {'n': n + 1, 'title': titles[n], 'size': int(r.headers['media-length']), 'url': mp4, 'path': title,
                 'sum': j})
        elif r.status_code != 404:
            continue
        i += 1


def get_stages_video(stages_id):
    args = get_stages_info(stages_url.format(stages_id=stages_id))
    get_video_url(*args)


def video_download(video_dict):
    global count
    with lock:
        if 'count' not in dir():
            count = 0
            sys.stdout.write(
                f"\r\033[0;37;42m下载中 {count}/{video_dict['sum']}\033[0m")
        sys.stdout.flush()
        if not os.path.exists(video_dict['path']):
            os.mkdir(video_dict['path'])
    path = os.path.join(video_dict['path'], str(video_dict['n']) + '.' + video_dict['title'] + '.mp4')
    h = headers
    while True:
        try:
            if os.path.exists(path):
                size = os.path.getsize(path)
            else:
                size = 0
            if size == video_dict['size']:
                break
            h['Range'] = 'bytes=%d-' % size
            r = requests.get(video_dict['url'], headers=h, stream=True, timeout=5)
            if r.status_code == 404:
                raise Exception
            with open(path, 'ab') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        size += len(chunk)
                        f.write(chunk)
                        f.flush()
                break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            pass
        except KeyboardInterrupt:
            return
    with lock:
        count += 1
        sys.stdout.write(
            f"\r\033[0;37;42m下载中 {count}/{video_dict['sum']}\033[0m")


if __name__ == '__main__':
    os.system('title 乐乐课堂视频爬取 @wxy1343')
    stages_url = 'http://www.leleketang.com/cr/stages.php?id={stages_id}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
    n = int(input('请输入标签id：'))
    get_stages_video(n)
    print('爬取完毕')
    pool.map(video_download, video_list)
    print('\n下载完成')
    os.system('pause')
