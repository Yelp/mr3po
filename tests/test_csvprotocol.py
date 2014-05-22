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

try:
    import unittest2 as unittest
    unittest  # quiet "redefinition of unused ..." warning from pyflakes
except ImportError:
    import unittest

from mr3po.csvprotocol import CsvProtocol
from mr3po.csvprotocol import CsvSingleQuotedProtocol

class CsvProtocolTestCase(unittest.TestCase):

    def test_read_one_line(self):
        p = CsvProtocol()
        line = "foo, bar, baz, 1, 2, 3.333\n"
        self.assertEqual(p.read(line), (None,[u'foo',u'bar',u'baz',u'1',u'2',u'3.333']))

    def test_drop_quotes(self):
        p = CsvProtocol()
        line = "\"foo\", \"bar\", \"baz\", 1, 2, 3.333"
        self.assertEqual(p.read(line), (None,[u'foo',u'bar',u'baz',u'1',u'2',u'3.333']))

    def test_alternate_quotes(self):
        p = CsvSingleQuotedProtocol()
        line = "'foo', 'bar', 'baz', 1, 2, 3.333"
        self.assertEqual(p.read(line), (None,[u'foo',u'bar',u'baz',u'1',u'2',u'3.333']))
    
    def test_read_unicode(self):
        p = CsvProtocol()
        line = '"Paul", "Erdős", "foo", 1, 2, 3.333'
        self.assertEqual(p.read(line), (None,[u'Paul',u'Erdős',u'foo',u'1',u'2',u'3.333']))
    
    def test_trailing_separator(self):
        p = CsvProtocol()
        line = '"foo", "bar", "baz", 1, 2, 3.333,'
        self.assertEqual(p.read(line), (None,[u'foo',u'bar',u'baz',u'1',u'2',u'3.333',u'']))

    def test_write_line(self):
        p = CsvProtocol()
        data = ['foo','bar','baz', 1, 2, 3.333]
        self.assertEqual(p.write(None,data), u"\"foo\",\"bar\",\"baz\",1,2,3.333")

    def test_format_strings(self):
        p = CsvProtocol()
        s1 = 'Benoit Mandelbrot'
        s2 = u'Paul Erdős'
        n1 = 101
        n2 = 2.718281
        self.assertEqual(p.fmt(s1), u'"Benoit Mandelbrot"')
        self.assertEqual(p.fmt(s2), u'"Paul Erdős"')
        self.assertEqual(p.fmt(n1), u'101')
        self.assertEqual(p.fmt(n2), u'2.718281')


