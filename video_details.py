__author__ = 'pravesh'

import json
import urllib
import re


def YTDurationToSeconds(duration):
    match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
    hours = _js_parseInt(match[0]) if match[0] else 0
    minutes = _js_parseInt(match[1]) if match[1] else 0
    seconds = _js_parseInt(match[2]) if match[2] else 0
    return hours * 3600 + minutes * 60 + seconds

# js-like parseInt
# https://gist.github.com/douglasmiranda/2174255
def _js_parseInt(string):
    return int(''.join([x for x in string if x.isdigit()]))


def video_details(video_id):
    api_key = "AIzaSyD87Y5RhYQ2wC0PoS2wIWAGs-d2akiTbI4"
    searchUrl = "https://www.googleapis.com/youtube/v3/videos?part=contentDetails,statistics&id="+video_id + "&key=" + api_key
    response = urllib.urlopen(searchUrl).read()
    data = json.loads(response)
    all_data = data['items']

    contentDetails = all_data[0]['contentDetails']
    statistics = all_data[0]['statistics']

    duration = YTDurationToSeconds(contentDetails['duration'])

    return {
        "length": duration,
        "views": statistics['viewCount'],
        "rating": 5 * int(statistics["likeCount"]) / (int(statistics["likeCount"]) + int(statistics["dislikeCount"]) + 1.)
    }

if __name__ == '__main__':
    print video_details("PYD-DIggB2k")