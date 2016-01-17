# Copyright 2016 John Reese
# Licensed under the MIT license

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sqlite3

from collections import namedtuple
from dateutil.parser import parse
from functools import wraps


Speaker = namedtuple('Speaker', ('id', 'name'))

# One or more sentences from a single speaker in a single episode
Quote = namedtuple('Quote', ('id', 'episode', 'number', 'speaker', 'text'))

# One or more quotes, in order, from a single episode
Passage = namedtuple('Passage', ('id', 'episode', 'quotes'))

Season = namedtuple('Season', ('number', 'episodes'))
Episode = namedtuple('Episode', ('id', 'season', 'number', 'title',
                                 'date', 'writers', 'director'))


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

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return '<Seinfeld: {}>'.format(self.db_path)

    def open(self):
        if self._open:
            return

        self._open = True
        self._db = sqlite3.connect(self.db_path)

        self._db.execute('''
                         CREATE TEMPORARY VIEW IF NOT EXISTS quote AS
                         SELECT u.id, u.episode_id, u.utterance_number,
                            u.speaker, group_concat(s.text, " ") text
                         FROM utterance u
                         JOIN sentence s ON u.id = s.utterance_id
                         GROUP BY u.id
                         ORDER BY u.episode_id asc, u.utterance_number asc,
                            s.sentence_number asc
                         ''')

    def close(self):
        if not self._open:
            return

        if self._db:
            self._db.close()

        self._open = False
        self._db = None

    def cursor(self):
        '''Returns a cursor. If the connection is closed, this will open it.'''
        if not self._open:
            self.open()

        return self._db.cursor()

    @cached('name')
    def speaker(self, name=None):
        '''Return a speaker with the given name.  If `name` is `None`, returns
        a dictionary of all known speakers.'''

        if name:
            return self.speaker().get(name.upper(), None)

        c = self.cursor()
        c.execute('''
                  select distinct speaker
                  from utterance
                  ''')

        speakers = {}
        for name, in c.fetchall():
            speaker = Speaker(name, name.capitalize())
            speakers[speaker.id] = speaker

        return speakers

    @cached('number')
    def season(self, number=None):
        '''Return a season, and the associated episodes.  If `number` is
        `None`, returns all seasons.'''

        if number:
            return self.season().get(number, None)

        seasons = {}
        for episode in self.episode().values():
            if episode.season not in seasons:
                seasons[episode.season] = Season(episode.season, {})

            seasons[episode.season].episodes[episode.number] = episode

        return seasons

    @cached('id')
    def episode(self, id=None):
        '''Return a season, and the associated episodes.  If `number` is
        `None`, returns all seasons.'''

        if id:
            return self.episode().get(id, None)

        c = self.cursor()
        c.execute('''
                  select id, season_number, episode_number,
                    title, the_date, writer, director
                  from episode
                  order by season_number asc, episode_number asc
                  ''')

        episodes = {}
        for row in c.fetchall():
            episode = self._episode(row)

            episodes[episode.id] = episode

        return episodes

    def _episode(self, row):
        '''Build episode from db row, substituting date object, splitting
        writers, etc.'''

        row = list(row)
        row[4] = parse(row[4]).date()
        row[5] = {w.strip() for w in row[5].split(',')}

        return Episode(*row)

    def _quote(self, row):
        '''Build quote from db row, substituting episode and speaker objects
        in place of IDs.'''

        row = list(row)
        row[1] = self.episode(row[1])
        row[3] = self.speaker(row[3])

        return Quote(*row)

    def quote(self, id):
        '''Return a single quote with the given ID.'''

        if id < 1 or id > self.MAX_QUOTE_ID:
            raise ValueError('Quote ID out of range')

        c = self.cursor()
        query = '''
                select id, episode_id, utterance_number, speaker, text
                from quote
                where id = ?
                '''
        c.execute(query, (id,))
        return self._quote(c.fetchone())

    def passage(self, quote, length=5):
        '''Given a quote object, return a passage of the given length
        surrounding the quote.'''

        if not isinstance(quote, Quote):
            quote = self.quote(quote)

        c = self.cursor()
        query = '''
                select id, episode_id, utterance_number, speaker, text
                from quote
                where episode_id = ? and
                    utterance_number >= ? and utterance_number <= ?
                order by utterance_number
                '''

        half = length // 2
        middle = quote.number
        start = middle - half if middle > half else 1
        end = start + length - 1

        c.execute(query, (quote.episode.id, start, end))

        quotes = [self._quote(row) for row in c.fetchall()]
        return Passage(quote.id, quote.episode, quotes)

    def search(self, episode=None, speaker=None, subject=None,
               limit=10, reverse=False, random=False):
        '''Return a list of quotes, in order, given the search criteria.'''

        if not any((episode, speaker, subject)):
            raise ValueError('Must specify episode, speaker, or subject')

        if episode and not isinstance(episode, Episode):
            episode = self.episode(id=episode)

        if speaker and not isinstance(speaker, Speaker):
            speaker = self.speaker(name=speaker)

        c = self.cursor()
        query = '''
                select id, episode_id, utterance_number, speaker, text
                from quote
                where {}
                order by {}
                limit {}
                '''

        wheres = []
        params = []

        if episode:
            wheres.append('episode_id = ?')
            params.append(episode.id)

        if speaker:
            wheres.append('speaker = ?')
            params.append(speaker.id)

        if subject:
            wheres.append('text like ?')
            params.append('%{}%'.format(subject))

        if random:
            order = 'RANDOM()'
        elif reverse:
            order = 'episode_id desc, utterance_number desc'
        else:
            order = 'episode_id asc, utterance_number asc'

        if not limit:
            limit = '-1'

        query = query.format(' and '.join(wheres), order, limit)
        c.execute(query, params)

        return [self._quote(row) for row in c.fetchall()]

    def random(self, speaker=None, subject=None):
        '''Returns a single quote matching the given search criteria.
        Shorthand for `search(... limit=1, random=True)[0]`.'''

        quotes = self.search(speaker=speaker, subject=subject,
                             limit=1, random=True)

        if quotes:
            return quotes[0]
        else:
            return None
