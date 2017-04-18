#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json
import random
from urllib import urlencode
from google.appengine.api import urlfetch
from google.appengine.api.taskqueue import taskqueue
import re
import webapp2
import default_songs
from utils import get_song, post_song, KEY, get_cached_song, get_similar_songs, load_data, update_cached_song, \
    get_queue_length
from loaddata import reload, load_songs
from logging import info, error, debug


def validate_captcha(self):
    recaptcha_response_field = self.request.params.get("g-recaptcha-response")
    remote_ip = self.request.remote_addr
    secret = '6Lef9wcUAAAAADH8LM23EjZKonRDVQHMjQiFJzkt'  # put recaptcha private key here

    recaptcha_post_data = {
        "secret":  secret,
        "remoteip": remote_ip,
        "response": recaptcha_response_field}

    response = urlfetch.fetch(url='https://www.google.com/recaptcha/api/siteverify',
                              payload=urlencode(recaptcha_post_data), method="POST")
    response = json.loads(response.content)
    return response['success']


def _json(handler, data):
    handler.response.headers["Access-Control-Allow-Origin"] = "*"
    handler.response.headers['Content-Type'] = 'application/json'
    debug("Sending following response: {0}".format(json.dumps(data)))
    handler.response.write(json.dumps(data))


def get_default_songs_with_tags(t):
    debug("Getting default songs for the following tags: {0}".format(" ".join(t or ['default'])))
    return filter(lambda obj: t in obj.get("tags", []), default_songs.songs)


def get_youtube_id_from_url(youtube_link):
    debug("Getting youtube id from youtube link: {0}".format(youtube_link))
    youtube_id = re.findall(r'\?.*&?v=([^&]+).*', youtube_link)
    debug("Youtube id is: {0}".format(youtube_id))
    return youtube_id[0]


def get_default_songs(tags):
    song_list = []
    for t in sorted(tags):
        song_list += get_default_songs_with_tags(t)
    if not song_list:
        song_list = default_songs.songs
    song = random.choice(song_list)
    if len(song_list) == len(default_songs.songs):
        song["tags"] = []
    info("returning the song " + repr(song))
    song = {
        "username_message": [{"name": "resham", "message": "Happy new year!"}],
        "youtube_id": get_youtube_id_from_url(song['youtube']),
        "tags": song["tags"]
    }
    # add to the memcache...
    taskqueue.add(url="/add_default", payload=json.dumps(song), method="POST")
    return song


class SongsHandler(webapp2.RequestHandler):
    def get(self):
        tags = self.request.params.get("tags", '').split(",")
        tags = [t.lower() for t in tags]
        debug("Got following tags {0}".format(" ".join(tags)))
        data = get_song(tags)
        if not data:
            debug("Got empty data")
            return _json(self, get_default_songs(tags))
        debug("Data for the tags: {0}" + json.dumps(data))
        return _json(self, data)

    def post(self):
        data = {}
        result = {}
        try:
            data = json.loads(self.request.body)
        except Exception:
            _json(self, {"error": "Invalid data format"})
            return

        if data:
            debug("Received following post request: {0}".format(json.dumps(data)))
            if data.get('validated'):
                try:
                    info("Posting results")
                    result = post_song(data)
                except Exception, e:
                    _json(self, {"error": e.message})
                    return
            else:
                # validate the data before adding to the database.
                info("added to the task queue")
                data.update({"validated": True})
                taskqueue.add(url="/songs", payload=json.dumps(data), method="POST")
                result = {"message": "Added to the queue.", "success": True, "estimated_time": get_queue_length()}

        return _json(self, result)


class Update(webapp2.RequestHandler):
    def get(self):
        reload()
        return _json(self, {"success": True})


class MainHandler(webapp2.RequestHandler):
    def get(self):
        return _json(self, {"sucess": "Now server static contents!"})

    def post(self):
        is_valid_captcha = validate_captcha(self)
        return _json(self, {"captcha": is_valid_captcha})


class AddDefaultHandler(webapp2.RequestHandler):
    def post(self):
        info("Adding a default song to the cache")
        data = json.loads(self.request.body)
        data["youtube"] = "https://youtube.com/watch?v=" + data["youtube_id"]
        data["name"] = data["message"] = "default"

        # we need to add this data to memcache.
        tags = data.get("tags", [])
        memkey = KEY + "_" + "_".join(sorted(tags))
        cache = get_cached_song(memkey)
        if cache:
            return
        # Not loaded in the cache.. now load.. we need the length for that
        song = load_data(data)
        update_cached_song(data, song.length, memkey)
        return


app = webapp2.WSGIApplication([
    ('/songs', SongsHandler),
    ('/reload', Update),
    ('/add_default', AddDefaultHandler),
    ('/', MainHandler)
], debug=True)
