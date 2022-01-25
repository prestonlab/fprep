#!/usr/bin/env python
#
# Get a list of the run numbers for a series of BOLD scans.

import os
import glob
import argparse


parser = argparse.ArgumentParser(description="Get run numbers from a BOLD directory")
parser.add_argument("bold_dir", type=str)
parser.add_argument("base", type=str)
args = parser.parse_args()

# get a sorted list of run numbers
dirs = glob.glob(os.path.join(args.bold_dir, args.base + "*"))
numbers = []
for d in dirs:
    name = os.path.basename(d)
    snum = ""
    for c in name:
        if c.isdigit():
            snum += c
    numbers.append(int(snum))

numbers.sort()

for n in numbers:
    print(n)
