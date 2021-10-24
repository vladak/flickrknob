#!/usr/bin/env python3

"""

This program deletes album along with all photos contained therein.

It is mean really just to aid debugging the flickrUploader.

"""

import argparse
import logging
import sys

import flickrapi
from alive_progress import alive_bar
from decouple import config

from .flickrknob import auth_check, delete_album, delete_photo, get_albums
from .logutil import LogLevelAction, get_package_logger
from .utils import check_env, confirm, parse_args

flickrKey = config("FLICKR_DELETE_KEY")
flickrSecret = config("FLICKR_DELETE_SECRET")


def get_album_id(flickr, album_name):
    """
    return ID for album name
    """

    logger = logging.getLogger(__name__)

    logger.info("Getting list of albums")
    albums = get_albums(flickr)
    if albums is None or len(albums.items()) == 0:
        logger.error("Empty list of albums")
        return None

    album_id = albums.get(album_name)
    if album_id is None:
        logger.error(f"Did not find album with name '{album_name}'")
        return None

    return album_id


def delete_album_with_photos():
    """
    command line tool to delete an album with all its photos
    """
    parser = argparse.ArgumentParser(
        description="delete Flickr album and " "all its photos"
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        action=LogLevelAction,
        help='Set log level (e.g. "ERROR")',
        default=logging.INFO,
    )
    parser.add_argument("name")

    args = parse_args(parser)

    logger = get_package_logger(args.loglevel)

    check_env(flickrKey, flickrSecret)

    logger.info("Checking authentication")
    flickr = flickrapi.FlickrAPI(flickrKey, flickrSecret)
    auth_check(flickr, perms="delete")

    album_id = get_album_id(flickr, args.name)
    if album_id is None:
        sys.exit(1)

    # Get list of photos in the album. (so that progress can be displayed)
    logger.info("Getting photo IDs")
    res = flickr.photosets.getPhotos(photoset_id=album_id)
    photoset_elem = res.find("photoset")
    logger.debug(f"photoset elem: {photoset_elem}")
    photo_ids = []
    for photo_elem in list(photoset_elem.iter("photo")):
        photo_id = photo_elem.attrib["id"]
        if photo_id:
            photo_ids.append(photo_id)
    logger.debug(f"Photo IDs: {photo_ids}")

    if not confirm(f"Delete album with {len(photo_ids)} photos ? Y/N "):
        sys.exit(0)

    logger.info(f"Deleting {len(photo_ids)} files")
    cnt = 0
    with alive_bar(len(photo_ids)) as bar:
        for photo_id in photo_ids:
            delete_photo(flickr, photo_id)
            # pylint: disable=E1102
            bar()
            cnt = cnt + 1

    logger.info(f"Deleted {cnt} files")

    # After the photos are deleted, the album might not be present anymore.
    album_id = get_album_id(flickr, args.name)
    if album_id is not None:
        delete_album(flickr, album_id)
