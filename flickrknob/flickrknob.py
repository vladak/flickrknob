#!/usr/bin/env python3

"""

Functions that wrap around Flickr API

"""

import os
import logging

import flickrapi
import webbrowser

import xml.etree.ElementTree as ElementTree


def report(bar, arg):
    logger = logging.getLogger(__name__)
    logger.debug("progress: {}".format(arg / 100))
    bar(arg / 100)


def get_albums(flickr_handle):
    """
    Return dictionary of albums. Names map to IDs.
    """

    logger = logging.getLogger(__name__)

    ret = dict()

    # Note: paging is not used currently. According to the API documentation
    #       this will return all photosets however this may change in the
    #       future.
    res = flickr_handle.photosets.getList()
    photosets_elem = res.find('photosets')
    for photoset_elem in list(photosets_elem.iter('photoset')):
        logger.debug(ElementTree.tostring(photoset_elem, 'utf-8'))
        title_elem = photoset_elem.find('title')
        if title_elem is not None:
            ret[title_elem.text] = photoset_elem.attrib['id']

    return ret


def create_album(flickr_handle, title, primary_photo_id):

    logger = logging.getLogger(__name__)

    logger.info("Creating album '{}' with primary photo {}".
                format(title, primary_photo_id))
    # Note: The album creation needs primary photo ID.
    # The photo will be automatically added to the album.
    res = flickr_handle.photosets.create(title=title,
                                         primary_photo_id=primary_photo_id)
    album_id = res.find('photoset').attrib['id']
    if album_id is not None:
        logger.info("Created album '{}' with ID {}".
                    format(title, album_id))

    return album_id


def upload_photo(flickr_handle, file_path, title=None, description=None,
                 tags=None, dedup=False):
    """
    Upload given file to Flickr. If title is not specified, it will be set
    to the basename of the file path.

    return photo ID or None.

    Note that Flickr automatically adds description based on EXIF data.

    Throws FlickrError on error.
    """
    res = None
    logger = logging.getLogger(__name__)

    logger.debug("Uploading \"{0}\")".format(file_path))

    params = {}
    if title is None:
        title = os.path.basename(file_path)

    params['title'] = title

    # With dedup_check = 1, uploaded photo can be detected as duplicate
    # even though the duplicate was already deleted.
    # The duplicate_photo_status tag will then say DELETED.
    # With dedup_check = 2 it seems this will cause the deleted duplicate
    # to be brought from the dead.
    if dedup:
        params['dedup_check'] = '2'

    if description is not None:
        params['description'] = description
    if tags is not None:
        params['tags'] = tags

    with open(file_path, 'rb') as fp:
        try:
            rsp = flickr_handle.upload(file_path, fileobj=fp,
                                       **params)
            logger.debug(ElementTree.tostring(rsp, 'utf-8'))
            photo_id = rsp.find('photoid')
            if photo_id is not None:
                res = photo_id.text
        except flickrapi.exceptions.FlickrDuplicate as e:
            logger.info("Duplicate photo '{}' with ID {}".
                        format(file_path, e.duplicate_photo_id))
            res = e.duplicate_photo_id

    logger.debug("Uploaded '{}' as {}".format(file_path, res))
    return res


def delete_photo(flickr_handle, photo_id):
    """
    Delete photo.
    """
    logger = logging.getLogger(__name__)

    logger.debug("Deleting file with photo ID {})".format(photo_id))
    flickr_handle.photos.delete(photo_id=photo_id)


def delete_album(flickr_handle, album_id):
    """
    Delete album
    """
    logger = logging.getLogger(__name__)

    logger.debug("Deleting album with ID {})".format(album_id))
    flickr_handle.photosets.delete(photoset_id=album_id)


def auth_check(flickr_handle, perms='read'):
    """
    TODO this should return/throw something in case of failure
    """

    # Only do this if we don't have a valid token already
    if not flickr_handle.token_valid(perms=perms):

        # Get a request token
        flickr_handle.get_request_token(oauth_callback='oob')

        # Open a browser at the authentication URL. Do this however
        # you want, as long as the user visits that URL.
        authorize_url = flickr_handle.auth_url(perms=perms)
        webbrowser.open_new_tab(authorize_url)

        # Get the verifier code from the user. Do this however you
        # want, as long as the user gives the application the code.
        verifier = str(input('Verifier code: '))

        # Trade the request token for an access token
        flickr_handle.get_access_token(verifier)
