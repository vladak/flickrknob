import os
import sys
import logging


def check_dir(name):
    """
    Check if name is directory. If not, exit the program with error code 1.
    """

    logger = logging.getLogger(__name__)

    if not os.path.isdir(name):
        logger.critical("{} is not a directory".format(name))
        sys.exit(1)
