#!/usr/bin/env python3

"""

This is primarily meant for uploging JPEG files however it should work
for any other format supported by Flickr.

"""

import os
import sys
from decouple import config
import logging
import argparse

import flickrapi
from alive_progress import alive_bar

from .flickrknob import upload_photo, auth_check, create_album, get_albums
from .photoutils import get_exif_date, is_known_suffix, EXIFerror
from .utils import check_dir
from .logutil import LogLevelAction

flickrKey = config('FLICKR_KEY')
flickrSecret = config('FLICKR_SECRET')


def uploader():
    parser = argparse.ArgumentParser(description='yet another Flickr uploader')
    parser.add_argument('-D', '--dedup', action='store_true', default=False,
                        help='deduplicate photos')
    parser.add_argument('-l', '--loglevel', action=LogLevelAction,
                        help='Set log level (e.g. \"ERROR\")',
                        default=logging.INFO)

    parser.add_argument('photoset')
    parser.add_argument('sourceDir')
    try:
        args = parser.parse_args()
    except ValueError as e:
        print("Argument parsing failed: {}".format(e), file=sys.stderr)
        sys.exit(1)

    logger = logging.getLogger(__package__)
    logger.setLevel(args.loglevel)
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    check_dir(args.sourceDir)

    if flickrKey is None:
        print("Missing Flickr key")
        sys.exit(1)
    if flickrSecret is None:
        print("Missing Flickr secret")
        sys.exit(1)

    logger.info("Checking authentication")
    flickr = flickrapi.FlickrAPI(flickrKey, flickrSecret)
    auth_check(flickr, perms='write')

    #
    # First check if album with same name exists. The create() API endpoint
    # will create new album with the same name even though the name is already
    # used so we want to avoid that. This check needs to be done first because
    # in order to create an album, there needs to be at least one photo
    # uploaded to be used as title photo.
    #
    logger.info("Checking album name")
    albums = get_albums(flickr)
    logger.debug("Albums: {}".format(albums))
    if albums is None or len(albums.items()) == 0:
        logger.error("Empty list of albums. Cannot check for dups.")
        sys.exit(1)

    album_names = albums.keys()

    if args.photoset in album_names:
        logger.error("Duplicate album name: '{}'".format(args.photoset))
        sys.exit(1)

    # Upload photos in the top level of the directory.
    dir_name = args.sourceDir
    logger.info("Getting list of files from '{}'".format(dir_name))
    dir_entries = [os.path.join(dir_name, f) for f in os.listdir(dir_name)
                   if os.path.isfile(os.path.join(dir_name, f))
                   and is_known_suffix(f)]

    # TODO: check what happens if file cannot be read or lacks EXIF data
    logger.info("Sorting files")
    try:
        dir_entries.sort(key=get_exif_date)
    except EXIFerror as e:
        logger.error(e)
        sys.exit(1)
    logger.debug("Sorted files: {}".format(dir_entries))

    logger.info("Uploading {} files".format(len(dir_entries)))
    photo_ids = {}
    primary_photo_id = None
    with alive_bar(len(dir_entries)) as bar:
        for file_path in dir_entries:
            # TODO: log the photo IDs to a file so that it is easier to
            #       recover if something fails during the process.
            file_name = os.path.basename(file_path)
            photo_id = upload_photo(flickr, file_path,
                                    title=file_name, dedup=args.dedup)
            photo_ids[file_name] = photo_id
            if primary_photo_id is None:
                primary_photo_id = photo_id
            bar()

    logger.info("Uploaded {} files".format(len(photo_ids)))

    album_id = create_album(flickr,
                            title=args.photoset,
                            primary_photo_id=primary_photo_id)
    if album_id is None:
        logger.error("Failed to create album '{}'".format(args.photoset))
        sys.exit(1)

    logger.info("Adding files to album '{}' ({})".
                format(args.photoset, album_id))
    with alive_bar(len(photo_ids.keys()) - 1) as bar:
        for name, photo_id in photo_ids.items():
            # Primary photo was automatically added to the album so skip it.
            if photo_id == primary_photo_id:
                continue

            logger.debug("Adding file '{}' ({}) to album {}".
                         format(name, photo_id, album_id))
            flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
            bar()
