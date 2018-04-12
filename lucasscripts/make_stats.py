import os
import sys
import glob
import numpy
import argparse
from collections import Counter

try:
	import psrchive as p
	from misc_tools import *
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass

# make_stats.py: script for producing some useful stats from a list of psrchive-format files
# Author:        Lucas Guillemot
# Last update:   13 Oct 2014
# Version:       2.13



# Some default declarations
DEF_DATA_DIR    = '.'
DEF_DATA_EXT    = 'zap'
DEF_OUTPUT      = 'stats.dat'
DEF_WIDTH       = 8.
DEF_HEIGHT      = 6.
DEF_OBSCOMB     = 'obscomb.png'
DEF_FREQPLOT    = 'freqplot.png'
DEF_SNRPLOT     = 'snrsplot.png'
DEF_OBSCHAR     = 'obschar.png'
DEF_ZAPPLOT     = 'zapplot.png'
DEF_ORIGDATAEXT = 'refold'
DEF_DPI         = 120
DEF_LOGFILE     = None


# 

def get_parser():
	parser = argparse.ArgumentParser(description='A script for producing useful stats from a list of psrchive-format files.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-output',type=str,default=DEF_OUTPUT,help='Name of an output file to store the statistics in (default: \"%s\").' % DEF_OUTPUT)
	parser.add_argument('-width',type=float,default=DEF_WIDTH,help='Width of individual subplots in inches (default: %f).' % DEF_WIDTH)
	parser.add_argument('-height',type=float,default=DEF_HEIGHT,help='Height of individual subplots in inches (default: %f).' % DEF_HEIGHT)
	parser.add_argument('-obscomb',type=str,default=DEF_OBSCOMB,help='Name of the output graph showing the \"observation comb\" (default: \"%s\").' % DEF_OBSCOMB)
	parser.add_argument('-freqplot',type=str,default=DEF_FREQPLOT,help='Name of the output graph showing observing frequencies (default: \"%s\").' % DEF_FREQPLOT)
	parser.add_argument('-snrplot',type=str,default=DEF_SNRPLOT,help='Name of the output graph showing SNR values (default: \"%s\").' % DEF_SNRPLOT)
	parser.add_argument('-obschar',type=str,default=DEF_OBSCHAR,help='Name of the output graph showing the observation characteristics (default: \"%s\").' % DEF_OBSCHAR)
	parser.add_argument('-zapplot',type=str,default=DEF_ZAPPLOT,help='Name of the output graph showing zapping properties versus time (default: \"%s\").' % DEF_ZAPPLOT)
	parser.add_argument('-noplots',action='store_true',default=False,help='If set, will not produce graphical outputs (default: False).')
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not the plots should be overwritten (default: False).')
	parser.add_argument('-origdatadir',type=str,default=None,help='Directory containing the original data files (i.e. containing the original nsub, nchan, etc.) information (default: None).')
	parser.add_argument('-origdataext',type=str,default=DEF_ORIGDATAEXT,help='Extension of original data files to read from (default: \"%s\").' % DEF_ORIGDATAEXT)
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	parser.add_argument('-logfile',type=str,default=DEF_LOGFILE,help='Path to an output log file.')
	return parser

#

def make_stats(	datadir     = DEF_DATA_DIR, \
		dataext     = DEF_DATA_EXT, \
		output      = DEF_OUTPUT, \
		width       = DEF_WIDTH, \
		height      = DEF_HEIGHT, \
		obscomb     = DEF_OBSCOMB, \
		freqplot    = DEF_FREQPLOT, \
		snrplot     = DEF_SNRPLOT, \
		obschar     = DEF_OBSCHAR, \
		zapplot     = DEF_ZAPPLOT, \
		noplots     = False, \
		overwrite   = False, \
		origdatadir = None, \
		origdataext = DEF_ORIGDATAEXT, \
		logfile     = DEF_LOGFILE, \
		**kwargs ):
	
	# Make some initial checks
	if logfile is not None:
		locargs = locals()
		logger  = initialize_logging(os.path.basename(__file__),logfile=logfile)
		logger.info('running refold_data with arguments:')
		logger.info(locargs)
	
	if not os.path.isdir(datadir):
		if logfile is not None: logger.error('data directory \"%s\" does not exist!' % datadir)
		raise ExistError('Error: data directory does not exist!')
		
	if dataext[0] == '.': dataext[1:]
	
	files  = glob.glob(os.path.join(datadir,'*.' + dataext))
	files.sort()
	Nfiles = len(files)
	if Nfiles == 0:
		if logfile is not None: logger.error('no data files selected! Check data directory and extension: \"%s\" \"%s\".' % (datadir,dataext))
		raise NoFilesError('Error: no data files selected! Check data directory and extension.')
	
	if noplots is False:
		if os.path.exists(obscomb):
			if overwrite: os.unlink(obscomb)
			else:
				if logfile is not None: logger.error('Observation comb plot \"%s\" already exists.' % obscomb)
				raise AlreadyExistError('Observation comb plot already exists. Exiting...')
				
		if os.path.exists(freqplot):
			if overwrite: os.unlink(freqplot)
			else:
				if logfile is not None: logger.error('Frequency plot \"%s\" already exists.' % freqplot)
				raise AlreadyExistError('Frequency plot already exists. Exiting...')
	
		if os.path.exists(snrplot):
			if overwrite: os.unlink(snrplot)
			else:
				if logfile is not None: logger.error('SNR plot \"%s\" already exists.' % snrplot)
				raise AlreadyExistError('SNR plot already exists. Exiting...')
				
		if os.path.exists(obschar):
			if overwrite: os.unlink(obschar)
			else:
				if logfile is not None: logger.error('Observation characteristic plot \"%s\" already exists.' % obschar)
				raise AlreadyExistError('Observation characteristic plot already exists. Exiting...')
		
		if os.path.exists(zapplot):
			if overwrite: os.unlink(zapplot)
			else:
				if logfile is not None: logger.error('Zapping plot \"%s\" already exists.' % zapplot)
				raise AlreadyExistError('Zapping plot already exists. Exiting...')
	
	#
	
	goodfiles = []
	
	for fichier in files:
		# Make sure the file is a valid psrchive file
		try:
			arch = load_archive(fichier)
		except:
			continue
			
		goodfiles.append(fichier)
	
	Nfiles = len(goodfiles)
	if Nfiles == 0:
		if logfile is not None: logger.error('No valid data files selected. Exiting here.')
		raise NoFilesError('No valid data files selected. Exiting here.')
	
	if logfile is not None: logger.info('Selected %d files. Will now collect the information...' % Nfiles)
	print 'Selected %d files. Will now collect the information...' % Nfiles
	
	
	# Look for the original data files
	if origdatadir is not None and not os.path.isdir(origdatadir):
		if logfile is not None: logger.error('data directory \"%s\" does not exist!' % origdatadir)
		raise ExistError('Error: origdatadir does not exist.')
	elif origdatadir is not None:
		if origdataext[0] == '.': origdataext[1:]
		
		orig_archives = glob.glob(os.path.join(origdatadir,'*.'+origdataext))
		
		if len(orig_archives) == 0:
			if logfile is not None: logger.error('No data files found in the original data directory. Exiting here.')
			raise NoFilesError('No data files found in the original data directory. Exiting here.')
			
		for orig_fichier in orig_archives:
			# Make sure the file is a valid psrchive file
			try:
				arch = load_archive(orig_fichier)
			except:
				if logfile is not None: logger.error('File \"%s\" does not seem to be a valid psrchive file!' % orig_fichier)
				raise PsrchiveError('Error: file does not seem to be a valid psrchive file!')
				
		good_origfiles = []
		for fichier in goodfiles:
			found = 0
			base1 = os.path.basename(fichier)
			base1 = os.path.splitext(base1)[0]
			for orig_fichier in orig_archives:
				base2 = os.path.basename(orig_fichier)
				base2 = os.path.splitext(base2)[0]
				if base1 == base2:
					found = 1
					break
					
			if not found:
				if logfile is not None: logger.error('Did not find a valid counterpart for all files in the original data directory!')
				raise NoFilesError('Did not find a valid counterpart for all files in the original data directory!')
				
			good_origfiles.append(orig_fichier)
	
	#
	
	epochs   = []
	lengths  = []
	freqs    = []
	bws      = []
	snrs     = []
	sources  = []
	sites    = []
	backends = []
	nbins    = []
	npols    = []
	nsubs    = []
	nchs     = []
	nsubxs   = []
	nchxs    = []

	line     = '# index epoch length freq bw snr source site backend nbin npol nsub nsubgood nchan nchangood'
	print line
	outf     = open(output,'w+')
	outf.write(line + '\n')

	for i in range(len(goodfiles)):
		fichier               = goodfiles[i]
		arch                  = load_archive(fichier)
		epoch                 = get_epoch_open(arch)
		length                = get_length_open(arch)
		freq                  = get_frequency_open(arch)
		bw                    = get_bandwidth_open(arch)
		source                = get_source_open(arch)
		site                  = get_site_open(arch)
		backend               = get_backend(fichier)
		
		if origdatadir is None: 
			nbin, npol, nsub, nch = get_ns_open(arch)
			nsubx, nchx           = get_nsubx_nchanx_open(arch)
			
			# This one MUST be done last, because it scrunches the nsubint, npol, etc., information.
			snr                   = get_snr_open(arch)
		else:
			# But is must be done before the orig data file is open! 
			snr                   = get_snr_open(arch)
			orig_fichier          = good_origfiles[i]
			nbin, npol, nsub, nch = get_ns(orig_fichier)
			nsubx, nchx           = get_nsubx_nchanx(orig_fichier)
		
		if numpy.isnan(snr):
			print 'SNR = NaN for archive file \"%s\". Continue...' % fichier
			continue
		
		#
		
		line                  = "%d %f %f %f %f %f %s %s %s %d %d %d %d %d %d" % (i+1, epoch, length, freq, bw, snr, source, site, backend, nbin, npol, nsub, nsubx, nch, nchx)
		print line
		outf.write(line + '\n')
		
		epochs.append(epoch)
		lengths.append(length)
		freqs.append(freq)
		bws.append(bw)
		snrs.append(snr)
		sources.append(source)
		sites.append(site)
		backends.append(backend)
		nbins.append(nbin)
		npols.append(npol)
		nsubs.append(nsub)
		nchs.append(nch)
		nsubxs.append(nsubx)
		nchxs.append(nchx)
		
	# Now get the statistics
	line    = '\nStatistics:\n'
	line   += '-----------\n'
	
	Nobs    = len(epochs)
	line   += 'Num. observations:                             ' + str(Nobs) + '\n'
	
	epochs  = numpy.array(epochs)
	tmin    = epochs.min()
	tmax    = epochs.max()
	deltat  = tmax - tmin
	avgcad  = float(Nobs) / deltat
	avgdel  = 1. / avgcad
	line   += 'Min. epoch (MJD):                              ' + str(tmin) + '\n'
	line   += 'Max. epoch (MJD):                              ' + str(tmax) + '\n'
	line   += 'Interval (days):                               ' + str(deltat) + '\n'
	line   += 'Avg. cadence (per day):                        ' + str(avgcad) + '\n'
	line   += 'Avg. time between obs. (day):                  ' + str(avgdel) + '\n'
	
	lengths = numpy.array(lengths) / 60.
	totlen  = lengths.sum()
	avglen  = lengths.mean()
	medlen  = numpy.median(lengths)
	stdlen  = lengths.std()
	line   += 'Total obs. length (min):                       ' + str(totlen) + '\n'
	line   += 'Avg. obs. length (min):                        ' + str(avglen) + '\n'
	line   += 'Median obs. length (min):                      ' + str(medlen) + '\n'
	line   += 'Stddev. obs. length (min):                     ' + str(stdlen) + '\n'
	
	freqcnt = Counter(freqs)
	freqs   = numpy.array(freqs)
	line   += 'Frequencies (MHz):                             ' + str(freqcnt.most_common(len(freqcnt))) + '\n'
	
	bwcnt   = Counter(bws)
	bws     = numpy.array(bws)
	line   += 'Bandwidths (MHz):                              ' + str(bwcnt.most_common(len(bwcnt))) + '\n'
	
	srccnt  = Counter(sources)
	line   += 'Sources:                                       ' + str(srccnt.most_common(len(srccnt))) + '\n'
	
	sitecnt = Counter(sites)
	line   += 'Sites:                                         ' + str(sitecnt.most_common(len(sitecnt))) + '\n'
	
	bkdcnt  = Counter(backends)
	line   += 'Backends:                                      ' + str(bkdcnt.most_common(len(bkdcnt))) + '\n'
	
	nbincnt = Counter(nbins)
	line   += 'Num. bins:                                     ' + str(nbincnt.most_common(len(nbincnt))) + '\n'
	
	npolcnt = Counter(npols)
	line   += 'Num. polarizations:                            ' + str(npolcnt.most_common(len(npolcnt))) + '\n'
	
	nsubcnt = Counter(nsubs)
	line   += 'Num. subintegrations:                          ' + str(nsubcnt.most_common(len(nsubcnt))) + '\n'
	
	nsubs   = numpy.array(nsubs,dtype=float)
	nsubxs  = numpy.array(nsubxs,dtype=float)
	zapsubs = 1. - nsubxs / nsubs
	avgzaps = zapsubs.mean()
	line   += 'Avg. Percentage of zapped subintegrations (%): ' + str(100.*avgzaps) + '\n'
	
	nchcnt  = Counter(nchs)
	line   += 'Num. channels:                                 ' + str(nchcnt.most_common(len(nchcnt))) + '\n'
	
	nchs    = numpy.array(nchs)
	nchxs   = numpy.array(nchxs)
	zapchs  = 1. - nchxs / nchs
	avgzapc = zapchs.mean()
	line   += 'Avg. Percentage of zapped channels (%):        ' + str(100.*avgzapc) + '\n'
	
	snrs    = numpy.array(snrs)
	avgsnr  = snrs.mean()
	medsnr  = numpy.median(snrs)
	stdsnr  = snrs.std()
	line   += 'Avg. SNR:                                      ' + str(avgsnr) + '\n'
	line   += 'Median SNR:                                    ' + str(medsnr) + '\n'
	line   += 'Stddev. SNR:                                   ' + str(stdsnr) + '\n'
	
	nsnrs   = snrs / numpy.sqrt(lengths) / numpy.sqrt(bws)
	avgnsnr = nsnrs.mean()
	mednsnr = numpy.median(nsnrs)
	stdnsnr = nsnrs.std()
	line   += 'Avg. Normalized SNR (per sqrt(min * MHz)):     ' + str(avgnsnr) + '\n'
	line   += 'Median Normalized SNR (per sqrt(min * MHz)):   ' + str(mednsnr) + '\n'
	line   += 'Stddev. Normalized SNR (per sqrt(min * MHz)):  ' + str(stdnsnr) + '\n'
	
	print line
	outf.write(line + '\n')
	outf.close()

	# Now plot the results
	if noplots: return

	import matplotlib
	if matplotlib.get_backend() == 'agg': pass
	else:                                 matplotlib.use('agg')
	
	from matplotlib import pyplot as P
	from matplotlib.ticker import MultipleLocator
	P.rcParams["xtick.major.size"] = 6
	P.rcParams["ytick.major.size"] = 6
	P.rcParams["xtick.minor.size"] = 3
	P.rcParams["ytick.minor.size"] = 3
	P.rcParams["font.size"]        = 12.
	P.rcParams["axes.labelsize"]   = 14.
	minorLocator = MultipleLocator(5)

	if kwargs.has_key('dpi'): dpi = kwargs['dpi']
	else:                     dpi = DEF_DPI
	
	
	# Observation comb
	if obscomb is not None:
		fig  = P.figure(figsize=(width,height))
		
		ax   = fig.add_subplot(111)
		axb  = ax.twinx()
		mint = numpy.floor(tmin-1.)
		maxt = numpy.ceil(tmax+1.)
		n1, bins, edges = ax.hist(epochs,range=[mint,maxt],bins=(maxt-mint)*3,linewidth=0.)
		n2, bins, edges = axb.hist(epochs,range=[mint,maxt],bins=(maxt-mint)*3,linewidth=1.,cumulative=True,fill=False,histtype='stepfilled')
		ax.set_xlim([mint,maxt])
		ax.set_xlabel('Epoch (MJD)')
		ax.set_ylim([0.,n1.max()+0.1])
		ax.set_ylabel('Counts',color='blue')
		ax.tick_params(axis='y',colors='blue')
		ax.ticklabel_format(useOffset=False)
		ax.minorticks_on()
		axb.set_ylim([0.,n2.max()+0.1])
		axb.set_ylabel('Cumulative Counts')
		axb.minorticks_on()
		
		fig.savefig(obscomb,bbox_inches='tight')
		P.close(fig)
	
	
	# Frequency vs time
	if freqplot is not None:
		fig  = P.figure(figsize=(2.*width,2.*height))
		fig.subplots_adjust(wspace=0.25,hspace=0.25)
		
		ax1  = fig.add_subplot(211)
		minf = (freqs-0.5*bws).min()-25.
		maxf = (freqs+0.5*bws).max()+25.
		ax1.errorbar(epochs,freqs,yerr=0.5*bws,fmt='o',mew=0.,mec='b')
		ax1.set_xlim([mint,maxt])
		ax1.set_xlabel('Epoch (MJD)')
		ax1.set_ylim([minf,maxf])
		ax1.set_ylabel('Frequency (MHz)')
		ax1.ticklabel_format(useOffset=False)
		ax1.minorticks_on()
		
		ax2  = fig.add_subplot(223)
		ax2b = ax2.twinx()
		keys = freqcnt.keys()
		keys.sort()
		vals = [freqcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		Xlab = ["%.3f" % float(keys[i]) for i in xrange(len(keys))]
		ax2.bar(X,vals,align='center',width=0.33,linewidth=0.,color='r')
		ax2.set_xlim([X.min()-1.,X.max()+1.])
		ax2.set_xticks(X)
		ax2.set_xticklabels(Xlab,rotation=45)
		ax2.set_xlabel('Frequency (MHz)')
		ax2.set_ylim([0.,numpy.array(vals).sum()])
		ax2.set_ylabel('Counts')
		ax2.yaxis.set_minor_locator(minorLocator)
		ax2b.set_ylabel('Percentage (%)')
		ax2b.set_ylim([0.,100.])
		
		ax3  = fig.add_subplot(224)
		ax3b = ax3.twinx()
		keys = bwcnt.keys()
		keys.sort()
		vals = [bwcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		ax3.bar(X,vals,align='center',width=0.33,linewidth=0.,color='g')
		ax3.set_xlim([X.min()-1.,X.max()+1.])
		ax3.set_xticks(X)
		ax3.set_xticklabels(keys,rotation=45)
		ax3.set_xlabel('Bandwidth (MHz)')
		ax3.set_ylim([0.,numpy.array(vals).sum()])
		ax3.set_ylabel('Counts')
		ax3.yaxis.set_minor_locator(minorLocator)
		ax3b.set_ylabel('Percentage (%)')
		ax3b.set_ylim([0.,100.])
		
		fig.savefig(freqplot,bbox_inches='tight')
		P.close(fig)
	
	
	# Length vs time and SNR vs time
	if snrplot is not None:
		fig  = P.figure(figsize=(2.*width,2.*height))
		fig.subplots_adjust(wspace=0.25,hspace=0.25)
		
		ax1  = fig.add_subplot(221)
		ax1.scatter(epochs,lengths,linewidth=0.,c='b')
		ax1.axhline(avglen,ls='--',c='r')
		ax1.axhline(medlen,ls='--',c='k')
		ax1.set_xlim([mint,maxt])
		ax1.ticklabel_format(useOffset=False)
		ax1.set_xlabel('Epoch (MJD)')
		ax1.set_ylabel('Obs. Length (min)')
		ax1.minorticks_on()
	
		ax2  = fig.add_subplot(222)
		ax2.scatter(epochs,snrs,linewidth=0.,c='r')
		ax2.axhline(avgsnr,ls='--',c='r')
		ax2.axhline(medsnr,ls='--',c='k')
		ax2.set_xlim([mint,maxt])
		ax2.ticklabel_format(useOffset=False)
		ax2.set_xlabel('Epoch (MJD)')
		ax2.set_ylim([0.,1.05*snrs.max()])
		ax2.set_ylabel('SNR')
		ax2.minorticks_on()
	
		ax3  = fig.add_subplot(223)
		ax3.scatter(epochs,nsnrs,linewidth=0.,c='g')
		ax3.axhline(avgnsnr,ls='--',c='r')
		ax3.axhline(mednsnr,ls='--',c='k')
		ax3.set_xlim([mint,maxt])
		ax3.ticklabel_format(useOffset=False)
		ax3.set_xlabel('Epoch (MJD)')
		ax3.set_ylim([0.,1.05*nsnrs.max()])
		ax3.set_ylabel('Norm. SNR (min$^{-1/2}$ MHz$^{-1/2}$)')
		ax3.minorticks_on()
		
		ax4  = fig.add_subplot(224)
		ax4b = ax4.twinx()
		mins = numpy.floor(nsnrs.min())
		maxs = numpy.ceil(nsnrs.max())
		n, bins, edges = ax4.hist(nsnrs,range=[mins,maxs],bins=30,linewidth=0.,color='m')
		ax4.axvline(avgnsnr,ls='--',c='r',label='Average')
		ax4.axvline(mednsnr,ls='--',c='k',label='Median')
		ax4.ticklabel_format(useOffset=False)
		ax4.set_ylim([0.,n.max()+1.])
		ax4.set_xlabel('Norm. SNR (min$^{-1/2}$ MHz$^{-1/2}$)')
		ax4.set_ylabel('Counts')
		ax4.legend(loc='upper right',frameon=False)
		ax4b.set_ylabel('Percentage (%)')
		ax4b.set_ylim([0.,100.*(n.max()+1.)/n.sum()])
		
		fig.savefig(snrplot,bbox_inches='tight')
		P.close(fig)

	
	# Observation characteristics
	if obschar is not None:
		fig  = P.figure(figsize=(4.*width,2.*height))
		fig.subplots_adjust(wspace=0.25,hspace=0.25)
		
		ax1  = fig.add_subplot(241)
		ax1b = ax1.twinx()
		keys = freqcnt.keys()
		keys.sort()
		vals = [freqcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		Xlab = ["%.3f" % float(keys[i]) for i in xrange(len(keys))]
		ax1.bar(X,vals,align='center',width=0.33,linewidth=0.,color='b')
		ax1.set_xlim([X.min()-1.,X.max()+1.])
		ax1.set_xticks(X)
		ax1.set_xticklabels(Xlab,rotation=45)
		ax1.set_xlabel('Frequency (MHz)')
		ax1.set_ylim([0.,numpy.array(vals).sum()])
		ax1.set_ylabel('Counts')
		ax1.yaxis.set_minor_locator(minorLocator)
		ax1b.set_ylabel('Percentage (%)')
		ax1b.set_ylim([0.,100.])
		
		ax2  = fig.add_subplot(242)
		ax2b = ax2.twinx()
		keys = bwcnt.keys()
		keys.sort()
		vals = [bwcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		ax2.bar(X,vals,align='center',width=0.33,linewidth=0.,color='r')
		ax2.set_xlim([X.min()-1.,X.max()+1.])
		ax2.set_xticks(X)
		ax2.set_xticklabels(keys,rotation=45)
		ax2.set_xlabel('Bandwidth (MHz)')
		ax2.set_ylim([0.,numpy.array(vals).sum()])
		ax2.set_ylabel('Counts')
		ax2.yaxis.set_minor_locator(minorLocator)
		ax2b.set_ylabel('Percentage (%)')
		ax2b.set_ylim([0.,100.])
		
		ax3  = fig.add_subplot(243)
		ax3b = ax3.twinx()
		keys = nbincnt.keys()
		keys.sort()
		vals = [nbincnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		ax3.bar(X,vals,align='center',width=0.33,linewidth=0.,color='g')
		ax3.set_xlim([X.min()-1.,X.max()+1.])
		ax3.set_xticks(X)
		ax3.set_xticklabels(keys,rotation=45)
		ax3.set_xlabel('Num. Phase Bins')
		ax3.set_ylim([0.,numpy.array(vals).sum()])
		ax3.set_ylabel('Counts')
		ax3.yaxis.set_minor_locator(minorLocator)
		ax3b.set_ylabel('Percentage (%)')
		ax3b.set_ylim([0.,100.])
		
		ax4  = fig.add_subplot(244)
		ax4b = ax4.twinx()
		keys = npolcnt.keys()
		keys.sort()
		vals = [npolcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		ax4.bar(X,vals,align='center',width=0.33,linewidth=0.,color='m')
		ax4.set_xlim([X.min()-1.,X.max()+1.])
		ax4.set_xticks(X)
		ax4.set_xticklabels(keys,rotation=45)
		ax4.set_xlabel('Num. Polarizations')
		ax4.set_ylim([0.,numpy.array(vals).sum()])
		ax4.set_ylabel('Counts')
		ax4.yaxis.set_minor_locator(minorLocator)
		ax4b.set_ylabel('Percentage (%)')
		ax4b.set_ylim([0.,100.])
		
		ax5  = fig.add_subplot(245)
		ax5b = ax5.twinx()
		minl = numpy.floor(lengths.min())
		maxl = numpy.ceil(lengths.max())
		n, bins, edges = ax5.hist(lengths,range=[minl,maxl],bins=30,linewidth=0.,color='c')
		ax5.ticklabel_format(useOffset=False)
		ax5.set_xlabel('Obs. Length (min)')
		ax5.set_ylim([0.,n.max()+1.])
		ax5.set_ylabel('Counts')
		ax5.yaxis.set_minor_locator(minorLocator)
		ax5b.set_ylabel('Percentage (%)')
		ax5b.set_ylim([0.,100.*(n.max()+1.)/n.sum()])
		
		ax6  = fig.add_subplot(246)
		ax6b = ax6.twinx()
		keys = nchcnt.keys()
		keys.sort()
		vals = [nchcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		ax6.bar(X,vals,align='center',width=0.33,linewidth=0.,color='y')
		ax6.set_xlim([X.min()-1.,X.max()+1.])
		ax6.set_xticks(X)
		ax6.set_xticklabels(keys,rotation=45)
		ax6.set_xlabel('Num. Freq. Channels')
		ax6.set_ylim([0.,numpy.array(vals).sum()])
		ax6.set_ylabel('Counts')
		ax6.yaxis.set_minor_locator(minorLocator)
		ax6b.set_ylabel('Percentage (%)')
		ax6b.set_ylim([0.,100.])
		
		ax7  = fig.add_subplot(247)
		ax7b = ax7.twinx()
		keys = srccnt.keys()
		keys.sort()
		vals = [srccnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		ax7.bar(X,vals,align='center',width=0.33,linewidth=0.,color='k')
		ax7.set_xlim([X.min()-1.,X.max()+1.])
		ax7.set_xticks(X)
		ax7.set_xticklabels(keys,rotation=45)
		ax7.set_xlabel('Sources')
		ax7.set_ylim([0.,numpy.array(vals).sum()])
		ax7.set_ylabel('Counts')
		ax7.yaxis.set_minor_locator(minorLocator)
		ax7b.set_ylabel('Percentage (%)')
		ax7b.set_ylim([0.,100.])
		
		ax8  = fig.add_subplot(248)
		ax8b = ax8.twinx()
		keys = bkdcnt.keys()
		keys.sort()
		vals = [bkdcnt[key] for key in keys]
		X    = numpy.arange(len(keys))
		a = ax8.bar(X,vals,align='center',width=0.33,linewidth=0.,color='0.5')
		ax8.set_xlim([X.min()-1.,X.max()+1.])
		ax8.set_xticks(X)
		ax8.set_xticklabels(keys,rotation=45)
		ax8.set_xlabel('Backends')
		ax8.set_ylim([0.,numpy.array(vals).sum()])
		ax8.set_ylabel('Counts')
		ax8.yaxis.set_minor_locator(minorLocator)
		ax8b.set_ylabel('Percentage (%)')
		ax8b.set_ylim([0.,100.])
		
		fig.savefig(obschar,bbox_inches='tight')
		P.close(fig)


	# Zapping statistics
	if zapplot is not None:
		fig  = P.figure(figsize=(2.*width,2.*height))
		fig.subplots_adjust(wspace=0.25,hspace=0.25)
		
		ax1  = fig.add_subplot(221)
		ax1.plot(epochs,nsubs,'b--',label='Total')
		ax1.scatter(epochs,nsubxs,linewidth=0.,c='r',label='Good')
		ax1.set_xlim([mint,maxt])
		ax1.set_xlabel('Epoch (MJD)')
		ax1.set_ylim([0.,nsubs.max()+1.])
		ax1.set_ylabel('Number of subintegrations')
		ax1.legend(loc='lower right',frameon=False)
		ax1.minorticks_on()
		
		ax2  = fig.add_subplot(222)
		ax2.plot(epochs,nchs,'b--',label='Total')
		ax2.scatter(epochs,nchxs,linewidth=0.,c='r',label='Good')
		ax2.set_xlim([mint,maxt])
		ax2.set_xlabel('Epoch (MJD)')
		ax2.set_ylim([0.,nchs.max()+1.])
		ax2.set_ylabel('Number of channels')
		ax2.legend(loc='lower right',frameon=False)
		ax2.minorticks_on()
		
		ax3  = fig.add_subplot(223)
		ax3.scatter(epochs,100.*zapsubs,linewidth=0.,c='b')
		ax3.axhline(100.*avgzaps,ls='--',c='r',label='Average')
		ax3.set_xlim([mint,maxt])
		ax3.set_xlabel('Epoch (MJD)')
		ax3.set_ylim([0.,100.])
		ax3.set_ylabel('Percentage of zapped subintegrations (%)')
		ax3.minorticks_on()
		
		ax4  = fig.add_subplot(224)
		ax4.scatter(epochs,100.*zapchs,linewidth=0.,c='b')
		ax4.axhline(100.*avgzapc,ls='--',c='r',label='Average')
		ax4.set_xlim([mint,maxt])
		ax4.set_xlabel('Epoch (MJD)')
		ax4.set_ylim([0.,100.])
		ax4.set_ylabel('Percentage of zapped channels (%)')
		ax4.legend(loc='upper right',frameon=False)
		ax4.minorticks_on()
		
		fig.savefig(zapplot,bbox_inches='tight')
		P.close(fig)
	
	#
	
	if logfile is not None: 
		logger.info('finished.')
		terminate_logging()
	
	return

#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	make_stats(	datadir     = args.datadir, \
			dataext     = args.dataext, \
			output      = args.output, \
			width       = args.width, \
			height      = args.height, \
			obscomb     = args.obscomb, \
			freqplot    = args.freqplot, \
			snrplot     = args.snrplot, \
			obschar     = args.obschar, \
			zapplot     = args.zapplot, \
			noplots     = args.noplots, \
			overwrite   = args.overwrite, \
			origdatadir = args.origdatadir, \
			origdataext = args.origdataext, \
			logfile     = args.logfile, \
			dpi         = args.dpi )
			
	goodbye()
