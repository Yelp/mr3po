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
"""A basic test than any protocol p should pass.

There should be at least one pair of values (k, v) that can survive the
round trip, that is, p.read(p.write(k, v)) == (k, v)

Additionally, for ANY pair of values (k, v):

p.write(*p.read(p.write(k, v))) should either equal p.write(k, v),
or p.write(k, v) should raise an exception.

Finally, p.write() should always return a str, and p.read() should always
return a tuple of two values.
"""
from decimal import Decimal

try:
    import unittest2 as unittest
    unittest  # quiet "redefinition of unused ..." warning from pyflakes
except ImportError:
    import unittest

# keys and values that should encode/decode properly in most protocols
SAFE_KEYS_AND_VALUES = [
    (None, None),
    (1, 2),
    ('foo', 'bar'),
    ([], []),
    ((), ()),
    ([1, 2, 3], ['A', 'B', 'C']),
    (['A', 'B', 'C'], (1, 2, 3)),
    ({'apples': 5}, {'oranges': 20}),
    (u'Qu\xe9bec', u'Ph\u1ede'),
    ('\t', '\n'),
]


DEFAULT_WRW_KEY_VALUES = SAFE_KEYS_AND_VALUES + [
    (set([1, 2, 3]), {1: set(['A', 'B', 'C'])}),
    (Decimal('1.3'), Decimal('3.1')),
]


class RoundTripTestCase(unittest.TestCase):
    PROTOCOLS = []

    WRW_KEY_VALUES = DEFAULT_WRW_KEY_VALUES

    ROUND_TRIP_KEY_VALUES = []

    # don't run the base class of this test case
    def run(self, result=None):
        if self.__class__ == RoundTripTestCase:
            return
        else:
            super(RoundTripTestCase, self).run(result=result)

    def test_round_trip(self):
        if not self.PROTOCOLS:
            self.skipTest('PROTOCOLS is empty')

        if not self.ROUND_TRIP_KEY_VALUES:
            self.skipTest('ROUND_TRIP_KEY_VALUES is empty')

        for p in self.PROTOCOLS:
            for key, value in self.ROUND_TRIP_KEY_VALUES:
                encoded = p.write(key, value)
                self.assertEqual(
                    type(encoded), str,
                    '%r.write() should encode (%r, %r) as a bytestring,'
                    ' not %r' % (p, key, value, encoded))

                decoded = p.read(encoded)
                self.assertEqual(
                    type(decoded), tuple,
                    '%r.read() should encode %r as a tuple, not %r' %
                    (p, encoded, decoded))

                self.assertEqual(
                    decoded, (key, value),
                    '%r failed to write then read (%r, %r)' %
                    (p, key, value))

    def test_wrw_equals_w(self):
        if not self.WRW_KEY_VALUES:
            self.skipTest('WRW_KEY_VALUES is empty')

        if not self.PROTOCOLS:
            self.skipTest('PROTOCOLS is empty')

        for p in self.PROTOCOLS:
            for key, value in self.WRW_KEY_VALUES:
                try:
                    encoded = p.write(key, value)
                except:
                    # can't encode this value. That's fine.
                    return

                self.assertEqual(
                    type(encoded), str,
                    '%r.write() should encode (%r, %r) as a bytestring,'
                    ' not %r' % (p, key, value, encoded))

                decoded = p.read(encoded)
                self.assertEqual(
                    type(encoded), tuple,
                    '%r.read() should encode %r as a tuple, not %r' %
                    (p, encoded, decoded))
                self.assertEqual(
                    len(decoded), 2,
                    '%r.read() should encode %r as a tuple with two items,'
                    ' not %r' % (p, encoded, decoded))

                reencoded = p.write(*decoded)

                self.assertEqual(
                    encoded, reencoded,
                    '%r re-encodes %r as %r' % (p, encoded, reencoded))
