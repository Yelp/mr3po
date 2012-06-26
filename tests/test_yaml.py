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

from mock import call
from mock import Mock
from yaml.constructor import ConstructorError
from yaml.representer import RepresenterError

from mr3po.yaml import SafeYAMLProtocol
from mr3po.yaml import SafeYAMLValueProtocol
from mr3po.yaml import YAMLProtocol
from mr3po.yaml import YAMLValueProtocol
from tests.roundtrip import RoundTripTestCase


SAFE_KEY_VALUES = [
    (None, None),
    (1, 2),
    ('foo', 'bar'),
    ([], []),
    ([1, 2, 3], ['A', 'B', 'C']),
    ({'apples': 5}, {'oranges': 20}),
    (u'Qu\xe9bec', u'Ph\u1ede'),
    ('\t', '\n'),
    (set([1, 2, 3]), {1: set(['A', 'B', 'C'])}),
]

SAFE_VALUE_TUPLES = [(None, v) for k, v in SAFE_KEY_VALUES]

UNSAFE_KEY_VALUES = [
    (Decimal('1.3'), Decimal('3.1')),
    (object(), object()),
    (YAMLProtocol, YAMLValueProtocol),
    # yaml module can encode lambdas but not decode them
    #(lambda x: x,
    # (lambda f: (lambda x: f(lambda v: x(x)(v)))(
    #     lambda x: f(lambda v: x(x)(v)))))
]

UNSAFE_VALUE_TUPLES = [(None, v) for k, v in UNSAFE_KEY_VALUES]

KEY_VALUES = (
    SAFE_KEY_VALUES + UNSAFE_KEY_VALUES)
VALUE_TUPLES = (
    SAFE_VALUE_TUPLES + UNSAFE_VALUE_TUPLES)


class YAMLProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
        YAMLProtocol(),
        YAMLProtocol(encoding='utf_7'),
        YAMLProtocol(encoding='utf_8'),
        YAMLProtocol(encoding='utf_16'),
    ]

    WRW_KEY_VALUES = KEY_VALUES
    KEY_VALUES = KEY_VALUES


class YAMLValueProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
        YAMLValueProtocol(),
        YAMLValueProtocol(encoding='utf_7'),
        YAMLValueProtocol(encoding='utf_8'),
        YAMLValueProtocol(encoding='utf_16'),
    ]

    WRW_KEY_VALUES = KEY_VALUES
    KEY_VALUES = VALUE_TUPLES


class SafeYAMLProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
        SafeYAMLProtocol(),
        SafeYAMLProtocol(encoding='utf_7'),
        SafeYAMLProtocol(encoding='utf_8'),
        SafeYAMLProtocol(encoding='utf_16'),
    ]

    WRW_KEY_VALUES = KEY_VALUES
    KEY_VALUES = SAFE_KEY_VALUES


class SafeYAMLValueProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
        SafeYAMLValueProtocol(),
        SafeYAMLValueProtocol(encoding='utf_7'),
        SafeYAMLValueProtocol(encoding='utf_8'),
        SafeYAMLValueProtocol(encoding='utf_16'),
    ]

    WRW_KEY_VALUES = KEY_VALUES
    KEY_VALUES = SAFE_VALUE_TUPLES


class SafetyTestCase(unittest.TestCase):

    def test_protocol_wont_encode(self):
        safe_p = SafeYAMLProtocol()

        for key, value in UNSAFE_KEY_VALUES:
            self.assertRaises(RepresenterError, safe_p.write, key, value)

    def test_value_protocol_wont_encode(self):
        safe_p = SafeYAMLValueProtocol()

        for key, value in UNSAFE_VALUE_TUPLES:
            self.assertRaises(RepresenterError, safe_p.write, key, value)

    def test_protocol_wont_decode(self):
        p = YAMLProtocol()
        safe_p = SafeYAMLProtocol()

        for key, value in UNSAFE_KEY_VALUES:
            encoded = p.write(key, value)
            self.assertRaises(ConstructorError, safe_p.read, encoded)

    def test_value_protocol_wont_decode(self):
        p = YAMLValueProtocol()
        safe_p = SafeYAMLValueProtocol()

        for key, value in UNSAFE_VALUE_TUPLES:
            encoded = p.write(key, value)
            self.assertRaises(ConstructorError, safe_p.read, encoded)

    def test_tuples_become_lists(self):
        p = YAMLProtocol()
        safe_p = SafeYAMLProtocol()

        self.assertEqual(p.read(safe_p.write((), ())), ([], []))
        self.assertRaises(
            ConstructorError, safe_p.read, p.write((), ()))


class CachingTestCase(unittest.TestCase):

    def test_caching(self):
        p = YAMLProtocol()
        # wrap load() with a mock so we can track calls to it
        p.load = Mock(wraps=p.load)

        self.assertEqual(p.read('[a, 1]\t2'), (['a', 1], 2))
        self.assertEqual(p.read('[a, 1]\t3'), (['a', 1], 3))
        self.assertEqual(p.read('[b, 2]\t3'), (['b', 2], 3))
        self.assertEqual(p.read('[a, 1]\t3'), (['a', 1], 3))

        self.assertEqual(
            p.load.call_args_list,
            [call('[a, 1]'), call('2'),
             # '[a, 1]' isn't decoded again because it's in the cache
             call('3'),
             # '3' is decoded repeatedly because we don't cache values
             call('[b, 2]'), call('3'),
             # '[a, 1]' is re-decoded because the cache only holds one key
             call('[a, 1]'), call('3')])
