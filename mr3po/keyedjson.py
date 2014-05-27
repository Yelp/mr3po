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
""" Read and write data using the Hadoop key<tab>value structure.

The key can be anything (will be a string in the output),
the value is a dictionary or list(or tuple) represented 
as a string which can be converted by the json module

Useful as an internal protocol when you need the key ordering 
of the Hadoop system and a structured data value.
"""
import json
import types
from common import decode_string

class KeyedJsonProtocol(object):

    READ_WRITE_TYPES = (types.DictType, types.ListType, types.TupleType)

    def read(self, line):
        """Parse a line of text input and return a tuple with 
        the key(str) and value(list|dict)
        """
        k, v = line.split('\t', 1)
        k_str = decode_string(k)
        v_obj = json.loads(decode_string(v)) 
        if type(v_obj) not in self.READ_WRITE_TYPES:
            raise ValueError("Value is not an acceptable type")
        return (k_str, v_obj)

    def write(self, key, value):
        """Write the key(str) and value(list|dict|tuple) 
        as a line of text separated by a tab
        NOTE: tuples will create json lists/arrays
        """
        if type(value) not in self.READ_WRITE_TYPES:
            raise ValueError("Value is not an acceptable type")
        return '{0}\t{1}'.format(key, json.dumps(value))
