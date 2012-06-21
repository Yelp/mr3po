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
"""Encode keys and values in single-line YAML. Which is a lot like JSON
without so many quotes."""
from __future__ import absolute_import

import yaml

from mr3po.common import decode_string


__all__ = ['YAMLProtocol', 'YAMLValueProtocol']


def dump_inline(data, allow_unicode=None, encoding=None, safe=False):
    """Dump YAML on a single line.

    :param allow_unicode: Don't escape non-ASCII characters in the result.
    :param encoding: Optional character encoding to use. If not set,
                     return unicode
    :param safe: if True, use :py:func:`yaml.safe_dump`; that is, only encode
                 basic value types; otherwise use :py:func:`yaml.dump`
    :param kwargs: additional keyword arguments to pass through to
                   :py:func:`yaml.dump`. Only *allow_unicode* and
                   *encoding* seem to be useful.
    """
    dump = yaml.safe_dump if safe else yaml.dump

    out = dump(
        data,
        allow_unicode=allow_unicode,
        canonical=None,
        default_flow_style='block',
        encoding=None,
        explicit_end=False,
        explicit_start=False,
        indent=None,
        line_break='\n',
        tags=None,
        version=None,
        width=float('inf')).rstrip()

    if out.endswith(u'\n...'):
        out = out[:-3].rstrip()

    return out.encode(encoding)


class YAMLProtocolBase(object):

    def __init__(self, allow_unicode=False, encoding=None, safe=False):
        self.allow_unicode = allow_unicode
        self.encoding = encoding
        self.safe = safe

    def load(self, data):
        unicode_data = decode_string(data, encoding=self.encoding)

        if self.safe:
            return yaml.safe_load(unicode_data)
        else:
            return yaml.load(unicode_data)

    def dump(self, data):
        return dump_inline(
            data,
            allow_unicode=self.allow_unicode,
            encoding=self.encoding or 'utf_8',  # never return Unicode
            safe=self.safe)


class YAMLProtocol(YAMLProtocolBase):

    def __init__(self, *args, **kwargs):
        super(YAMLProtocol, self).__init__(*args, **kwargs)

        # a tuple containing the last encoded key seen, and the decoded key
        self._key_cache = (None, None)

    def read(self, line):
        key_str, value_str = line.split('\t')

        # cache last key
        if key_str != self._key_cache[0]:
            self._key_cache = (key_str, self.load(key_str))

        key = self._key_cache[1]

        return key, self.load(value_str)

    def write(self, key, value):
        return '%s\t%s' % (self.dump(key), self.dump(value))


class YAMLValueProtocol(YAMLProtocolBase):

    def read(self, line):
        return None, self.load(line)

    def write(self, _, value):
        return self.dump(value)
