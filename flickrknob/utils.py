"""

helper functions

"""

import os
import sys
import logging


def parse_args(parser):
    """
    parse command line arguments. exits on error.
    """
    try:
        return parser.parse_args()
    except ValueError as exc:
        print(f"Argument parsing failed: {exc}", file=sys.stderr)
        sys.exit(1)


def check_env(flickr_key, flickr_secret):
    """
    check key and secret. If any is None, exit with 1.
    """
    if flickr_key is None:
        print("Missing Flickr key")
        sys.exit(1)
    if flickr_secret is None:
        print("Missing Flickr secret")
        sys.exit(1)


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
