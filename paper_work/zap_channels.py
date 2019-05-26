#!/usr/bin/env python
import os.path as path
import psrchive as psr
import numpy as np
import argparse

parser = argparse.ArgumentParser(description="cut-off frequency channels")
parser.add_argument('files', type=str, nargs='+', help='input archives')
parser.add_argument('-o', '--outdir', dest='output_dir', metavar='<output_dir>', default='', help='specify output directory')

args = parser.parse_args()
output_dir = args.output_dir

if ( not args.files ):
    print "E.g.: python zap_channels.py input.ar -o <out-put>"
    exit(1)



# cut-off the first 43 and the last 7 channels of PSR with 400 channels (i.e. the last 16 channels of PSR with 366 channels).
# frequency range is as expected (118.1640625 <= freq <= 186.328125).
first_frequency = 118.1640625
last_frequency = 186.328125
channel_bw = 0.1953125
nchan_final = 350

# check the frequency chanels of each file and erform the cut-off
for file in args.files:
    archive=psr.Archive_load(file)
    nchan=archive.get_nchan()
    if ( nchan == 400 ):
        print archive, nchan
        archive.remove_chan(0, 41)
        archive.remove_chan(350, 357)
        archive.unload(output_dir + '/' + file + '.F350')
    else:
        print archive, nchan
        archive.remove_chan(350, 365)
        archive.unload(output_dir + '/' + file + '.F350')



