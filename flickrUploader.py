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

from flickrknob import upload_photo, auth_check
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

    logging.basicConfig(level=logging.DEBUG) # TODO
    logger = logging.getLogger(__name__)

    check_dir(args.sourceDir)

    if flickrKey is None:
        print("Missing Flickr key")
        sys.exit(1)
    if flickrSecret is None:
        print("Missing Flickr secret")
        sys.exit(1)

    flickr = flickrapi.FlickrAPI(flickrKey, flickrSecret)
                                 # format='parsed-json')
    auth_check(flickr, perms='write')

    # Upload photos in the top level of the directory.
    # TODO: do not recurse
    photo_ids = list()
    # TODO: order photos according to date taken (will require EXIF reader)
    #       otherwise they will appear in the album in the order uploaded.
    for dir_name, _, file_names in os.walk(args.sourceDir):
        for file_name in file_names:
            # TODO: check what happens if file cannot be read
            # TODO: log the photo IDs to a file so that it is easier to
            #       recover if something fails during the process.
            photo_id = upload_photo(flickr, os.path.join(dir_name, file_name),
                                    title=file_name, dedup=args.dedup)
            logger.info("Uploaded {} as {}".format(file_name, photo_id))
            photo_ids.append(photo_id)

    logger.info("Uploaded {} photos".format(len(photo_ids)))

    # TODO: check if album exists first. The API will create new album
    #       with the same name even though the name is already used.
    # The album creation needs primary photo ID.
    res = flickr.photosets.create(title=args.photoset,
                                  primary_photo_id=photo_ids[0])
    album_id = res.find('photoset').attrib['id']
    logger.info("Created album \"{}\" with ID {}".
                format(args.photoset, album_id))

    # TODO add uploaded photos to the album
    for photo_id in photo_ids:
        # Primary photo was automatically added to the album.
        if photo_id == photo_ids[0]:
            continue

        logger.debug("Adding photo {} to album {}".
                     format(photo_id, album_id))
        flickr.photosets.addPhoto(photoset_id=album_id, photo_id=photo_id)

