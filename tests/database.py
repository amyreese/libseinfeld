# Copyright 2022 Amethyst Reese
# Licensed under the MIT license

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime as dt
import unittest

from seinfeld import Seinfeld


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.seinfeld = Seinfeld()
        self.seinfeld.open()

    def tearDown(self):
        self.seinfeld.close()

    def test_db_counts(self):
        self.assertEqual(len(self.seinfeld.episode()), 173)
        self.assertEqual(len(self.seinfeld.season()), 9)
        self.assertEqual(len(self.seinfeld.speaker()), 726)

        c = self.seinfeld.cursor()
        c.execute('select id from utterance order by id desc limit 1')
        count, = c.fetchone()

        self.assertEqual(count, 52206)
        self.assertEqual(self.seinfeld.MAX_QUOTE_ID, 52206)

    def test_data(self):
        season = self.seinfeld.season(2)
        self.assertEqual(season.number, 2)
        self.assertIsInstance(season.episodes, dict)
        self.assertEqual(len(season.episodes), 12)

        episode = season.episodes[3]
        self.assertEqual(episode.season, 2)
        self.assertEqual(episode.number, 3)
        self.assertEqual(episode.title, 'The Jacket')
        self.assertIsInstance(episode.date, dt.date)
        self.assertEqual(episode.date, dt.date(1991, 2, 6))

        self.assertIsInstance(episode.writers, set)
        self.assertIn('Larry David', episode.writers)
        self.assertIn('Jerry Seinfeld', episode.writers)
        self.assertEqual(episode.director, 'Tom Cherones')

    def test_quote(self):
        speaker = self.seinfeld.speaker('GEORGE')
        episode = self.seinfeld.season(4).episodes[3]
        quote = self.seinfeld.quote(34663)

        self.assertEqual(quote.id, 34663)
        self.assertEqual(quote.episode, episode)
        self.assertEqual(quote.number, 250)
        self.assertEqual(quote.speaker, speaker)
        self.assertEqual(quote.text, '(Smiling) Nothing.')

    def test_search_single_quote(self):
        speaker = self.seinfeld.speaker('CUSTOMER')
        episode = self.seinfeld.season(2).episodes[3]
        quotes = self.seinfeld.search(speaker=speaker, subject='Alton Benes')
        self.assertEquals(len(quotes), 1)

        quote = quotes[0]
        self.assertEqual(quote.id, 1442)
        self.assertEqual(quote.episode, episode)
        self.assertEqual(quote.number, 6)
        self.assertEqual(quote.speaker, speaker)
        self.assertEqual(quote.text, 'Alton Benes is your father?')

    def test_search_multi_quote(self):
        speaker = self.seinfeld.speaker('ELAINE')
        episode = self.seinfeld.season(3).episodes[14]

        # test default limit
        quotes = self.seinfeld.search(episode=episode, speaker=speaker)
        self.assertEquals(len(quotes), 10)

        # test custom limit
        quotes = self.seinfeld.search(episode=episode, speaker=speaker,
                                      limit=5)
        self.assertEquals(len(quotes), 5)

        # test no limit
        quotes = self.seinfeld.search(episode=episode, speaker=speaker,
                                      limit=None)
        self.assertEquals(len(quotes), 37)

        last_number = 0
        for quote in quotes:
            self.assertEqual(quote.episode, episode)
            self.assertGreater(quote.number, last_number)
            self.assertEqual(quote.speaker, speaker)
            self.assertTrue(quote.text)

            last_number = quote.number

    def test_passage(self):
        speaker = self.seinfeld.speaker('GEORGE')
        episode = self.seinfeld.season(4).episodes[3]
        quote = self.seinfeld.quote(34663)

        # custom length
        passage = self.seinfeld.passage(quote, length=10)
        self.assertEqual(len(passage.quotes), 10)

        # default length
        passage = self.seinfeld.passage(quote)
        self.assertEqual(len(passage.quotes), 5)

        self.assertTrue(passage)
        self.assertEqual(passage.id, 34663)
        self.assertEqual(passage.episode, episode)

        # passage beginning
        quote = passage.quotes[0]
        self.assertEqual(quote.id, 34661)
        self.assertEqual(quote.episode, episode)
        self.assertEqual(quote.number, 248)
        self.assertEqual(quote.speaker, speaker)
        self.assertTrue(quote.text.startswith('I think I can sum up the show'))

        # passage ending
        quote = passage.quotes[-1]
        self.assertEqual(quote.id, 34665)
        self.assertEqual(quote.episode, episode)
        self.assertEqual(quote.number, 252)
        self.assertEqual(quote.speaker, speaker)
        self.assertEqual(quote.text, 'The show is about nothing.')
