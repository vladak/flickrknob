#!/usr/bin/env python3

from setuptools import setup

setup(name='flickrknob',
      version='0.1',
      author='Vladimir Kotal',
      author_email='vlada@devnull.cz',
      # list folders, not files
      packages=['flickrknob'],
      scripts=['flickrknob/bin/flickrUploader.py'],
      install_requires=[
        'flickrapi',
        'requests',
        'python-decouple',
        'alive-progress',
        'flake8',
        'exifread'
      ],
      )
