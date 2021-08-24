#!/usr/bin/env python3

import json

import flickrapi
import webbrowser
import sys

from decouple import config

api_key = config('FLICKR_KEY')
api_secret = config('FLICKR_SECRET')

if api_key is None:
    print("Missing Flickr key")
    sys.exit(1)
if api_secret is None:
    print("Missing Flickr secret")
    sys.exit(1)

flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

print('Step 1: authenticate')

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms='read'):

    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms='read')
    webbrowser.open_new_tab(authorize_url)

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    verifier = str(input('Verifier code: '))

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

print('Step 2: use Flickr')
# resp = flickr.photos.getInfo(photo_id='7658567128')
resp = flickr.people.findByEmail(find_email='vlada@devnull.cz')
print(resp)
#for el in resp:
#    print(el)

user_id = resp['user']['id']
print("user_id = " + user_id)

resp = flickr.photosets.getList(user_id=user_id)
# json_str = json.dumps(resp, indent=4)
# print(json_str)
for pset in resp['photosets']['photoset']:
   # pset_str = json.dumps(pset, indent=4)
   # print(pset_str)
   # print(pset['id'] + " " + pset['title']['_content'])
   title = pset['title']['_content']
   if "farn" in title:
       print(pset['id'] + " " + title)

photoset_id = "72157719733783830"
resp = flickr.photosets.getPhotos(photoset_id=photoset_id, user_id=user_id)
# json_str = json.dumps(resp, indent=4)
# print(json_str)
for photo in resp['photoset']['photo']:
   resp = flickr.photos.getInfo(photo_id=photo['id'])
   json_str = json.dumps(resp, indent=4)
   print(json_str)
