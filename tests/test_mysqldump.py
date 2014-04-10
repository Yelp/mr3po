# -*- coding: utf-8 -*-
# Copyright 2012 Yelp
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from decimal import Decimal

try:
    import unittest2 as unittest
    unittest  # quiet "redefinition of unused ..." warning from pyflakes
except ImportError:
    import unittest

from mr3po.mysqldump import AbstractMySQLInsertProtocol
from mr3po.mysqldump import MySQLExtendedCompleteInsertProtocol
from mr3po.mysqldump import MySQLCompleteInsertProtocol
from mr3po.mysqldump import MySQLExtendedInsertProtocol
from mr3po.mysqldump import MySQLInsertProtocol

from tests.roundtrip import RoundTripTestCase


class GoodInputTestCase(unittest.TestCase):

    def test_insert(self):
        p = MySQLInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL);")
        self.assertEqual(
            (key, value),
            (u'user', [1, u'David Marin', 25.25, '\xc0\xde', None]))

    def test_complete_insert(self):
        p = MySQLCompleteInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 1,
                                     u'name': u'David Marin',
                                     u'score': 25.25,
                                     u'data': '\xc0\xde',
                                     u'misc': None}))

    def test_extended_insert(self):
        p = MySQLExtendedInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL),"
            " (2,'Nully Nullington',NULL,NULL,NULL);")
        self.assertEqual(
            (key, value),
            (u'user', [[1, u'David Marin', 25.25, '\xc0\xde', None],
                       [2, u'Nully Nullington', None, None, None]]))

    def test_extended_complete_insert(self):
        p = MySQLExtendedCompleteInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL),"
            " (2,'Nully Nullington',NULL,NULL,NULL);")
        self.assertEqual(
            (key, value), (u'user', [{u'id': 1,
                                      u'name': u'David Marin',
                                      u'score': 25.25,
                                      u'data': '\xc0\xde',
                                      u'misc': None},
                                     {u'id': 2,
                                      u'name': u'Nully Nullington',
                                      u'score': None,
                                      u'data': None,
                                      u'misc': None}]))


class BadInputTestCase(unittest.TestCase):

    def test_empty(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(ValueError, p.read, '')

    def test_non_insert(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(ValueError, p.read, 'USE test;')

    def test_missing_close_paren(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(
            ValueError,
            p.read, "INSERT INTO `user` VALUES (1,'David Marin'")

    def test_rows_and_cols_dont_match(self):
        p = MySQLExtendedInsertProtocol()
        # this is a problem even if the protocol doesn't care about
        # column names
        self.assertRaises(
            ValueError,
            p.read,
            "INSERT INTO `user` (`id`) VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL);")

    def test_differing_row_sizes(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(
            ValueError,
            p.read,
            "INSERT INTO `user` VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL), (2);")


class EncodingTestCase(unittest.TestCase):

    def test_default_encoding(self):
        p = MySQLCompleteInsertProtocol()
        # encoded in UTF-8
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (3,'Paul Erdős',0,0x0E2D05,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 3,
                                     u'name': u'Paul Erdős',
                                     u'score': 0,
                                     u'data': '\x0e\x2d\x05',
                                     u'misc': None, }))

        key, value = p.read(
            # encoded in latin-1, with ö instead of ő
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (3,'Paul Erd\xf6s',0,0x0E2D05,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 3,
                                     u'name': u'Paul Erdös',
                                     u'score': 0,
                                     u'data': '\x0e\x2d\x05',
                                     u'misc': None, }))

    def test_alternate_encoding(self):
        p = MySQLCompleteInsertProtocol(encoding='latin-1')
        # encoded in UTF-8, but we will decode it in latin-1
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (3,'Paul Erdős',0,0x0E2D05,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 3,
                                     u'name': 'Paul Erdős'.decode('latin-1'),
                                     u'score': 0,
                                     u'data': '\x0e\x2d\x05',
                                     u'misc': None}))


class NumberTestCase(unittest.TestCase):

    def test_int_vs_float(self):
        p = MySQLInsertProtocol()
        key, value = p.read("INSERT INTO `score` (1, 1.0, 1.25)")
        self.assertEqual(key, 'score')
        self.assertEqual(value, [1, 1.0, 1.25])
        self.assertEqual([type(x) for x in value], [int, float, float])

    def test_decimal(self):
        p = MySQLInsertProtocol(decimal=True)
        key, value = p.read("INSERT INTO `score` (1, 1.0, 1.25)")
        self.assertEqual(key, 'score')
        self.assertEqual(value, [1, Decimal('1.0'), Decimal('1.25')])
        self.assertEqual([type(x) for x in value], [int, Decimal, Decimal])


class OutputTabTestCase(unittest.TestCase):

    def test_tabs(self):
        p = MySQLInsertProtocol(output_tab=True)

        row1 = p.write('score', [1, 1.0, 1.25])
        row2 = p.write('score', [0, None, None])
        row3 = p.write('user', [2, u'Nully Nullington', None, None, None])

        self.assertEqual(row1.split('\t')[0], row2.split('\t')[0])
        self.assertNotEqual(row1.split('\t')[0], row3.split('\t')[0])

    def test_no_tabs(self):
        p = MySQLInsertProtocol()

        row1 = p.write('score', [1, 1.0, 1.25])
        row2 = p.write('score', [0, None, None])

        self.assertNotEqual(row1.split('\t')[0], row2.split('\t')[0])


class MySQLInsertProtocolTestCase(RoundTripTestCase):
    PROTOCOLS = [
        MySQLInsertProtocol(),
        MySQLInsertProtocol(output_tab=True),
        MySQLInsertProtocol(encoding='utf16'),
    ]

    ROUND_TRIP_KEY_VALUES = [
        ('user', [1, u'David Marin', 25.25, '\xc0\xde', None]),
        ('user', [2, u'Nully Nullington', None, None, None]),
        ('user', [3, u'Paul Erdős', 0, '\x0e\x2d\x05', None]),
    ]


class MySQLInsertProtocolDecimalTestCase(RoundTripTestCase):
    PROTOCOLS = [
        MySQLInsertProtocol(decimal=True),
    ]

    ROUND_TRIP_KEY_VALUES = [
        ('user', [4, u'Ezra', Decimal('2010.66'), None, None]),
    ]


class MySQLCompleteInsertProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
        MySQLCompleteInsertProtocol(),
        MySQLCompleteInsertProtocol(output_tab=True),
        MySQLCompleteInsertProtocol(encoding='utf16'),
    ]

    ROUND_TRIP_KEY_VALUES = [
        ('user', {'id': 1,
                  'name': u'David Marin',
                  'score': 25.25,
                  'data': '\xc0\xde',
                  'misc': None}),
        ('user', {'id': 2,
                  'name': u'Nully Nullington',
                  'score': None,
                  'data': None,
                  'misc': None}),
        ('user', {'id': 3,
                  'name': u'Paul Erdős',
                  'score': 0,
                  'data': '\x0e\x2d\x05',
                  'misc': None}),
    ]


class MySQLExtendedInsertProtocolTestCase(RoundTripTestCase):
    PROTOCOLS = [
        MySQLExtendedInsertProtocol(),
        MySQLExtendedInsertProtocol(output_tab=True),
        MySQLExtendedInsertProtocol(encoding='utf16'),
    ]

    ROUND_TRIP_KEY_VALUES = [
        ('user', [[1, u'David Marin', 25.25, '\xc0\xde', None],
                  [2, u'Nully Nullington', None, None, None],
                  [3, u'Paul Erdős', 0, '\x0e\x2d\x05', None]]),
    ]


class MySQLExtendedCompleteInsertProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
        MySQLExtendedCompleteInsertProtocol(),
        MySQLExtendedCompleteInsertProtocol(output_tab=True),
        MySQLExtendedCompleteInsertProtocol(encoding='utf16'),
    ]

    ROUND_TRIP_KEY_VALUES = [
        ('user', [{'id': 1,
                   'name': u'David Marin',
                   'score': 25.25,
                   'data': '\xc0\xde',
                   'misc': None},
                  {'id': 2,
                   'name': u'Nully Nullington',
                   'score': None,
                   'data': None,
                   'misc': None},
                  {'id': 3,
                   'name': u'Paul Erdős',
                   'score': 0,
                   'data': '\x0e\x2d\x05',
                   'misc': None},
                  ]),
    ]


class NotImplementedExceptions(unittest.TestCase):

    def test_complete(self):
        p = AbstractMySQLInsertProtocol()
        with self.assertRaises(NotImplementedError):
            p.complete()

    def test_single_row(self):
        p = AbstractMySQLInsertProtocol()
        with self.assertRaises(NotImplementedError):
            p.single_row()


if __name__ == '__main__':
    unittest.main()
