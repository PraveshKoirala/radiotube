__author__ = 'pravesh'

from google.appengine.ext import ndb


class Songs(ndb.Model):
    """Models an individual Guestbook entry with content and date."""
    name = ndb.StringProperty()
    timestamp = ndb.FloatProperty()
    youtube_id = ndb.StringProperty()
    message = ndb.TextProperty(required=False)
    country = ndb.StringProperty(required=False)
    queue = ndb.BooleanProperty(default=True)
    length = ndb.IntegerProperty(required=True)
    tags = ndb.StringProperty(required=False, repeated=True)

    @classmethod
    def query_book(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.timestamp)

    @classmethod
    def exists(cls, *args):
        return bool(Songs.query(*args).get())