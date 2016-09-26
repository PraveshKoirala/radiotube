from models import Songs

__author__ = 'pravesh'

# from pymongo import MongoClient
from utils import _parse_data
from google.appengine.ext import ndb


data = [
    {
      "name": "Kale Dai",
      "message": "Cat loves printer!!",
      "country": "China",
      "youtube": "https://www.youtube.com/watch?v=dOhIMh4aoh0&index=2&list=PL9FUXHTBubp-_e0wyNu1jfVVJ2QVAi5NW"
    },

    {
        "name": "Basnet Kaji",
        "message": "World Peace!",
        "country": "Nepal",
        "youtube": "https://www.youtube.com/watch?v=JBQ7NMm2"
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
      "youtube": "https://www.youtube.com/watch?v=dOhIMh4aoh0&index=2&list=PL9FUXHTBubp-_e0wyNu1jfVVJ2QVAi5NW"
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

    ndb.delete_multi(
        Songs.query().fetch(keys_only=True)
    )

    print "Loading new data"
    for d in data:
        s = _parse_data(d)
        s.put()

    print "Done!"
