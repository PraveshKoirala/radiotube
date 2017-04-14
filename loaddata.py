from models import Songs

__author__ = 'pravesh'

# from pymongo import MongoClient
from utils import load_data
from google.appengine.ext import ndb
import google.appengine.api.memcache as mc


load_songs = [
    {
      "name": "Kale Dai",
      "message": "Cat loves printer!!",
      "country": "China",
      "youtube": "https://www.youtube.com/watch?v=dOhIMh4aoh0&index=2&list=PL9FUXHTBubp-_e0wyNu1jfVVJ2QVAi5NW",
      "tags": ["rock", "pop", "australia"]
    },
    {
        "name": "Basnet Kaji",
        "message": "World Peace!",
        "country": "Nepal",
        "youtube": "https://www.youtube.com/watch?v=JBQ7NMm2",
        "tags": ['folk', "nepal"]
    },

    {
        "name": "Prakash Aryal",
        "message": "Kathmandu Rocks!",
        "country": "South Africa",
        "youtube": "https://www.youtube.com/watch?v=F_MNNzqQnkg",
    },
    {
      "name": "Bhale Dai",
      "message": "Basketball player!!",
      "country": "New York",
      "youtube": "https://www.youtube.com/watch?v=dOhIMh4aoh0&index=2&list=PL9FUXHTBubp-_e0wyNu1jfVVJ2QVAi5NW",
      "tags": "rock and roll"
    },

    {
        "name": "Sushila Devi",
        "message": "<3 <3 to Sushmita.. you are my sweetheart!",
        "country": "India",
        "youtube": "https://www.youtube.com/watch?v=pybCDZY0k_I",
    },
]


def reload():

    print "Dropping Database"
    mc.flush_all()
    ndb.delete_multi(
        Songs.query().fetch(keys_only=True)
    )

    print "Loading new data"
    for d in load_songs:
        try:
            s = load_data(d)
            s.put()
        except Exception, e:
            print "Exception occured " + e.message

    print "Done!"
