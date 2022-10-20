import requests
import json
import isodate
import time
import re
import asyncio
import aiohttp
import random
import ssl
import certifi
from aiohttp.client import ClientSession

#asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

CHROME = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
          'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36')

SSL_CONTEXT           = ssl.create_default_context(cafile=certifi.where())
HEADERS               = requests.utils.default_headers()
HEADERS['User-Agent'] = random.choice(CHROME)

key = 'AIzaSyDaH3gW1qoX6lW1HYU7UTnoN_hG3kpZmTg'

adds,creators,deleted_videos,maybe_videos,videos,links,videos_id = [],[],[],[],[],[],[]
result_all,sec_spend,channels,list_of_channels,videos_by_channel = [],[],[],[],[]
stats,channel_data,channelIdbySubs = {},{},{}
requestCounter = 0


results = []
channel_result = []

most_frequent_video = []

def process_data(FILE_PATH):
    print("process_data")


    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    f.close()


    # odziela potecjalne filmy od reklam
    for x in range(len(data)):
        if "details" in data[x]:
            adds.append(data[x])
        else:
            maybe_videos.append(data[x])
    # odziela potencjalne filmy od prawdziwych filmow
    for x in range(len(maybe_videos)):
        if "Obejrzano: https://www.youtube.com/watch?v=" in maybe_videos[x]['title'] or "Obejrzano film, który został usunięty" in maybe_videos[x]['title'] or "Obejrzano relację:" in maybe_videos[x]['title'] or "Odwiedzono: YouTube Music" in maybe_videos[x]['title']:
            deleted_videos.append(maybe_videos[x]['title'])
        else:
            videos.append(maybe_videos[x])
    for x in range(len(videos)):
        # dodanie tworcow do listy
        creators.append(videos[x]['subtitles'][0]['name'])



def get_video_id():
    for x in range(len(videos)):
        link = videos[x]['titleUrl']
        result = re.findall(
            "^(?:https?:\/\/)?(?:(?:www\.)?youtube\.com\/(?:(?:v\/)|(?:embed\/|watch(?:\/|\?)){1,2}(?:.*v=)?|.*v=)?|(?:www\.)?youtu\.be\/)([A-Za-z0-9_\-]+)&?.*$", link)
        videos_id.append(result[0])


async def get_channel_data():
    print("get_channel_data")
    start_time=time.time() 
    unique_channels = list(set(list_of_channels))
    chunks = [unique_channels[x:x+50] for x in range(0, len(unique_channels), 50)]
    URL= "https://www.googleapis.com/youtube/v3/channels"
    params = {'key' : key,
          'part': 'statistics'}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for chunk in chunks:
            params['id'] = chunk
            async with session.get(url=URL, params=params, ssl=SSL_CONTEXT) as resp:
                if not (resp.status==200): continue
                channel_result.append(await resp.json())
    print("Channels requests time:",time.time() - start_time)

async def get_data():
    print("get_data")
    start_time=  time.time()
    chunks = [videos_id[x:x+50] for x in range(0, len(videos_id), 50)]
    URL= "https://www.googleapis.com/youtube/v3/videos"
    params = {'key' : key,
          'part': 'statistics,contentDetails,snippet'}
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for chunk in chunks:
            params['id'] = chunk
            async with session.get(url=URL, params=params, ssl=SSL_CONTEXT) as resp:
                if not (resp.status==200): continue
                results.append(await resp.json())
    print("Videos requests time:",time.time() - start_time)

def process_videos():
    print("process_videos")
    most_frequent_id = max(set(videos_id), key = videos_id.count)
    asyncio.run(get_data())
    for x in range(len(results)):   #parsowanie danych 
        part =results[x] # pobranie danych o filmie
        for x in range((len(part['items']))):
            id = part['items'][x]['id']
            try: #czasami views nie ma bo sa ukryte wiec najpierw probujemy je zdobyc jak nie to wstawiamy 0
                viewCount = part['items'][x]['statistics']['viewCount']
            except Exception as error:
                likeCount = 0
            try: #tak samo jak z viewsami
                likeCount = part['items'][x]['statistics']['likeCount']
            except Exception as error:
                likeCount = 0
            pass
            duration = int(isodate.parse_duration( #formatowanie czasu 
                part['items'][x]['contentDetails']['duration']).total_seconds())
            title = part['items'][x]['snippet']['title']
            channelTitle = part['items'][x]['snippet']['channelTitle']
            channelId = part['items'][x]['snippet']['channelId']
            result_all_temp = {
                'id': id,
                'title': title,
                'likeCount': likeCount,
                'viewCount': viewCount,
                'duration': duration,
                'channel_name': channelTitle,
                'channel_id': channelId

            }
            list_of_channels.append(channelId)
            sec_spend.append(duration)
            duration= 0
            result_all.append(result_all_temp)
            channels.append({channelTitle: channelId})
            if id == most_frequent_id:
                most_frequent_video_temp={
                'id': id,
                'title': title,
                'timesWatched': videos_id.count(id)
                }
                most_frequent_video.append(most_frequent_video_temp)
    return result_all
sec_spend.clear()
def process_channels():
    print("process_channels")
    asyncio.run(get_channel_data())
    for x in range(len(channel_result)):
        part =channel_result[x]
        for x in range(len(part['items'])):
            subs = int(part['items'][x]['statistics']['subscriberCount'])
            channelId = part['items'][x]['id']
            channelIdbySubs[channelId]=subs

    for video in result_all:
        channel_name = video['channel_name']
        if channel_name not in channel_data:
            channel_data[channel_name] = {'videos': {}, 'channel_stats': {
                'subs': channelIdbySubs[video['channel_id']],
                'id': video['channel_id']
            }}
        channel_data[channel_name]['videos'][video['id']] = {
            'viewCount':int(video['viewCount']),
            'likeCount': int(video['likeCount']),
            'duration': int(video['duration']),
            'title': video['title'],
        }
    return channel_data

def get_stats():
    print("get_stats")
    new_time = []
    print(len(videos_id))
    print(len(sec_spend))
    for x in range(len(videos_id)):
        try:
            new_time.append(sec_spend[x])
        except IndexError:
            new_time.append(0)
            pass
        
    stats = {
        "videosWatched":len(videos_id),
        "uniqueVideosWatched":len(list(set(videos_id))),
        "watchTime":int(sum(new_time)),
        "mostFrequentVideo": most_frequent_video[0]['title'],
        "timesWatched": most_frequent_video[0]['timesWatched'],
        "id": most_frequent_video[0]['id'],
        "link": "https://www.youtube.com/watch?v="+most_frequent_video[0]['id'],
        'mostFrequentCreator':max(set(creators), key = creators.count)
    }
    return stats


def init():
    print("init")
    get_video_id()


def remover():
    print("remover")
    to_remove = [adds,creators,deleted_videos,maybe_videos,videos,links,videos_id,result_all,sec_spend,channels,list_of_channels,videos_by_channel,stats,channel_data,channelIdbySubs]
    for item in to_remove:
        item.clear()
