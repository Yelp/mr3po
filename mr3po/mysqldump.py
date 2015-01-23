# Copyright 2011-2012 Yelp
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
import itertools
from decimal import Decimal
import re

from mr3po.common import decode_string

__all__ = [
    'MySQLExtendedCompleteInsertProtocol',
    'MySQLCompleteInsertProtocol',
    'MySQLExtendedInsertProtocol',
    'MySQLInsertProtocol',
]

# Used http://dev.mysql.com/doc/refman/5.5/en/language-structure.html
# as my guide for parsing INSERT statements

IDENTIFIER_RE = re.compile(
    r'`(?P<identifier>.*?)`'
)

INSERT_RE = re.compile(r'((?P<null>NULL)|'
                       r"'(?P<string>(?:\\.|''|[^'\\]+)*?)'|"
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

MYSQL_STRING_ESCAPES_FOR_TRANSLATE = dict(
    (ord(c), u'\\%s' % esc) for esc, c in MYSQL_STRING_ESCAPES.iteritems())


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
        return dump_as_insert(
            key, value,
            complete=self.complete,
            encoding=self.encoding,
            output_tab=self.output_tab,
            single_row=self.single_row)

    def __repr__(self):
        return '%s(decimal=%r, encoding=%r, output_tab=%r)' % (
            self.__class__.__name__,
            self.decimal, self.encoding, self.output_tab)


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


# NOTE: Follow "dot free" methodology, cf.
# https://wiki.python.org/moin/PythonSpeed/PerformanceTips
_group = next(INSERT_RE.finditer(u"'hi'")).__class__.group


def parse_value(m, decimal):
    if _group(m, 'null'):
        return None

    str_value = _group(m, 'string')
    if str_value is not None:  # parse empty strings!
        return unescape_string(str_value)

    number_value = _group(m, 'number')
    if number_value:
        return parse_number(number_value, decimal=decimal)

    hex_value = _group(m, 'hex')
    if hex_value:
        return hex_value.decode('hex')

    raise ValueError("Bad match {0!r}".format(m.groupdict()))


def parse_values_sql(values_sql, decimal):
    current_row = []
    for m in INSERT_RE.finditer(values_sql):
        if _group(m, 'close_paren') is not None:
            yield current_row
            current_row = []
        else:
            current_row.append(parse_value(m, decimal))
    assert not current_row


_table_name_and_columns_cache = {}
def parse_table_name_and_cols(identifiers_sql):
    try:
        return _table_name_and_columns_cache[identifiers_sql]
    except KeyError:
        # Clear the cache occasionally
        if len(_table_name_and_columns_cache) > 100:
            _table_name_and_columns_cache.clear()

        # The actual regex search
        identifiers = tuple(
            _group(m, 'identifier')
            for m in IDENTIFIER_RE.finditer(identifiers_sql)
        )

        # Do some checks here, no need to do them for cached values
        if not identifiers:
            raise ValueError('bad INSERT, no identifiers')
        elif len(identifiers) <= 1:
            raise ValueError("bad INSERT, couldn't find columns")

        # split to table name and columns
        table_name, columns = identifiers[0], identifiers[1:]
        _table_name_and_columns_cache[identifiers_sql] = table_name, columns
        return table_name, columns


def make_row_dict(cols, row):
    if len(row) != len(cols):
        raise ValueError(
            "Wrong number of columns ({0}) in row, expected {1}"
            .format(len(row), len(cols))
        )
    return dict(zip(cols, row))


def do_all_parsing(sql, decimal, complete):
    name_and_cols_sql, values_sql = sql.split(" VALUES ", 1)

    table_name, cols = parse_table_name_and_cols(name_and_cols_sql)
    results = [
        (make_row_dict(cols, row) if complete else row)
        for row in parse_values_sql(values_sql, decimal)
    ]

    if not results:
        raise ValueError('bad INSERT, no values')

    return table_name, results


def parse_insert(sql, complete=False, decimal=False, encoding=None,
                 single_row=False):

    sql = decode_string(sql, encoding)

    if not sql.startswith('INSERT'):
        raise ValueError('not an INSERT statement')

    table, results = do_all_parsing(sql, decimal=decimal, complete=complete)
    return (
        (table, results[0])
        if single_row
        else (table, results)
    )


def dump_as_insert(table, data, complete=False, encoding=None,
                   output_tab=False, single_row=False):
    if not table or not isinstance(table, basestring):
        raise ValueError('Bad table name')

    if not data:
        raise ValueError('No data to insert')

    if single_row:
        data = [data]

    cols = None

    if complete:
        rows = []
        for row_num, row_data in enumerate(data):
            row_cols, row = zip(*sorted(row_data.iteritems()))
            if cols is None:
                cols = row_cols
            elif cols != row_cols:
                raise ValueError(
                    'row 0 has columns %r, but row %d has columns %r'
                    % (cols, row_num, row_cols))

            rows.append(row)
    else:
        num_cols = len(data[0])
        for i, row_data in enumerate(data[1:]):
            if len(row_data) != num_cols:
                raise ValueError(
                    'row 0 has %d items, but row %d has %d items' %
                    (num_cols, i + 1, len(row_data)))

        rows = data

    sql = 'INSERT INTO %s%s%s VALUES %s;' % (
        format_identifier(table),
        '\t' if output_tab else '',
        (' ' + format_cols(cols)) if cols else '',
        ', '.join(format_row(row) for row in rows))

    return sql.encode(encoding or 'utf_8')


def format_identifier(identifier):
    # TODO: add encoding, escaping
    return '`%s`' % identifier


def format_cols(cols):
    return '(%s)' % ','.join(format_identifier(col) for col in cols)


def format_row(items):
    return '(%s)' % ','.join(format_value(x) for x in items)


def format_value(x):
    if x is None:
        return 'NULL'
    elif isinstance(x, (int, long, float, Decimal)):
        return str(x)
    elif isinstance(x, unicode):
        return "'%s'" % escape_unicode_string(x)
    elif isinstance(x, str):
        return '0x%s' % x.encode('hex').upper()
    else:
        raise TypeError("can't encode values of type %s" %
                        x.__class__.__name__)


def string_escape_replacer(match):
    c = match.group(1)
    return MYSQL_STRING_ESCAPES.get(c, c)


def unescape_string(s):
    return STRING_ESCAPE_RE.sub(string_escape_replacer, s)


def escape_unicode_string(u):
    if not isinstance(u, unicode):
        raise TypeError
    # TODO: translate() was pretty slow last I checked; maybe try regex?
    return u.translate(MYSQL_STRING_ESCAPES_FOR_TRANSLATE)


def parse_number(x, decimal=False):
    try:
        return int(x)
    except ValueError:
        if decimal:
            return Decimal(x)
        else:
            return float(x)
