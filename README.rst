libseinfeld
===========

Python library for querying Seinfeld quotes.

Depends on a database generated using `scripts by Colin Pollick`_.

.. image:: https://travis-ci.org/jreese/libseinfeld.svg?branch=master
    :target: https://travis-ci.org/jreese/libseinfeld


Install
-------

libseinfeld is compatible with Python 2.7 and Python 3.3+.
You can install it from PyPI with the following command::

    $ pip install seinfeld

libseinfeld requires a local copy of the Seinfeld quote database.
You can build it by following the instructions on the `seinfeld-scripts repo`_,
or you can download a prebuilt copy with the following command::

    $ wget https://noswap.com/pub/seinfeld.db


Usage
-----

First thing is to import libseinfeld and create a connection to the local
database::

    >>> from seinfeld import Seinfeld
    >>> seinfeld = Seinfeld(<path to seinfeld.db>)

To get information on individual episodes or seasons::

    >>> seinfeld.season(1).episodes.keys()
    [1, 2, 3, 4]

    >>> seinfeld.season(1).episodes[1].title
    u'Good News, Bad News'

    >>> seinfeld.season(1).episodes[1].writers[0]
    u'Jerry Seinfeld'

    >>> seinfeld.season(1).episodes[1].date
    datetime.date(1990, 6, 14)

Quotes can be retrieved by unique ID::

    >>> quote = seinfeld.quote(34665)
    >>> quote.text
    u'The show is about nothing.'

    >>> quote.speaker.name
    u'George'

    >>> quote.episode.title
    u'The Pitch'

Searching for quotes is simple::

    >>> seinfeld.search(speaker='Jerry', subject='keys')
    [Quote(...), ...]

Searches are limited to ten quotes by default, but you can get more or less.
To get all the quotes, in order, for a given episode::

    >>> episode = seinfeld.season(1).episodes[1]
    >>> quotes = seinfeld.search(episode=episode, limit=None)
    >>> len(quotes)
    209

You can even get random quotes by search query::

    >>> seinfeld.random(speaker='George')
    Quote(...)

If you'd like context around an individual quote, you can get a passage::

    >>> passage = seinfeld.passage(quote)
    >>> len(passage.quotes)
    5


License
-------

Copyright 2016 John Reese, and licensed under the MIT license.
See the ``LICENSE`` file for details.

.. _scripts by Colin Pollick: https://github.com/colinpollock/seinfeld-scripts
.. _seinfeld-scripts repo: https://github.com/colinpollock/seinfeld-scripts
