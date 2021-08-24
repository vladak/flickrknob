#!/usr/bin/env python3

from alive_progress import alive_bar
import time

x = 5000
with alive_bar(x) as bar:
    for i in range(5000):
        time.sleep(.001)
        bar()
