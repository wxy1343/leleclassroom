from threading import Thread
import requests
import functools
import re
from lxml import etree
import asyncio


async def get_stages_info(stages_url):
    r = requests.get(stages_url, headers=headers)
    html = etree.HTML(r.text)
    length = len(html.xpath("//a[contains(@class, 'kn_one') and contains(@class, ' ')]/@href"))
    url = 'http://www.leleketang.com/cr/' + \
          html.xpath("//a[contains(@class, 'kn_one') and contains(@class, ' ')]/@href")[0]
    titles = html.xpath("//div[contains(@class, 'kn_o_name') and contains(@class, 'ellipsis')]/@title")
    future = asyncio.get_event_loop().run_in_executor(None,
                                                      functools.partial(requests.get, url, headers=headers))
    r = await future
    url, first_video_id = re.search('m4v: "//(v.leleketang.com/dat/.*/.*/k/video/(.*?).mp4)",', r.text).groups()
    url = 'http://' + url.replace(first_video_id, '{video_id}')
    first_video_id = int(first_video_id)
    return url, first_video_id, length, titles


def get_video_url(*args):
    url, first_video_id, length, titles = args
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
        i += 1


async def get_stages_video(stages_id):
    args = await get_stages_info(stages_url.format(stages_id=stages_id))
    Thread(target=get_video_url, args=args).start()


if __name__ == '__main__':
    stages_url = 'http://www.leleketang.com/cr/stages.php?id={stages_id}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
    n = int(input('请输入标签id：'))
    asyncio.run(get_stages_video(n))
