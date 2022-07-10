#!/usr/bin/env python3

"""

This is primarily meant for uploading JPEG files however it should work
for any other format supported by Flickr.

"""

import argparse
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from alive_progress import alive_bar
from decouple import config

from flickrapi import FlickrAPI, FlickrError

from .flickrknob import auth_check, create_album, get_albums, upload_photo
from .logutil import get_file_logger, get_package_logger
from .parserutil import get_base_parser
from .photoutils import get_date, is_known_suffix
from .utils import check_dir, check_env, parse_args

flickrKey = config("FLICKR_KEY")
flickrSecret = config("FLICKR_SECRET")


# pylint: disable=R0913
def upload_single_photo(file_path, bar, file_logger, flickr, dedup, retries):
    """
    worker function to upload a photo and report progress
    """

    file_name = os.path.basename(file_path)
    photo_id = upload_photo(
        flickr, file_path, title=file_name, dedup=dedup, retries=retries
    )

    bar()
    file_logger.info(f"Uploaded '{file_path}':{photo_id}")

    return file_name, photo_id


def add_photo_to_album(bar, file_logger, flickr, photo_id, album_id):
    """
    worker function to add photo to album and report progress
    """

    logger = logging.getLogger(__name__)

    logger.debug(f"Adding file {photo_id} to album {album_id}")
    flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
    bar()
    file_logger.info(f"Added {photo_id} to album {album_id}")


def get_args():
    """
    return parsed arguments from command line
    """
    parser = argparse.ArgumentParser(
        add_help=False,
        description="yet another Flickr uploader",
        parents=[get_base_parser()],
    )
    parser.add_argument(
        "-D", "--dedup", action="store_true", default=False, help="deduplicate photos"
    )
    parser.add_argument(
        "--logfile",
        help="Log file to record uploaded files",
        default="files-{album_name}.log",
    )
    parser.add_argument(
        "--retries",
        help="Number of retries when single file upload fails",
        type=int,
        default=3,
    )
    parser.add_argument("--threads", help="Number of threads to create", default=4)
    parser.add_argument("photoset")
    parser.add_argument("sourceDir")
    args = parse_args(parser)
    return args


def check_album_name(album_name, flickr):
    """
    Check if album name already exists. If it does, exit the program.
    """
    logger = logging.getLogger(__name__)

    logger.info("Checking album name")
    albums = get_albums(flickr)
    logger.debug(f"Albums: {albums}")
    if albums is None or len(albums.items()) == 0:
        logger.error("Empty list of albums. Cannot check for dups.")
        sys.exit(1)
    album_names = albums.keys()
    if album_name in album_names:
        logger.error(f"Duplicate album name: '{album_name}'")
        sys.exit(1)


# pylint: disable=R0914,R0913
def upload_files(dir_entries, file_logger, flickr, numworkers, dedup, retries):
    """
    upload files to Flickr
    """
    logger = logging.getLogger(__name__)

    logger.info(f"Uploading {len(dir_entries)} files")
    photo_ids = {}
    primary_photo_id = None
    with alive_bar(len(dir_entries)) as bar:
        with ThreadPoolExecutor(max_workers=numworkers) as executor:
            futures = []
            for i, file_path in enumerate(dir_entries):
                # Simulate pipeline start for better bandwidth utilization.
                # Assumes the threads will start running immediately.
                if i < numworkers:
                    time.sleep(i * 0.5)
                futures.append(
                    executor.submit(
                        upload_single_photo,
                        file_path,
                        bar,
                        file_logger,
                        flickr,
                        dedup,
                        retries,
                    )
                )
            for future in as_completed(futures):
                try:
                    file_name, photo_id = future.result()
                    photo_ids[file_name] = photo_id
                    if primary_photo_id is None:
                        primary_photo_id = photo_id
                except FlickrError as exc:
                    logger.error(exc)

    logger.info(f"Uploaded {len(photo_ids)} files")
    logger.debug(f"File to IDs: {photo_ids}")

    return photo_ids, primary_photo_id


# pylint: disable=R0913
def add_files_to_album(
    album_id, file_logger, flickr, numworkers, photo_ids, primary_photo_id
):
    """
    add files to album
    """
    logger = logging.getLogger(__name__)

    logger.info(f"Adding files to album {album_id}")
    with alive_bar(len(photo_ids.keys()) - 1) as bar:
        with ThreadPoolExecutor(max_workers=numworkers) as executor:
            futures = []
            for photo_id in photo_ids.values():
                # Primary photo was automatically added to the album,
                # so skip it.
                if photo_id == primary_photo_id:
                    continue

                futures.append(
                    executor.submit(
                        add_photo_to_album, bar, file_logger, flickr, photo_id, album_id
                    )
                )

            for future in as_completed(futures):
                try:
                    future.result()
                except FlickrError as exc:
                    logger.error(exc)


def reorder_files(album_id, dir_entries, flickr, photo_ids):
    """
    reorder files in the album
    """
    logger = logging.getLogger(__name__)

    logger.info("Sorting files in the album")
    dir_file_names = list(map(os.path.basename, dir_entries))
    photo_ids_sorted = list(map(photo_ids.get, dir_file_names))
    logger.debug(f"Sorted photo IDs: {photo_ids_sorted}")
    flickr.photosets.reorderPhotos(
        photoset_id=album_id, photo_ids=",".join(photo_ids_sorted)
    )


# pylint: disable=R0914
def uploader():
    """
    command line tool for uploading files
    """
    args = get_args()

    logger = get_package_logger(args.loglevel)

    check_dir(args.sourceDir)
    check_env(flickrKey, flickrSecret)

    logger.info("Checking authentication")
    flickr = FlickrAPI(flickrKey, flickrSecret)
    auth_check(flickr, perms="write")

    #
    # First check if album with same name exists. The create() API endpoint
    # will create new album with the same name even though the name is already
    # used so we want to avoid that. This check needs to be done first because
    # in order to create an album, there needs to be at least one photo
    # uploaded to be used as title photo.
    #
    check_album_name(args.photoset, flickr)

    # List files in the top level of the directory.
    dir_name = args.sourceDir
    logger.info(f"Getting list of files from '{dir_name}'")
    dir_entries = [
        os.path.join(dir_name, f)
        for f in os.listdir(dir_name)
        if os.path.isfile(os.path.join(dir_name, f)) and is_known_suffix(f)
    ]

    # Sort the files according to the (EXIF) date.
    # This serves also as prevention for file related problems in the upload
    # phase (except this is still a TOCTOU problem).
    logger.info(f"Sorting {len(dir_entries)} files")
    try:
        dir_entries.sort(key=get_date)
    except PermissionError as exc:
        logger.error(exc)
        sys.exit(1)
    logger.debug(f"Sorted files: {dir_entries}")

    # Log the photo IDs to a file so that it is easier to recover if something
    # fails during the process.
    file_logger = get_file_logger(
        args.logfile.format(album_name=args.photoset), __name__
    )

    photo_ids, primary_photo_id = upload_files(
        dir_entries, file_logger, flickr, args.threads, args.dedup, args.retries
    )

    album_id = create_album(
        flickr, title=args.photoset, primary_photo_id=primary_photo_id
    )
    if album_id is None:
        logger.error(f"Failed to create album '{args.photoset}'")
        sys.exit(1)

    add_files_to_album(
        album_id, file_logger, flickr, args.threads, photo_ids, primary_photo_id
    )

    # The files need to be reordered since they were uploaded in parallel.
    reorder_files(album_id, dir_entries, flickr, photo_ids)
