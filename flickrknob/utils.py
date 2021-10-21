"""

helper functions

"""

import os
import sys
import logging


def create_trunc(file_path):
    """
    Make sure given file exists and has length of 0.
    """
    # pylint: disable=W1514
    with open(file_path, 'w+') as file_object:
        file_object.truncate()


def confirm(msg):
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input(msg).lower()
    return answer == "y"


def check_dir(name):
    """
    Check if name is directory. If not, exit the program with error code 1.
    """

    logger = logging.getLogger(__name__)

    logger.debug(f"Checking if '{name}' is directory")

    if not os.path.isdir(name):
        logger.critical(f"{name} is not a directory")
        sys.exit(1)
