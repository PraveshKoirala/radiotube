from video_details import video_details

__author__ = 'pravesh'

# stack overflow!
# http://stackoverflow.com/questions/16181121/python-very-simple-multithreading-parallel-url-fetching-without-queue

import threading
import urllib2
import time
from google.appengine.api.background_thread.background_thread import start_new_background_thread


def check_if_valid_and_post(song):
    start_new_background_thread(fetch_video_async, args=(song,)).start()
    # threading.Thread(target=fetch_video_async, args=(song,)).start()
    return True


def fetch_video_async(song):
    vid = None
    info = []
    for i in range(100):
        vid = song.youtube_id
        info = video_details(vid)
    print "'%s\' fetched length %d" % (vid, info['length'] )
    song.put()




