"""

Utility functions for working with photo files.

"""

import logging
from datetime import datetime

import exifread


class EXIFerror(Exception):
    """
    exception class to report problems with EXIF processing
    """

    def __init__(self, msg):
        super().__init__(self, msg)


def get_exif_date(file_path):
    """
    Read EXIF data from given file and return datetime.datetime object
    corresponding to the creation date of the photo.
    """

    logger = logging.getLogger(__name__)

    logger.debug(f"Getting EXIF tags for '{file_path}'")

    tag_name = "DateTimeOriginal"
    try:
        with open(file_path, "rb") as fobj:
            tags = exifread.process_file(fobj, stop_tag=tag_name)
            try:
                date_original = tags["EXIF " + tag_name]
            except KeyError:
                # pylint: disable=W0707
                raise EXIFerror(f"File '{file_path}' lacks EXIF " "{tag_name} tag")

            if date_original:
                try:
                    date_obj = datetime.strptime(
                        str(date_original), "%Y:%m:%d %H:%M:%S"
                    )
                    return date_obj
                except ValueError:
                    # pylint: disable=W0707
                    raise EXIFerror(
                        f"{tag_name} tag not correctly formed " "for '{file_path}'"
                    )
    except PermissionError as exc:
        # pylint: disable=W0707
        raise EXIFerror(f"Permission problem for '{file_path}': {exc}")

    raise EXIFerror(f"cannot find {tag_name} in '{file_path}'")


def is_known_suffix(file_name):
    """
    return whether given file name ends with hard-coded suffix
    (case insensitive)
    """
    file_name = file_name.lower()
    dot_index = file_name.rindex(".")
    strip_index = dot_index + 1
    extension = file_name[strip_index:]

    return extension in ["jpg", "jpeg", "mov", "mp4"]
