#!/usr/bin/env python
import os.path as path
import psrchive as psr
import numpy as np

import argparse
from math import sqrt

parser = argparse.ArgumentParser(description="Set the weight of profiles to"
                                 +" their S/N")
parser.add_argument('files', type=str, nargs='+', help='input archives')
parser.add_argument('-e', '--ext', type=str, nargs=1,
                    help="write new files with this extension")
parser.add_argument('--snr', action='store_true', help="use S/N of the profile"
                    + " as the new weight")
parser.add_argument('--snrsq', action='store_true', help="use S/N^2 of the profile"
                    + " as the new weight")
parser.add_argument('--rms', action='store_true', help="use baseline's rms^-1"
                    + " as the new weight")
parser.add_argument('-m', '--multiply', action='store_true', help="Multiply the"
                    + " desired weight by the original weight of the profile")
parser.add_argument('-R','--rescale',action='store_true', help="Set the peak"
                    + " of the profile to the chosen scale factor")

args = parser.parse_args()

if ( not args.files or not args.ext or not ( args.snr or args.rms or args.snrsq) ):
    print "You need to specify the input archive, extension for the output"
    print "as well as the quantity you want to use as the new weight"
    print "E.g.: python set_wt_to_snr.py input.ar -e snr --rms"
    exit(1)

for file in args.files:
    archive=psr.Archive_load(file)
    for isub in range(archive.get_nsubint()):
        if ( args.rms or args.rescale ):
            bs=(archive.get_Integration(isub)).baseline_stats()
        for ichan in range(archive.get_nchan()):
            for ipol in range(archive.get_npol()):
                p=archive.get_Profile(isub,ipol,ichan)
                if ( p.get_weight() > 0.0 ):
                    if ( args.snr ):
                        new_weight=p.snr()
                    elif ( args.snrsq ):
                        new_weight=p.snr()*p.snr()
                    elif ( args.rms ):
                        new_weight=1./sqrt(bs[1][ipol][ichan])
    
                    if ( args.multiply ):
                        new_weight=new_weight*p.get_weight()
                    if ( args.rescale ):
                        pd=p.get_amps()
                        pd -= bs[0][ipol][ichan]
                        profile_peak=np.amax(pd)
                        pd *= new_weight / profile_peak
                        pd += bs[0][ipol][ichan]
                    else:
                        p.set_weight(new_weight)

    archive.unload(path.splitext(path.basename(file))[0]+"."+args.ext[0])
