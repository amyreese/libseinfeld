# Copyright 2016 John Reese
# Licensed under the MIT license

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sqlite3

from collections import namedtuple
from functools import wraps


Season = namedtuple('Season', ('id', 'episodes'))
Episode = namedtuple('Episode', ('id', 'season', 'number', 'title',
                                 'date', 'writer', 'director'))

Speaker = namedtuple('Speaker', ('id', 'name'))

# One or more sentences from a single speaker in a single episode
Quote = namedtuple('Quote', ('id', 'episode', 'number', 'speaker', 'text'))

# One or more quotes, in order, from a single episode
Passage = namedtuple('Passage', ('id', 'episode', 'quotes'))


def cached(key_name=None):
    def decorator(method):
        method_cache = {}

        @wraps(method)
        def wrapped_method(self, *args, **kwargs):
            key = None
            if key_name:
                if args:
                    key = args[0]
                key = kwargs.get(key_name, key)

            if key not in method_cache:
                method_cache[key] = method(self, *args, **kwargs)        

            return method_cache.get(key, None)

        return wrapped_method
    return decorator


class Seinfeld(object):
    MAX_QUOTE_ID = 52206  # select id from utterance order by id desc limit 1

    def __init__(self, path='seinfeld.db'):
        self.db_path = path

        self._open = False
        self._db = None
        self._episode_cache = {}
        self._season_cache = {}

    def __enter__(self):
        self.open()
        return self

    def __exit__(self):
        self.close()

    def __repr__(self):
        return '<Seinfeld: {}>'.format(self.db_path)

    def open(self):
        if self._open:
            return

        self._open = True
        self._db = sqlite3.connect(self.db_path)

    def close(self):
        if not self._open:
            return

        if self._db:
            self._db.close()

        self._open = False
        self._db = None

    def cursor(self):
        '''Returns a db cursor. If the connection is closed, this will open it.'''
        if not self._open:
            self.open()

        return self._db.cursor()

    @cached()
    def speakers(self):
        '''Return an alphabetic list of all known speakers.'''

        c = self.cursor()
        c.execute('''
                  select distinct speaker
                  from utterance
                  order by speaker asc
                  ''')

        speakers = []
        for name, in c.fetchall():
            speaker = Speaker(name, name.capitalize())
            speakers.append(speaker)

        return speakers

    @cached('number')
    def season(self, number=None):
        '''Return a season, and the associated episodes.  If `number` is
        `None`, returns all seasons.'''

        if number:
            return self.season().get(number, None)

        c = self.cursor()
        c.execute('''
                  select id, season_number, episode_number,
                    title, the_date, writer, director
                  from episode
                  order by season_number asc, episode_number asc
                  ''')

        seasons = {}
        for row in c.fetchall():
            episode = Episode(*row)

            if episode.season not in seasons:
                seasons[episode.season] = Season(episode.season, {})

            seasons[episode.season].episodes[episode.number] = episode

        return seasons

    def episode(self, season, number):
        '''Return an episode given the season number and episode number.'''

        return self.season(season).episodes[number]

