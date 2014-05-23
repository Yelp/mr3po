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
"""Read and write values in csv format. 

Primarily useful for reading from raw input files. 
Can also output csv if that is your kind of thing.

Definitely NOT recommended for use as an internal protocol. 
"""

import csv
import types
import StringIO
from common import decode_string

class CsvProtocol(object):

    QUOTE_CHAR = '"'
    QUOTABLE_TYPES = [types.StringType,types.StringTypes,types.UnicodeType]

    def read(self, line):
        """read a line of csv data and output a list of values
        converts to unicode using common.decode_string
        """
        l = csv.reader(StringIO.StringIO(line), 
                quotechar=self.QUOTE_CHAR, 
                skipinitialspace=True)
        for r in l:
            data = [decode_string(f).strip() for f in r]
            break
        return (None, data)

    def write(self, _, data):
        """Output a list of values as a comma-separated string
        """
        out = [self.fmt(d) for d in data]
        return ",".join(out)

    def fmt(self,val):
        """Format the values for common CSV output 
        """
        if type(val) in self.QUOTABLE_TYPES:
            s = decode_string(val)
            return u"{0}{1}{2}".format(self.QUOTE_CHAR, s, self.QUOTE_CHAR)
        else:
            return decode_string(str(val))

class CsvSingleQuotedProtocol(CsvProtocol):
    QUOTE_CHAR = "'"

