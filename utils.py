from collections import Counter
from models import Songs
from video_details import video_details
import google.appengine.api.memcache as mc

__author__ = 'pravesh'

import re
import time
from logging import info, debug, warn, error
import json
import threading

_thread_lock = threading.Lock()
KEY = "cached_song"


def length_if_already_present(youtube_id):
    song = Songs.query(Songs.youtube_id == youtube_id).get()
    if song:
        return song.length
    return 0


def load_data(data):
    youtube_link = data.get('youtube')
    assert youtube_link, "Youtube link is empty!"

    name = data['name']
    assert name, "Username is empty"

    message = data.get('message', '')

    country = data.get('country', '')

    youtube_id = re.findall(r'\?.*&?v=([^&]+).*', youtube_link)
    assert youtube_id, "Couldn't find youtube id"

    valid_youtube = re.match(r'https?://(www\.)?youtube\.com/watch/?\?.*', youtube_link)
    assert valid_youtube, "Youtube link is not valid"

    tags = data.get("tags", [])
    if not isinstance(tags, list):
        try:
            tags = list(tags)
        except Exception, e:
            raise Exception("Tags could not be converted to list.")

    youtube_id = youtube_id[0]
    length = length_if_already_present(youtube_id)
    if not length:
        try:
            song_info = get_song_info(youtube_id)
        except Exception, e:
            raise Exception("Invalid video id..")

        if not is_valid_song(song_info):
            raise Exception("Invalid video requirements..")
        length = song_info['length']
    s = Songs(name=name, message=message, country=country,
              youtube_id=youtube_id, timestamp=time.time(), length=length, queue=True, tags=tags)
    return s


def get_queue_length():
    return mc.get("queue_length") or 0


def update_queue_length(length):
    queue_length = get_queue_length()
    mc.set("queue_length", queue_length + length)


def get_cached_song(memkey):
    return mc.get(key=memkey)


def get_relevant_song(tags):
    # get the latest running song
    # results = db.songs.find({'queue': True}).sort([("timestamp", 1)]).limit(1)
    tags = filter(None, tags)
    if tags:
        results = Songs.query(Songs.queue == True, Songs.tags.IN(tags)).order(Songs.timestamp)
    else:
        results = Songs.query(Songs.queue == True).order(Songs.timestamp)

    results = list(results)
    if results:
        # find other similar results here and mark others as tagged..
        return results[0]
    return {}


def get_song_info(youtube_id):
    return video_details(youtube_id)


def is_valid_song(song_info):
    if song_info['length'] < 10*60 and song_info['views'] > 10000 and song_info['rating'] > 2.5:
        return True
    return False


def get_similar_songs(song):
    timestamp = song.timestamp

    # 5 hours
    end_timestamp = timestamp + 5 * 60 * 60

    # results = db.songs.find({'queue': True, '_id': {"$ne": song['_id']}, 'youtube_id': song['youtube_id'],
    # 'timestamp': {"$lte": end_timestamp}})\
    #             .sort([("timestamp", 1)])

    results = Songs.query(Songs.queue==True, Songs.youtube_id == song.youtube_id,
                          Songs.timestamp <= end_timestamp)
    songs = list(filter(lambda s: s.key != song.key, results))

    info("%d new songs found similar to %s" % (len(songs), song.youtube_id))
    return [song] + songs


def serialize_song(songs):
    assert all([s.youtube_id == songs[0].youtube_id for s in songs])

    country_counter = Counter([s.country for s in songs])

    serialized_object = {
        "username_message": [{'name': s.name, 'message': s.message} for s in songs],
        "country": country_counter.most_common(1)[0][0],   # most common string in the country field
        "youtube_id": songs[0].youtube_id
    }

    return serialized_object


def update_cached_song(serialized, duration, memkey):
    info("Updating Cache with following id %s" % serialized['youtube_id'])

    # decrease the time to play
    update_queue_length(-duration)
    mc.set(memkey, serialized, duration)


def mark_songs(songs):
    # query = {"_id": {"$in": [s['_id'] for s in songs]}}
    for s in songs:
        s.queue = False
        s.put()


def get_song(tags):
    memkey = KEY + "_" + "_".join(sorted(tags))

    cache = get_cached_song(memkey)
    if cache:
        return cache

    debug("Cache miss, now retrieving new song.")

    song = get_relevant_song(tags)
    if not song:
        # song is empty
        info("Now new songs found, will have to retrieve from the fallback database.")
        return {}


    songs = get_similar_songs(song)
    serialized = serialize_song(songs)
    print song.length
    update_cached_song(serialized, song.length, memkey)

    # mark them as processed
    mark_songs(songs)

    return serialized


def post_song(data):
    # post the song in queue..
    debug("New song request: %s" % json.dumps(data))
    try:
        # validate and load
        song = load_data(data)

        # if a song is already in queue, don't bother increasing the estimated play time.
        if not Songs.exists(Songs.queue==True, Songs.youtube_id==song.youtube_id):
            update_queue_length(song.length)
        song.put()

        return True
    except Exception, e:
        error("Error occured: %s" % e.message)
        return False


if __name__ == "__main__":
    # tests
    dataitem = load_data({
        "username": '123',
        'youtube': 'http://youtube.com/watch?v=ABCDE'
    })
    assert dataitem['youtube_id'] == "ABCDE"

    # Incorrect youtube link
    dataitem = load_data({
        "username": '123',
        'youtube': 'https://youtube.com/watch?v=AB23&DE',
        'message': "I love all kinds of people!"
    })
    assert dataitem['youtube_id'] == "AB23"

    try:
        # Incorrect youtube link
        dataitem = load_data({
            "username": '123',
            'youtube': 'https://youtube.com/watch?list=AB23&DE',
            'message': "Random message"
        })
        assert False, "Must hit exception"
    except AssertionError, e:
        assert e.message == "Couldn't find youtube id"

    # Check www
    dataitem = load_data({
        "username": '123',
        'youtube': 'https://www.youtube.com/watch?v=AB23CCij012',
        'message': "Random message"
    })
    assert dataitem['youtube_id'] == 'AB23CCij012'

    assert dataitem['timestamp']

    # video = pafy.new("GqmRDV0a_70")
    # print video
    #
    # import youtube_dl
    #
    #
    # ydl_opts = {
    #     'quiet': True,
    #     'skip_download': True,
    # }
    # with youtube_dl.YoutubeDL(ydl_opts) as ydl:
    #     info = ydl.extract_info('https://www.youtube.com/watch?v=GqmRDV0a_70')
    #
    # print('Title of the extracted video/playlist: %s' % info['title'])