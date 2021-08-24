#!/usr/bin/env python3

from FileObjWithCallback import FileObjWithCallback
from alive_progress import alive_bar
import time


def report(bar, arg):
    # print("progress: {}".format(arg / 100))
    bar(arg / 100)


def read_in_chunks(file_object, chunk_size=1024):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


with open("/etc/passwd") as fp:

    # data = nfp.read()
    # print(len(data))
    # nfp.read(10000)

    with alive_bar(manual=True) as bar:
        nfp = FileObjWithCallback(fp, report, bar)
        for piece in read_in_chunks(nfp, chunk_size=100):
            time.sleep(.3)
