"""
argument parser utility functions
"""

import argparse
import logging

from .logutil import LogLevelAction


def get_base_parser():
    """
    return base parser with the log level argument and argument defaults formatter
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-l",
        "--loglevel",
        action=LogLevelAction,
        help='Set log level (e.g. "ERROR")',
        default=logging.INFO,
    )

    return parser
