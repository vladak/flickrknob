import logging
from datetime import datetime

import exifread


def get_exif_date(file_path):
    """
    Read EXIF data from given file and return datetime.datetime object
    corresponding to the creation date of the photo.
    """

    logger = logging.getLogger(__name__)

    logger.debug("Getting EXIF tags for '{}'".format(file_path))

    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f, stop_tag='DateTimeOriginal')
        date_original = tags['EXIF DateTimeOriginal']
        if date_original:
            date_obj = datetime.strptime(str(date_original),
                                         '%Y:%m:%d %H:%M:%S')
            return date_obj

    return None


def is_known_suffix(file_name):
    file_name = file_name.lower()

    return file_name.endswith('.jpg')
