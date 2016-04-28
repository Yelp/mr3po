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


def decode_string(s, encoding=None):
    """Decode *s* into a unicode string, if it isn't alreaady.

    If *encoding* is ``None`` (the default), assume *s* is in UTF-8,
    and if it's not, fall back to latin-1.
    """
    if isinstance(s, unicode):
        return s

    if not encoding:
        try:
            return s.decode('utf_8')
        except:
            # this should always work
            return s.decode('latin_1')
    else:
        return s.decode(encoding)
