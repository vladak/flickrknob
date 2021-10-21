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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from flickrapi import FlickrAPI, FlickrError
from alive_progress import alive_bar

from .flickrknob import upload_photo, auth_check, create_album, get_albums
from .photoutils import get_exif_date, is_known_suffix, EXIFerror
from .utils import check_dir
from .logutil import LogLevelAction, get_file_logger

flickrKey = config('FLICKR_KEY')
flickrSecret = config('FLICKR_SECRET')


def upload_single_photo(file_path, bar, file_logger, flickr, dedup):

    file_name = os.path.basename(file_path)
    photo_id = upload_photo(flickr, file_path,
                            title=file_name, dedup=dedup)

    bar()
    file_logger.info("Uploaded '{}':{}".format(file_path, photo_id))

    return (file_name, photo_id)


def add_photo_to_album(file_name, bar, flickr, photo_id, album_id):

    logger = logging.getLogger(__name__)

    logger.debug("Adding file '{}' ({}) to album {}".
                 format(file_name, photo_id, album_id))
    flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
    bar()


def uploader():
    parser = argparse.ArgumentParser(description='yet another Flickr uploader',
                                     formatter_class=argparse.
                                     ArgumentDefaultsHelpFormatter)
    parser.add_argument('-D', '--dedup', action='store_true', default=False,
                        help='deduplicate photos')
    parser.add_argument('-l', '--loglevel', action=LogLevelAction,
                        help='Set log level (e.g. \"ERROR\")',
                        default=logging.INFO)
    parser.add_argument('--logfile',
                        help='Log file to record uploaded files',
                        default='files-{album_name}.log')
    parser.add_argument('--threads',
                        help='Number of threads to create',
                        default=4)

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
    flickr = FlickrAPI(flickrKey, flickrSecret)
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

    # Upload files in the top level of the directory.
    dir_name = args.sourceDir
    logger.info("Getting list of files from '{}'".format(dir_name))
    dir_entries = [os.path.join(dir_name, f) for f in os.listdir(dir_name)
                   if os.path.isfile(os.path.join(dir_name, f))
                   and is_known_suffix(f)]

    # This serves also as prevention for file related problems in the upload
    # phase (except this is still a TOCTOU problem).
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
    #
    # Log the photo IDs to a file so that it is easier to recover if something
    # fails during the process.
    #
    logfile = args.logfile.format(album_name=args.photoset)
    file_logger = get_file_logger(logfile, __name__)
    numworkers = args.threads
    with alive_bar(len(dir_entries)) as bar:
        with ThreadPoolExecutor(max_workers=numworkers) as executor:
            futures = []
            for i, file_path in enumerate(dir_entries):
                # Simulate pipeline start for better bandwidth utilization.
                # Assumes the threads will start running immediately.
                if i < numworkers:
                    time.sleep(i * 0.5)
                futures.append(
                    executor.submit(upload_single_photo, file_path,
                                    bar, file_logger, flickr, args.dedup)
                )
            for future in as_completed(futures):
                try:
                    file_name, photo_id = future.result()
                    photo_ids[file_name] = photo_id
                    if primary_photo_id is None:
                        primary_photo_id = photo_id
                except FlickrError as e:
                    logger.error(e)  # TODO shutdown () ?

    logger.info("Uploaded {} files".format(len(photo_ids)))
    logger.debug(f"File to IDs: {photo_ids}")

    album_id = create_album(flickr,
                            title=args.photoset,
                            primary_photo_id=primary_photo_id)
    if album_id is None:
        logger.error(f"Failed to create album '{args.photoset}'")
        sys.exit(1)

    logger.info(f"Adding files to album '{args.photoset}' ({album_id})")
    with alive_bar(len(photo_ids.keys()) - 1) as bar:
        with ThreadPoolExecutor(max_workers=numworkers) as executor:
            futures = []
            for name, photo_id in photo_ids.items():
                # Primary photo was automatically added to the album,
                # so skip it.
                if photo_id == primary_photo_id:
                    continue

                futures.append(
                    executor.submit(add_photo_to_album, name, bar,
                                    flickr, photo_id, album_id)
                )

            for future in as_completed(futures):
                try:
                    future.result()
                except FlickrError as e:
                    logger.error(e)  # TODO shutdown () ?

    # The files need to be reordered since they were uploaded in parallel.
    logger.info("Sorting files in the album")
    dir_file_names = list(map(os.path.basename, dir_entries))
    photo_ids_sorted = list(map(photo_ids.get, dir_file_names))
    logger.debug(f"Sorted photo IDs: {photo_ids_sorted}")
    flickr.photosets.reorderPhotos(photoset_id=album_id,
                                   photo_ids=",".join(photo_ids_sorted))
