# Alternative Flickr uploader

The Flickr Uploadr app has a few limitations that make it unusable for my uses
cases, namely:
  - cannot specify title of the photos to match file names of the uploaded photos
  - the duplicate detection is inflexible. I want the photos still be present in
    the created album even though they are duplicate to some photos in the
    photostream.
  - cannot upload videos

In short, there is not enough knobs to turn for me, hence the main module is
named `flickrknob`.

## Setup

```
python3 -m venv env
. ./env/bin/activate
pip install -r requirements.txt
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
./flickrUploader.py "album name" "photo directory"
```

This will upload photos from the top level of the `photo directory` (i.e. does
not recurse) and assign them to the newly created album with `album name`.
