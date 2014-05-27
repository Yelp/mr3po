# -*- coding: utf-8 -*-
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

from mr3po.keyedjson import KeyedJsonProtocol
from tests.roundtrip import RoundTripTestCase

class KeyedJsonProtocolRoundTripTestCase(RoundTripTestCase):
    PROTOCOLS = [
            KeyedJsonProtocol()
            ]
    ROUND_TRIP_KEY_VALUES = [
            ("foo",{'foo':123,'bar':456}),
            ("123", [1,2,3,4,5]),
            ]

class KeyedJsonProtocolTestCase(unittest.TestCase):

    def test_read_line_dict(self):
        p = KeyedJsonProtocol()
        line = '54321\t{"foo":123,"bar":456,"baz":"oh noes!"}'
        expected = ("54321",{'foo':123,'bar':456,'baz':'oh noes!'})
        self.assertEqual(p.read(line),expected)

    def test_read_line_list(self):
        p = KeyedJsonProtocol()
        line = '54321\t["foo","bar",456, 789]'
        expected = ("54321",['foo','bar',456,789])
        self.assertEqual(p.read(line),expected)

    def test_write_line_dict(self):
        p = KeyedJsonProtocol()
        key = "54321"
        val = {'foo':123,'bar':456,'baz':'oh noes!'}
        expected = '54321\t{"baz": "oh noes!", "foo": 123, "bar": 456}'
        # TODO _ order of dictionary not guaranteed.
        # test this with a regex?
        self.assertEqual(p.write(key,val),expected)

    def test_write_line_list(self):
        p = KeyedJsonProtocol()
        key = "54321"
        val = ['foo','bar',456,789]
        expected = '54321\t["foo", "bar", 456, 789]'
        self.assertEqual(p.write(key,val),expected)

    def test_write_line_tuple(self):
        p = KeyedJsonProtocol()
        key = "54321"
        val = ('foo','bar',456,789)
        expected = '54321\t["foo", "bar", 456, 789]'
        self.assertEqual(p.write(key,val),expected)

    def test_read_unkeyed_data_raises_exception(self):
        p = KeyedJsonProtocol()
        self.assertRaises(ValueError, p.read, "foo")

    def test_read_invalid_data_raises_exception(self):
        p = KeyedJsonProtocol()
        self.assertRaises(ValueError, p.read, "foo\nbar")

    def test_write_invalid_data_raises_exception(self):
        p = KeyedJsonProtocol()
        self.assertRaises(ValueError, p.write, "123", "foo")


