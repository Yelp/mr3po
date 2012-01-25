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
"""Parse MySQL INSERT statements from the output of mysqldump.

We recommend using :py:class:`MySQLCompleteInsertProtocol`, which parses
one-row ```INSERT`` statements that include column names (this is the format
created when using :command:s3mysqldump with the :option:`--single-row`
option). There are also protocols to handle rows without column names and
multi-row ``INSERT`` statements.
"""
from decimal import Decimal
import re


__all__ = [
    'MySQLExtendedCompleteInsertProtocol',
    'MySQLCompleteInsertProtocol',
    'MySQLExtendedInsertProtocol',
    'MySQLInsertProtocol',
]

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

class AbstractMySQLInsertProtocol(object):

    def __init__(self, decimal=False, encoding=None, output_tab=False):
        self.decimal = decimal
        self.encoding = encoding
        self.output_tab = output_tab

    @property
    def complete(self):
        raise NotImplementedError

    @property
    def single_row(self):
        raise NotImplementedError

    def read(self, line):
        return parse_insert(
            line,
            complete=self.complete,
            decimal=self.decimal,
            encoding=self.encoding,
            single_row=self.single_row)

    def write(self, key, value):
        raise NotImplementedError


class MySQLCompleteInsertProtocol(AbstractMySQLInsertProtocol):
    complete = True
    single_row = True


class MySQLExtendedCompleteInsertProtocol(AbstractMySQLInsertProtocol):
    complete = True
    single_row = False


class MySQLInsertProtocol(AbstractMySQLInsertProtocol):
    complete = False
    single_row = True


class MySQLExtendedInsertProtocol(AbstractMySQLInsertProtocol):
    complete = False
    single_row = False


def parse_insert(
    sql, complete=False, decimal=False, encoding=None, single_row=None):

    sql = decode(sql, encoding)

    if not sql.startswith('INSERT'):
        raise ValueError('not an INSERT statement')

    identifiers = []
    rows = []
    current_row = []
    for m in INSERT_RE.finditer(sql):
        if m.group('identifier'):
            identifiers.append(m.group('identifier'))
        elif m.group('null'):
            current_row.append(None)
        elif m.group('string') is not None:  # parse empty strings!
            current_row.append(unescape_string(m.group('string')))
        elif m.group('hex'):
            current_row.append(m.group('hex').decode('hex'))
        elif m.group('number'):
            current_row.append(
                parse_number(m.group('number'), decimal=decimal))
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
            raise ValueError(
                'bad INSERT, row 0 has %d values, but row %d has %d values' %
                (row_len, i + 1, len(row)))

    if not identifiers:
        raise ValueError('bad INSERT, no identifiers')

    table, cols = identifiers[0], identifiers[1:]
    
    if cols and len(cols) != row_len:
        raise ValueError(
            'bad INSERT, %d column names but rows have %d values' %
            (len(cols), row_len))

    if complete:
        if cols:
            results = [dict(zip(cols, row)) for row in rows]
        else:
            raise ValueError('incomplete INSERT, no column names')
    else:
        results = rows

    if single_row:
        if len(results) == 1:
            return table, results[0]
        else:
            raise ValueError(
                'bad INSERT, expected 1 row but got %d' % len(results))
    else:
        return table, results


def string_escape_replacer(match):
    c = match.group(1)
    return MYSQL_STRING_ESCAPES.get(c, c)


def unescape_string(s):
    return STRING_ESCAPE_RE.sub(string_escape_replacer, s)


def parse_number(x, decimal=False):
    try:
        return int(x)
    except ValueError:
        if decimal:
            return Decimal(x)
        else:
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
