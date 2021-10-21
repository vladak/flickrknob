import logging
from datetime import datetime

import exifread


"""
Utility functions for working with photo files.
"""


class EXIFerror(Exception):
    def __init__(self, msg):
        super().__init__(self, msg)


def get_exif_date(file_path):
    """
    Read EXIF data from given file and return datetime.datetime object
    corresponding to the creation date of the photo.
    """

    logger = logging.getLogger(__name__)

    logger.debug("Getting EXIF tags for '{}'".format(file_path))

    tag_name = 'DateTimeOriginal'
    try:
        with open(file_path, 'rb') as fobj:
            tags = exifread.process_file(fobj, stop_tag=tag_name)
            try:
                date_original = tags['EXIF ' + tag_name]
            except KeyError:
                raise EXIFerror("File '{}' lacks EXIF {} tag".
                                format(file_path, tag_name))

            if date_original:
                try:
                    date_obj = datetime.strptime(str(date_original),
                                                 '%Y:%m:%d %H:%M:%S')
                    return date_obj
                except ValueError:
                    raise EXIFerror("{} tag not correctly formed for '{}'".
                                    format(tag_name, file_path))
    except PermissionError as e:
        raise EXIFerror("Permisson problem for '{}': {}".
                        format(file_path, e))

    raise EXIFerror("cannot find {} in '{}'".
                    format(tag_name, file_path))


def is_known_suffix(file_name):
    file_name = file_name.lower()
    dot_index = file_name.rindex('.')
    extension = file_name[dot_index+1:]

    return extension in ['jpg', 'jpeg', 'mov', 'mp4']
