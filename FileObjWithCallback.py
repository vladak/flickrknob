"""

wrapper over file object to provide read operation callback
from https://www.flickr.com/groups/api/discuss/72157714857761072/

use like this:

  XXX

"""

import os
import logging


class FileObjWithCallback(object):
    def __init__(self, fileobj, callback, callback_arg):
        self._f = fileobj
        self._callback = callback
        self._callback_arg = callback_arg
        # requests library uses 'len' attribute instead of seeking to
        # end of file and back
        self.len = os.fstat(self._f.fileno()).st_size

    # substitute read method
    def read(self, size=-1):
        if self._callback:
            self._callback(self._callback_arg,
                           self._f.tell() * 100 // self.len)

        logger = logging.getLogger(__name__)
        logger.debug("Calling read with size {}".format(size))
        return self._f.read(size)

    # delegate all other attributes to file object
    def __getattr__(self, name):
        return getattr(self._f, name)
