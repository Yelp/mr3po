# -*- coding: utf-8 -*-
#
# Licensed under the Apache License,  Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,  software
# distributed under the License is distributed on an "AS IS" BASIS, 
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,  either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import unittest2 as unittest
    unittest  # quiet "redefinition of unused ..." warning from pyflakes
except ImportError:
    import unittest

from mr3px.csvprotocol import CsvProtocol
from mr3px.csvprotocol import CsvSingleQuotedProtocol


class CsvProtocolTestCase(unittest.TestCase):

    def test_read_one_line(self):
        p = CsvProtocol()
        line = "foo,  bar,  baz,  1,  2,  3.333\n"
        res = [u'foo', u'bar', u'baz', u'1', u'2', u'3.333']
        self.assertEqual(p.read(line), (None, res))

    def test_drop_quotes(self):
        p = CsvProtocol()
        line = "\"foo\",  \"bar\",  \"baz\",  1,  2,  3.333"
        res = [u'foo', u'bar', u'baz', u'1', u'2', u'3.333'] 
        self.assertEqual(p.read(line), (None, res))

    def test_alternate_quotes(self):
        p = CsvSingleQuotedProtocol()
        line = "'foo',  'bar',  'baz',  1,  2,  3.333"
        res = [u'foo', u'bar', u'baz', u'1', u'2', u'3.333']
        self.assertEqual(p.read(line), (None, res))
    
    def test_read_unicode(self):
        p = CsvProtocol()
        line = '"Paul",  "Erdős",  "foo",  1,  2,  3.333'
        res = [u'Paul', u'Erdős', u'foo', u'1', u'2', u'3.333']
        self.assertEqual(p.read(line), (None, res))
    
    def test_trailing_separator(self):
        p = CsvProtocol()
        line = '"foo",  "bar",  "baz",  1,  2,  3.333, '
        res = [u'foo', u'bar', u'baz', u'1', u'2', u'3.333', u'']
        self.assertEqual(p.read(line), (None, res))

    def test_write_line(self):
        p = CsvProtocol()
        data = ['foo', 'bar', 'baz',  1,  2,  3.333]
        res = u"\"foo\",\"bar\",\"baz\",1,2,3.333"
        self.assertEqual(p.write(None, data), res)

    def test_format_strings(self):
        p = CsvProtocol()
        io = [('Benoit Mandelbrot',  u'"Benoit Mandelbrot"'), 
              (u'Paul Erdős',  u'"Paul Erdős"'), 
              (101,  u'101'), 
              (2.718281,  u'2.718281')]
        for t in io:
            self.assertEqual(p.fmt(t[0]), t[1]) 


