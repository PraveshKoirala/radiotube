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
import webapp2
from utils import get_song, post_song
from loaddata import reload

def _json(handler, data):
    handler.response.headers["Access-Control-Allow-Origin"] = "*"
    handler.response.headers['Content-Type'] = 'application/json'
    handler.response.write(json.dumps(data))


class SongsHandler(webapp2.RequestHandler):
    def get(self):
        _json(self, get_song())

    def post(self):
        data = {}
        result = {}
        try:
            data = json.loads(self.request.body)
        except:
            _json(self, {"error": "Invalid data format"})
            return

        if data:
            try:
                result = post_song(data)
            except Exception, e:
                _json(self, {"error": e.message})
                return

        return _json(self, result)


class Update(webapp2.RequestHandler):
    def get(self):
        # reload()
        return _json(self, {"success": True})


class MainHandler(webapp2.RequestHandler):
    def get(self):
        return _json(self, {"sucess": "Now server static contents!"})


app = webapp2.WSGIApplication([
    ('/songs', SongsHandler),
    ('/reload', Update),
    ('/', MainHandler)
], debug=True)
