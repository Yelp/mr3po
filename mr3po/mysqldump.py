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
"""Parse INSERT statements from the output of mysqldump.

This is a very very basic parser; it doesn't handle insert statements or SQL
in general; just the output of mysqldump.
"""
import re




__all__ = ['parse_insert', 'parse_insert_many']

# Used http://dev.mysql.com/doc/refman/5.5/en/language-structure.html
# as my guide for parsing INSERT statements

INSERT_RE = re.compile(r'(`(?P<identifier>.*?)`|'
                       r'(?P<null>NULL)|'
                       r"'(?P<string>(?:\\.|''|[^'])*?)'|"
                       r'0x(?P<hex>[0-9a0-f]+)|'
                       r'(?P<number>[+-]?\d+\.?\d*(?:e[+-]?\d+)?)|'
                       r'(?P<close_paren>\)))')

STRING_ESCAPE_RE = re.compile(r'\\(.)')

# from http://dev.mysql.com/doc/refman/5.5/en/string-syntax.html
#
# MySQL string escape are almost the same as in Python, but there is
# no \f, and there's \Z for Windows EOF
MYSQL_STRING_ESCAPES = {
    'r': '\r',
    'n': '\n',
    'b': '\b',
    't': '\t',
    '0': '\0',
    'Z': '\x1a',
}


def parse_insert(sql, encoding=None):
    table, rows = parse_insert_many(sql)

    if len(rows) != 1:
        raise ValueError('bad INSERT, expected 1 row but got %d' % len(rows))

    return table, rows[0]


def parse_insert_many(sql, encoding=None):
    sql = decode(sql, encoding)

    identifiers = []
    rows = []
    current_row = []
    for m in INSERT_RE.finditer(sql):
        if m.group('identifier'):
            identifiers.append(m.group('identifier'))
        elif m.group('null'):
            current_row.append(None)
        elif m.group('string') is not None:
            current_row.append(unescape_string(m.group('string')))
        elif m.group('hex'):
            current_row.append(m.group('hex').decode('hex'))
        elif m.group('number'):
            current_row.append(parse_number(m.group('number')))
        elif m.group('close_paren'):
            # woot, I'm a parser
            if current_row:
                rows.append(current_row)
                current_row = []
        else:
            assert False, 'should not be reached!'

    if current_row:
        raise ValueError('bad INSERT, missing close paren')

    if not rows:
        raise ValueError('bad INSERT, no values')

    row_len = len(rows[0])
    for i, row in enumerate(rows[1:]):
        if len(row) != row_len:
            raise ValueError('bad INSERT, row 0 has %d values, but row %d has %d values' % (row_len, i+1, len(row)))

    if not identifiers:
        raise ValueError('bad INSERT, no identifiers')

    table, cols = identifiers[0], identifiers[1:]

    # no column names, return rows as lists
    if not cols:
        return table, rows

    if not len(cols) == row_len:
         raise ValueError('bad INSERT, %d column names but rows have %d values' % (len(cols), row_len))

    return table, [dict(zip(cols, row)) for row in rows]


def string_escape_replacer(match):
    c = match.group(1)
    return MYSQL_STRING_ESCAPES.get(c, c)


def unescape_string(s):
    return STRING_ESCAPE_RE.sub(string_escape_replacer, s)


def parse_number(x):
    try:
        return int(x)
    except ValueError:
        return float(x)


def decode(s, encoding=None):
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
