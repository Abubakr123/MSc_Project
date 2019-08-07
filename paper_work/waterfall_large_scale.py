#!/usr/bin/python
import argparse
import os
import sys
import matplotlib.pyplot as plt
import numpy

# file_exist_check for argparse
def existing_file(filename):
    if not(os.path.exists(filename) and os.path.isfile(filename)):
        raise argparse.ArgumentTypeError(filename+" is not an existing file!")
    else:
        return filename

# command line parse
parser = argparse.ArgumentParser(description='Create a waterfall plot.')
parser.add_argument('files',help='List of files to be processed.',nargs='+',type=existing_file)
verbosity_group = parser.add_mutually_exclusive_group()
verbosity_group.add_argument('-v','--verbose',help='print more stuff',action='store_true')
verbosity_group.add_argument('-q','--quiet',  help='only print warnings',action='store_true')
parser.add_argument('-T','--tscr',help='tscrunch input archives',action='store_true')
parser.add_argument('-P','--psr',help='name of input archives',type=str, default='0')
parser.add_argument('-F','--fscr',help='fscrunch input archives',action='store_true')
parser.add_argument('-b','--bscr',help='bscrunch input archives by this factor',type=int,default='0')
parser.add_argument('-D','--diff',help='plot difference to first profile',action='store_true')
parser.add_argument('-s','--snr',help='reject profiles with less than 50%% median S/N',
                    action='store_true')
parser.add_argument('-a','--avg',help='calculate average of at least N profiles',type=int,default='1')
parser.add_argument('-d','--days',help='calculate average of at least X days',type=float,default='0')
parser.add_argument('-x','--xrange',help='overwrite automatic plot range',type=float,nargs=2,
                    metavar=('xmin','xmax'))
args = parser.parse_args()
if not args.psr: print("print pulsar name")

# check input
if not args.fscr and not(args.tscr and len(args.files) == 1):
    print("Don't use time-resolved data when creating a frequency-dependent waterfall!")
    sys.exit()

# load files
if not args.quiet: print("loading input files ...")
import psrchive
archives = []
for filename in args.files:
    if args.verbose: print("loading " + filename + " ...")
    archives.append(psrchive.Archive_load(filename))
    if args.tscr: archives[-1].tscrunch()
    if args.fscr: archives[-1].fscrunch()
    if args.bscr != 0: archives[-1].bscrunch(args.bscr)
    archives[-1].pscrunch()
    if not archives[-1].get_dedispersed(): archives[-1].dedisperse()
    archives[-1].remove_baseline()
nbin = archives[0].get_nbin()

# read profiles
if not args.quiet: print("reading profiles ...")
profiles = []
mjds = []
for ar in archives:
    nchan = ar.get_nchan()
    nsub = ar.get_nsubint()
    for isub in range(nsub):
        for ichan in range(nchan):
            pr = ar.get_Profile(isub,0,ichan)
            if pr.get_weight() > 0:
                profiles.append(pr)
                mjds.append(ar.get_Integration(isub).get_epoch().in_days())
nprof = len(profiles)
if not args.quiet: print(" ... read " + str(nprof) + " profiles ...")
# reject by snr
if args.snr:
    snr = [pr.snr() for pr in profiles]
    med_snr = numpy.median(snr)
    if not args.quiet: print("median S/N: " + str(med_snr))
    rej_ct = 0
    ii = 0
    while ii < nprof:
        if snr[ii] < 0.5*med_snr:
            del profiles[ii]
            del snr[ii]
            del mjds[ii]
            nprof -= 1
            rej_ct += 1
        else:
            ii += 1
    if not args.quiet: print("rejected " + str(rej_ct) + " profiles because of S/N!")

# rotate and scale standard
std_amps = profiles[0].get_amps()
std_maxbin = numpy.argmax(std_amps)
std_ampl = profiles[0].max()
profiles[0].rotate_phase(std_maxbin / float(nbin) - 0.5)
profiles[0].scale(1/std_ampl)
std_maxbin = numpy.argmax(std_amps)
# get width for plot window and fits
edge_l = std_maxbin
edge_r = std_maxbin
while std_amps[edge_l] > 0.3: edge_l-=1
while std_amps[edge_r] > 0.3: edge_r+=1
width_l = std_maxbin - edge_l
width_r = edge_r - std_maxbin
width_min = min((width_l,width_r))
xmin = edge_l - 1*width_min
xmax = edge_r + 3*width_min

# quick align (initial guess for phase shift)
if not args.quiet: print("aligning ...")
p = psrchive.ProfileShiftFit()
p.set_standard(profiles[0])
for pr in profiles:
    p.set_Profile(pr)
    p.compute()
    shift = p.get_shift()
    scale = p.get_scale()
    pr.rotate_phase(shift[0])
    pr.scale(1/scale[0])

# fine align, minimise sum of squared residuals btwn obs and tmpl near leading edge
def sum_squared_res(a1,a2):
    result = 0
    for ii in range(len(a1)):
        result += (a1[ii] - a2[ii])**2
        return result
# shift by +-1 bin in steps of 1/RES bin
RES = 40
for pr in profiles[1:]:
    clone = pr.clone()
    clone.rotate_phase((-1-1./RES)/nbin)
    obs_amps = clone.get_amps()
    ssr = []
    for ii in range(2*RES+1):
        clone.rotate_phase(1./RES/nbin)
        ssr.append(sum_squared_res(std_amps[std_maxbin-width_l:std_maxbin+width_l/3],
                                   obs_amps[std_maxbin-width_l:std_maxbin+width_l/3]))
    del clone
    best_shift = 1. * (numpy.argmin(ssr) - RES) / RES / nbin
    pr.rotate_phase(best_shift)

# plot
if not args.quiet: print("plotting ...")
# do averaging and set up datasets to plot
xx = numpy.array(range(nbin)) / float(nbin)
nplot = 0
nn = 0
first_mjd = 0
yy = numpy.zeros(nbin)
for ii in range(nprof):
    yy += profiles[ii].get_amps()
    nn += 1
    if first_mjd == 0: first_mjd = mjds[ii]
    if ((nn >= args.avg and abs(mjds[ii] - first_mjd) >= args.days) or 
        ii == nprof - 1 or (ii == 0 and args.diff)
    ):
        yy /= nn
        if args.diff:
            yy -= profiles[0].get_amps()
            yy *= 10
        yy += 0.1*nplot
        plt.plot(xx,yy)
        nplot += 1
        nn = 0
        first_mjd = 0
        yy = numpy.zeros(nbin)
# now plot
if args.xrange:
    plt.xlim(args.xrange)
else:
    plt.xlim([xmin/float(nbin),xmax/float(nbin)])
if args.diff:
    ymin = -0.5
    ymax = 1 + 0.1*nplot - 0.5
else:
    ymin = 0
    ymax = 1 + 0.17*nplot

plt.ylim([ymin,ymax])
plt.title("Profile evolution with frequency for %s"%str(args.psr))
plt.xlabel("Pulse phase")
plt.ylabel("Frequency (118.164 - 186.328 MHz)")
plt.savefig("%s_profile_evolution"%str(args.psr))
plt.show()

