#!/usr/bin/env python3

"""

This program lists all photos in given album.

"""

import argparse
import sys

from decouple import config

import flickrapi

from .flickrknob import auth_check, get_album_id
from .logutil import get_package_logger
from .parserutil import get_base_parser
from .utils import check_env, parse_args

flickrKey = config("FLICKR_KEY")
flickrSecret = config("FLICKR_SECRET")


def list_album_photos():
    """
    command line tool to list photos in an album
    """
    parser = argparse.ArgumentParser(
        add_help=False,
        description="list photos in Flickr album and",
        parents=[get_base_parser()],
    )
    parser.add_argument("name")

    args = parse_args(parser)

    logger = get_package_logger(args.loglevel)

    check_env(flickrKey, flickrSecret)

    logger.info("Checking authentication")
    flickr = flickrapi.FlickrAPI(flickrKey, flickrSecret)
    auth_check(flickr)

    album_id = get_album_id(flickr, args.name)
    if album_id is None:
        sys.exit(1)

    logger.info("Getting photo IDs")
    res = flickr.photosets.getPhotos(photoset_id=album_id)
    photoset_elem = res.find("photoset")
    logger.debug(f"photoset elem: {photoset_elem}")
    for photo_elem in list(photoset_elem.iter("photo")):
        photo_id = photo_elem.attrib.get("id")
        if photo_id:
            print(photo_elem.attrib["title"])
