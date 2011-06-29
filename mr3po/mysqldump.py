# Copyright 2011 Yelp
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
"""Parse INSERT statements from the output of mysqldump"""
import re

# Used http://dev.mysql.com/doc/refman/5.5/en/language-structure.html
# as my guide for parsing INSERT statements

_INSERT_RE = re.compile(r'(`(?P<identifier>.*?)`|'
                       r'(?P<null>NULL)|'
                       r"'(?P<string>(?:\\.|''|[^'])*?)'|"
                       r'(?P<number>[+-]?\d+\.?\d*(?:e[+-]?\d+)?))')

_STRING_ESCAPE_RE = re.compile(r'\\(.)')

# from http://dev.mysql.com/doc/refman/5.5/en/string-syntax.html
#
# MySQL string escape are almost the same as in Python, but there is
# no \f, and there's \Z for Windows EOF
_MYSQL_STRING_ESCAPES = {
    'r': '\r',
    'n': '\n',
    'b': '\b',
    't': '\t',
    '0': '\0',
    'Z': '\x1a',
}


def _string_escape_replacer(match):
    c = match.group(1)
    return _MYSQL_STRING_ESCAPES.get(c, c)


def unescape_string(s):
    return _STRING_ESCAPE_RE.sub(_string_escape_replacer, s)


def parse_number(x):
    try:
        return int(x)
    except ValueError:
        return float(x)


def parse_insert(sql, encoding=None):
    table, rows = parse_insert_many(sql)

    if table is None: # i.e. not an INSERT statement
        return None, None

    if len(rows) != 1:
        raise ValueError('bad INSERT, expected 1 row but got %d' % len(rows))

    return table, rows[0]


def parse_insert_many(sql, encoding=None):
    sql = _decode(sql, encoding)

    if not sql.startswith('INSERT'):
        return None, []

    identifiers = []
    values = []
    for m in _INSERT_RE.finditer(sql):
        if m.group('identifier'):
            identifiers.append(m.group('identifier'))
        elif m.group('null'):
            values.append(None)
        elif m.group('string'):
            values.append(unescape_string(m.group('string')))
        elif m.group('number'):
            values.append(parse_number(m.group('number')))
        else:
            assert False, 'should not be reached!'

    table, cols = identifiers[0], identifiers[1:]

    if not cols or not values or len(values) % len(cols) != 0:
        raise ValueError('bad INSERT, got %d cols and %d values: %r' % (
            len(cols), len(values), sql))

    # segment values, and turn them into row dictionaries
    return table, [dict(zip(cols, values[i:i+len(cols)]))
                   for i in xrange(0, len(values), len(cols))]


def _decode(s, encoding=None):
    """Decode *s* into a unicode string, if it isn't alreaady.

    If *encoding* is ``None`` (the default), assume *s* is in UTF-8,
    and if it's not, fall back to latin-1.
    """
    if isinstance(s, unicode):
        return s

    if not encoding:
        try:
            return s.decode('utf8')
        except:
            # this should always work
            return s.decode('latin1')
    else:
        return s.decode(encoding)
