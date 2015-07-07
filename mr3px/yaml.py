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
"""Represent data in single-line YAML.

:py:class:`YAMLProtocol` can handle nearly any data type, and can serve as a
more readable alternative to :py:class:`~mrjob.protocol.PickleProtocol`.
As with pickle, you should be careful about reading untrusted data with this
protocol, because it can execute arbitrary code; also, this format is
Python-specific.

:py:class:`SafeYAMLProtocol` supports basic YAML data types, which are
a superset of JSON data types, and are supported across YAML implementations.

We also provide :py:class:`YAMLValueProtocol` and :py:class:`SafeYAMLProtocol`
to handle values without keys.
"""
from __future__ import absolute_import

import yaml

from mr3px.common import decode_string


__all__ = [
    'SafeYAMLProtocol',
    'SafeYAMLValueProtocol',
    'YAMLProtocol',
    'YAMLValueProtocol',
]


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
        default_flow_style='block',
        explicit_end=False,
        explicit_start=False,
        line_break='\n',
        width=float('inf')).rstrip()

    if out.endswith(u'\n...'):
        out = out[:-3].rstrip()

    return out.encode(encoding)


class YAMLProtocolBase(object):

    safe = True

    def __init__(self, allow_unicode=False, encoding=None):
        """Optional parameters:

        :param allow_unicode: Allow non-ASCII characters in the output
                              (e.g. accented characters).
        :param encoding: Character encoding to use. We default to UTF-8,
                         with fallback to latin-1 when decoding input.
        """
        self.allow_unicode = allow_unicode
        self.encoding = encoding

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


class SafeYAMLProtocol(YAMLProtocolBase):
    """Encode/decode keys and values that can be represented using
    YAML tags. This is a superset of JSON, and includes most basic data
    structures; for a full list see
    http://pyyaml.org/wiki/PyYAMLDocumentation#YAMLtagsandPythontypes.

    Note that this will encode tuples as lists.
    """
    def read(self, line):
        key_str, value_str = line.split('\t')

        # cache last key
        if key_str != getattr(self, '_key_cache', [None])[0]:
            self._key_cache = (key_str, self.load(key_str))

        key = self._key_cache[1]

        return key, self.load(value_str)

    def write(self, key, value):
        return '%s\t%s' % (self.dump(key), self.dump(value))


class YAMLProtocol(SafeYAMLProtocol):
    """Encode/decode keys and values of virtually any type using YAML.
    """
    safe = False


class SafeYAMLValueProtocol(YAMLProtocolBase):
    """Encode/decode keys and values that can be represented using
    YAML tags. This is a superset of JSON, and includes most basic data
    structures; for a full list see
    http://pyyaml.org/wiki/PyYAMLDocumentation#YAMLtagsandPythontypes.

    Note that this will encode tuples as lists.
    """
    def read(self, line):
        return None, self.load(line)

    def write(self, _, value):
        return self.dump(value)


class YAMLValueProtocol(SafeYAMLValueProtocol):
    """Encode/decode values of virtually any type using YAML.
    """
    safe = False
