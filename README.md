[![Python checks](https://github.com/vladak/flickrknob/actions/workflows/python-checks.yml/badge.svg)](https://github.com/vladak/flickrknob/actions/workflows/python-checks.yml) [![CodeQL](https://github.com/vladak/flickrknob/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/vladak/flickrknob/actions/workflows/codeql-analysis.yml)

# Alternative Flickr uploader

The [Flickr Uploadr app](https://www.flickr.com/tools/) has a few limitations that make it unusable for my uses
cases, namely:
  - cannot specify title of the photos to match file names of the uploaded photos
    - this makes it easier to track the correspondence between Flickr photos and files on my hard drive 
  - the duplicate detection is inflexible. Flickr Uploader uses Flickr API parameter to detect duplicate photos.
    Once a photo is detected as duplicate, it will not be addded to the album being created.
    I want the photos still be present in the created album even though they are duplicate to some photos in the
    photostream.
  - cannot upload videos
  - retries failed upload operations (which seem to fail in Flickr infrastructure more often than not with HTTP 504 error codes with
    messages such as *"CloudFront attempted to establish a connection with the origin, ..."*)

In short, there is not enough knobs to turn for me, hence the main module is
named `flickrknob`.

## Setup

Checkout the Git submodules:
```
git submodule init
git submodule checkout
```

Install the package:
```
python3 -m venv env
. ./env/bin/activate
python3 -m pip install poetry
poetry install
```

### Obtain credentials

[Set up a Flickr App](https://www.flickr.com/services/api/keys), and copy the key and secret into a `.env` file. The script will look here to obtain the credentials.

Your `.env` file should look like this, with `<key>` and `<secret>` replaced by the actual values:
```
FLICKR_KEY = "<key>"
FLICKR_SECRET = "<secret>"
```

Your access token will be stored in the `~/.flickr` directory.
Be sure you don't upload this folder or your `.env` file to a public repository.

## Run

```
flickrUploader "album name" "photo directory"
```

This will upload photos from the top level of the `photo directory` (i.e. does
not recurse) and assign them to the newly created album with `album name`.
