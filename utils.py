from collections import Counter
from models import Songs
from video_details import video_details
import google.appengine.api.memcache as mc

__author__ = 'pravesh'

import re
# from pymongo import MongoClient
import time
# import pafy
#
# client = MongoClient()
# db = client.songdb

# cached_song = {}


def _parse_data(data):
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
    s = Songs(name=name, message=message, country=country, youtube_id=youtube_id[0], timestamp=time.time(), queue=True)
    return s


def get_cached_song():
    return mc.get(key="cached_song")
    # global cached_song
    # if cached_song:
    #     if time.time() > cached_song['end_timestamp']:
    #         cached_song = {}
    #     return cached_song
    # return {}


def get_relevant_song():
    # get the latest running song
    # results = db.songs.find({'queue': True}).sort([("timestamp", 1)]).limit(1)
    results = Songs.query(Songs.queue==True).order(Songs.timestamp)
    results = list(results)
    if results:
        # find other similar results here and mark others as tagged..
        return results[0]
    return {}


def get_song_info(song):
    return video_details(song.youtube_id)


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
    return [song] + list(filter(lambda s: s.key != song.key,results))


def serialize_song(songs):
    assert all([s.youtube_id == songs[0].youtube_id for s in songs])

    country_counter = Counter([s.country for s in songs])

    serialized_object = {
        "username_message": [{'name': s.name, 'message': s.message} for s in songs],
        "country": country_counter.most_common(1)[0][0],   # most common string in the country field
        "youtube_id": songs[0].youtube_id
    }

    return serialized_object


def update_cached_song(serialized, duration):
    mc.set('cached_song', serialized, duration)
    # global cached_song
    # cached_song = serialized
    # cached_song['end_timestamp'] = time.time() + duration


def mark_songs(songs):
    # query = {"_id": {"$in": [s['_id'] for s in songs]}}
    for s in songs:
        s.queue = False
        s.put()


def get_song():
    cache = get_cached_song()
    if cache:
        return cache

    song = {}
    song_info = {}

    # retry 5 times
    for i in range(5):
        song = get_relevant_song()
        if not song:
            # song is empty
            return {}

        # try and get the song info.. fail if invalid youtube id
        try:
            song_info = get_song_info(song)
        except:
            # if not youtube id remove from db
            song.key.delete()
            continue

        # Check for song's validity: time, rating, viewcount.. etc
        if is_valid_song(song_info):
            break
        else:
            song.key.delete()

    if not song:
        return {}

    songs = get_similar_songs(song)
    serialized = serialize_song(songs)

    update_cached_song(serialized, song_info['length'])

    # mark them as processed
    mark_songs(songs)

    return serialized


def post_song(data):
    # post the song in queue..

    # validate and load
    song = _parse_data(data)
    song.put()
    return True

if __name__ == "__main__":
    # tests
    dataitem = _parse_data({
        "username": '123',
        'youtube': 'http://youtube.com/watch?v=ABCDE'
    })
    assert dataitem['youtube_id'] == "ABCDE"

    # Incorrect youtube link
    dataitem = _parse_data({
        "username": '123',
        'youtube': 'https://youtube.com/watch?v=AB23&DE',
        'message': "I love all kinds of people!"
    })
    assert dataitem['youtube_id'] == "AB23"

    try:
        # Incorrect youtube link
        dataitem = _parse_data({
            "username": '123',
            'youtube': 'https://youtube.com/watch?list=AB23&DE',
            'message': "Random message"
        })
        assert False, "Must hit exception"
    except AssertionError, e:
        assert e.message == "Couldn't find youtube id"

    # Check www
    dataitem = _parse_data({
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