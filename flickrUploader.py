#!/usr/bin/env python3

"""

TODO

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

from flickrknob import upload_photo, auth_check, create_album, get_album_names
from photoutils import get_exif_date, is_known_suffix
from utils import check_dir

flickrKey = config('FLICKR_KEY')
flickrSecret = config('FLICKR_SECRET')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='yet another flickr uploader')
    parser.add_argument('-D', '--dedup', action='store_true', default=False,
                        help='deduplicate photos')

    parser.add_argument('photoset')
    parser.add_argument('sourceDir')
    args = parser.parse_args()

    # TODO: avoid basicConfig() - only want to receive logs from my modules
    logging.basicConfig(level=logging.DEBUG) # TODO: make this configurable
    logger = logging.getLogger(__name__)

    check_dir(args.sourceDir)

    if flickrKey is None:
        print("Missing Flickr key")
        sys.exit(1)
    if flickrSecret is None:
        print("Missing Flickr secret")
        sys.exit(1)

    flickr = flickrapi.FlickrAPI(flickrKey, flickrSecret)
    auth_check(flickr, perms='write')

    #
    # First check if album with same name exists. The create() API endpoint
    # will create new album with the same name even though the name is already
    # used so we want to avoid that. This check needs to be done first because
    # in order to create an album, there needs to be at least one photo uploaded
    # to be used as title photo.
    #
    album_names = get_album_names(flickr)
    if album_names is None or len(album_names) == 0:
        logger.error("Empty list of album names. Cannot check for dups.")
        sys.exit(1)

    if args.photoset in album_names:
        logger.error("Duplicate album name: '{}'".format(args.photoset))
        sys.exit(1)

    # Upload photos in the top level of the directory.
    dir_name = args.sourceDir
    # TODO: support more extenstions (videos)
    logger.info("Getting list of photo files from '{}'".format(dir_name))
    dir_entries = [os.path.join(dir_name, f) for f in os.listdir(dir_name)
                   if os.path.isfile(os.path.join(dir_name, f))
                   and is_known_suffix(f)]

    # TODO: check what happens if file cannot be read or lacks EXIF data
    logger.info("Sorting photo files")
    dir_entries.sort(key=get_exif_date)
    logger.debug("Sorted files: {}".format(dir_entries))

    logger.info("Uploading {} photos".format(len(dir_entries)))
    photo_ids = list()
    with alive_bar(len(dir_entries)) as bar:
        for file_path in dir_entries:
            # TODO: log the photo IDs to a file so that it is easier to
            #       recover if something fails during the process.
            file_name = os.path.basename(file_path)
            photo_id = upload_photo(flickr, file_path,
                                    title=file_name, dedup=args.dedup)
            logger.info("Uploaded {} as {}".format(file_name, photo_id))
            photo_ids.append(photo_id)
            bar()

    logger.info("Uploaded {} photos".format(len(photo_ids)))

    album_id = create_album(flickr,
                            title=args.photoset,
                            primary_photo_id=photo_ids[0])
    if album_id is None:
        # TODO: log the photo IDs here ?
        sys.exit(1)

    # TODO add uploaded photos to the album
    for photo_id in photo_ids:
        # Primary photo was automatically added to the album.
        if photo_id == photo_ids[0]:
            continue

        logger.debug("Adding photo {} to album {}".
                     format(photo_id, album_id))
        flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)
