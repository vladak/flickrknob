#!/usr/bin/env python3

"""

This program deletes album along with all photos contained therein.

It is mean really just to aid debugging the flickrUploader.

"""

import sys
from decouple import config
import logging
import argparse

import flickrapi
from alive_progress import alive_bar

from .flickrknob import auth_check, get_albums, delete_album, delete_photo
from .logutil import LogLevelAction
from .utils import confirm


flickrKey = config('FLICKR_DELETE_KEY')
flickrSecret = config('FLICKR_DELETE_SECRET')


def delete_album_with_photos():
    parser = argparse.ArgumentParser(description='delete Flickr album and '
                                                 'all its photos')
    parser.add_argument('-l', '--loglevel', action=LogLevelAction,
                        help='Set log level (e.g. \"ERROR\")',
                        default=logging.INFO)

    parser.add_argument('name')
    try:
        args = parser.parse_args()
    except ValueError as e:
        print("Argument parsing failed: {}".format(e), file=sys.stderr)
        sys.exit(1)

    logger = logging.getLogger(__package__)
    logger.setLevel(args.loglevel)
    handler = logging.StreamHandler()
    logger.addHandler(handler)

    if flickrKey is None:
        print("Missing Flickr key")
        sys.exit(1)
    if flickrSecret is None:
        print("Missing Flickr secret")
        sys.exit(1)

    logger.info("Checking authentication")
    flickr = flickrapi.FlickrAPI(flickrKey, flickrSecret)
    auth_check(flickr, perms='delete')

    logger.info("Getting list of albums")
    albums = get_albums(flickr)
    if albums is None or len(albums.items()) == 0:
        logger.error("Empty list of albums")
        sys.exit(1)

    album_id = albums.get(args.name)
    if album_id is None:
        logger.error("Did not find album with name '{}'".format(args.name))
        sys.exit(1)

    # TODO get list of photos in the album (so that progress can be displayed)
    logger.info("Getting photo IDs")
    res = flickr.photosets.getPhotos(photoset_id=album_id)
    photoset_elem = res.find('photoset')
    logger.debug("photoset elem: {}".format(photoset_elem))
    photo_ids = list()
    for photo_elem in list(photoset_elem.iter('photo')):
        photo_id = photo_elem.attrib['id']
        if photo_id:
            photo_ids.append(photo_id)
    logger.debug("Photo IDs: {}".format(photo_ids))

    # TODO: ask for confirmation
    if not confirm("Delete album with {} photos ? Y/N ".
                   format(len(photo_ids))):
        sys.exit(0)

    logger.info("Deleting {} files".format(len(photo_ids)))
    cnt = 0
    with alive_bar(len(photo_ids)) as bar:
        for photo_id in photo_ids:
            delete_photo(flickr, photo_id)
            bar()
            cnt = cnt + 1

    logger.info("Deleted {} files".format(cnt))

    delete_album(flickr, album_id)