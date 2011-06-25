"""Parse INSERT statements from the output of mysqldump"""
import re

INSERT_RE = re.compile(r'(`(?P<identifier>.*?)`|'
                       r'(?P<null>NULL)|'
                       r"'(?P<string>(?:\\.|''|[^'])*?)'|"
                       r'(?P<number>[+-]?\d+\.?\d*(?:e[+-]?\d+)?))')


def unescape_string(s):
    # TODO: implement this
    return s


def parse_number(x):
    try:
        return int(x)
    except ValueError:
        return float(x)


def parse_insert_row(sql):
    if not sql.startswith('INSERT'):
        raise ValueError('not an insert statement: %r' % (sql,))

    identifiers = []
    values = []
    for m in INSERT_RE.finditer(sql):
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

    if len(cols) != len(values):
        raise ValueError('bad statement, got %d cols and %d values' % (
            len(cols), len(values)))

    return table, dict(zip(cols, values))
