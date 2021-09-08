import os
import sys
import glob
import numpy
import commands
import argparse

try:
	import psrchive as p
	from misc_tools import *
	from plotone import extract_data
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass


# make_templates.py: script for constructing standard profiles from Nancay pulsar timing data.
# Author:            Lucas Guillemot
# Last update:       22 Avr 2015
# Version:           1.74




# Some default declarations
DEF_CLK_CORR        = '/usr/local/src/tempo2/T2runtime/clock/ncyobs2obspm.clk'
DEF_DATA_DIR        = '.'
DEF_DATA_EXT        = 'DFTp'
DEF_FREQ            = 1484.0
DEF_FTOL            = 25.
DEF_BW              = 512.0
DEF_BTOL            = 0.
DEF_OBSNCHAN        = 16
DEF_BACKEND         = 'NUPPI'
DEF_SCALE           = 'ReferenceFluxDensity'
DEF_MAXSUM          = 1.e6
DEF_NPROF           = 10
DEF_ADDED           = 'summed.prof'
DEF_SMOOTHED        = 'smoothed.prof'
DEF_OUTPUT_INFO     = None
DEF_OUTPUT_ADDED    = None
DEF_OUTPUT_SMOOTHED = None
DEF_PLOT1           = 'templates.png'
DEF_PLOT2           = 'snrplot.png'
DEF_PLOT3           = 'snrplot2.png'
DEF_LOGFILE         = None
DEF_DPI             = 100

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for constructing standard profiles from Nancay pulsar timing data.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-tmin',type=float,default=0.,help='Minimum MJD (default: 0).')
	parser.add_argument('-tmax',type=float,default=99999.,help='Maximum MJD (default: 99999).')
	parser.add_argument('-freq',type=float,default=DEF_FREQ,help='Observations at frequencies different from that value +/- ftol will be skipped. If 0, will skip this test (default: %f).' % DEF_FREQ)
	parser.add_argument('-ftol',type=float,default=DEF_FTOL,help='Tolerance in frequency (default: %f).' % DEF_FTOL)
	parser.add_argument('-bw',type=float,default=DEF_BW,help='Observations with bandwidths different from that value +/- btol will be skipped. If 0, will skip this test (default: %f).' % DEF_BW)
	parser.add_argument('-btol',type=float,default=DEF_BTOL,help='Tolerance in bandwidth (default: %f).' % DEF_BTOL)
	parser.add_argument('-backend',type=str,default=DEF_BACKEND,help='Observations with backend different from that value will be skipped. If 0, will skip this test (default: \"%s\").' % DEF_BACKEND)
	parser.add_argument('-obsnchan',type=int,default=DEF_OBSNCHAN,help='Observations with obsnchan parameter different from that value will be skipped. If 0, will skip this test (default: %d).' % DEF_OBSNCHAN)
	parser.add_argument('-scale',type=str,default=DEF_SCALE,help='Observations with scale parameter different from that value will be skipped. If 0, will skip this test (default: \"%s\").' % DEF_SCALE)
	parser.add_argument('-maxsum',type=float,default=DEF_MAXSUM,help='Observations with parameter all:sum larger than this value will be skipped. If 0, will skip this test (default: %le).' % DEF_MAXSUM)
	parser.add_argument('-nprof',type=int,default=DEF_NPROF,help='If 0, will concatenate all the profiles. Else, will concatenate this number of profiles (default: %d).' % DEF_NPROF)
	parser.add_argument('-addedprof',type=str,default=DEF_ADDED,help='Name of the output summed profile (default: \"%s\").' % DEF_ADDED)
	parser.add_argument('-smoothedprof',type=str,default=DEF_SMOOTHED,help='Name of the output smoothed summed profile (default: \"%s\").' % DEF_SMOOTHED)
	parser.add_argument('-forcealign',action='store_true',default=False,help='Whether or not the phase alignment between profile will be forced in psradd (default: False).')
	parser.add_argument('-output_info',type=str,default=DEF_OUTPUT_INFO,help='Output some information on frequencies, backends, bandwidths, etc. to this file (default: None).')
	parser.add_argument('-output_added',type=str,default=DEF_OUTPUT_ADDED,help='Output the summed profile to this file (default: None).')
	parser.add_argument('-output_smoothed',type=str,default=DEF_OUTPUT_SMOOTHED,help='Output the smoothed profile to this file (default: None).')
	parser.add_argument('-clk_corr_file',type=str,default=DEF_CLK_CORR,help='Path to the tempo2 clock correction file for this telescope and backend (default: \"%s\").' % DEF_CLK_CORR)
	parser.add_argument('-noclock',action='store_true',default=False,help='If set, will not read the clock correction file (default: False).')
	parser.add_argument('-noplots',action='store_true',default=False,help='If set, disable creation of summary plots (default: False).')
	parser.add_argument('-plot1',type=str,default=DEF_PLOT1,help='Name of the output summary plot of templates (default: \"%s\").' % DEF_PLOT1)
	parser.add_argument('-plot2',type=str,default=DEF_PLOT2,help='Name of the output summary plot of snr vs number of concatenated files (default: \"%s\").' % DEF_PLOT2)
	parser.add_argument('-plot3',type=str,default=DEF_PLOT3,help='Name of the output summary plot of snr vs square root of integration time (default: \"%s\").' % DEF_PLOT3)
	parser.add_argument('-sortsnr',action='store_true',default=False,help='If set, light curves will be sorted by SNR in the summary plot (default: False).')
	parser.add_argument('-maxline',action='store_true',default=False,help='If set, a dashed line at the maximum of the smoothed profile will be drawn in the summary plot (default:False).')
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not added and smoothed profiles will be overwritten (default: False).')
	parser.add_argument('-shiftmax',action='store_true',default=False,help='Rotate the smoothed profile (and the added profile accordingly) so that the maximum falls at 0 (default: False).')
	parser.add_argument('-nosnrfit',action='store_true',default=False,help='If set, will not fit the snr vs sqrt(time) curve (default: False).')
	parser.add_argument('-automax',action='store_true',default=False,help='If set, will automatically build a profile with the optimal SNR (default: False).')
	parser.add_argument('-logfile',type=str,default=DEF_LOGFILE,help='Path to an output log file.')
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	return parser

#

def make_templates(	datadir         = DEF_DATA_DIR, \
			dataext         = DEF_DATA_EXT, \
			tmin            = 0., \
			tmax            = 99999., \
			freq            = DEF_FREQ, \
			ftol            = DEF_FTOL, \
			bw              = DEF_BW, \
			btol            = DEF_BTOL, \
			obsnchan        = DEF_OBSNCHAN, \
			backend         = DEF_BACKEND, \
			scale           = DEF_SCALE, \
			maxsum          = DEF_MAXSUM, \
			nprof           = DEF_NPROF, \
			addedprof       = DEF_ADDED, \
			smoothedprof    = DEF_SMOOTHED, \
			forcealign      = False, \
			output_info     = DEF_OUTPUT_INFO, \
			output_added    = DEF_OUTPUT_ADDED, \
			output_smoothed = DEF_OUTPUT_SMOOTHED, \
			clk_corr_file   = DEF_CLK_CORR, \
			noclock         = False, \
			noplots         = False, \
			plot1           = DEF_PLOT1, \
			plot2           = DEF_PLOT2, \
			plot3           = DEF_PLOT3, \
			sortsnr         = False, \
			maxline         = False, \
			overwrite       = False, \
			shiftmax        = False, \
			nosnrfit        = False, \
			logfile         = DEF_LOGFILE, \
			**kwargs ):
	
	# Make some initial checks
	if logfile is not None:
		locargs = locals()
		logger  = initialize_logging(os.path.basename(__file__),logfile=logfile)
		logger.info('running make_templates with arguments:')
		logger.info(locargs)

	if not os.path.exists(datadir):
		if logfile is not None: logger.error('data directory \"%s\" does not exist!' % datadir)
		raise ExistError('Error: data directory does not exist!')
		
	if not noclock and not os.path.exists(clk_corr_file):
		if logfile is not None: logger.error('clock correction file \"%s\" does not exist!' % clk_corr_file)
		raise ExistError('Error: clock correction file does not exist!')
	
	if dataext[0] == '.': dataext = dataext[1:]
		
	files  = glob.glob(os.path.join(datadir,'*.' + dataext))
	files.sort()
	Nfiles = len(files)
	if Nfiles == 0:
		if logfile is not None: logger.error('no data files selected! Check data directory and extension: \"%s\" \"%s\".' % (datadir,dataext))
		raise NoFilesError('Error: no data files selected! Check data directory and extension.')
	
	if forcealign is False and not noclock:
		tmin2, tmax2 = get_clk_corr_range(clk_corr_file)
		tmin         = max(tmin, tmin2)
		tmax         = min(tmax, tmax2)
	
	if os.path.exists(addedprof):
		if overwrite: os.unlink(addedprof)
		else:
			if logfile is not None: logger.error('added profile \"%s\" already exists.' % addedprof)
			raise AlreadyExistError('Added profile already exists. Exiting...')
	
	if os.path.exists(smoothedprof):
		if overwrite: os.unlink(smoothedprof)
		else:
			if logfile is not None: logger.error('smoothed profile \"%s\" already exists.' % smoothedprof)
			raise AlreadyExistError('Smoothed profile already exists. Exiting...')
			
	if '/' in addedprof:
		paths = addedprof.split('/')
		path  = ''
		for elem in paths[:-1]:
			path = os.path.join(path,elem)
			if not os.path.isdir(path): os.mkdir(path)
			
	if '/' in smoothedprof:
		paths = smoothedprof.split('/')
		path  = ''
		for elem in paths[:-1]:
			path = os.path.join(path,elem)
			if not os.path.isdir(path): os.mkdir(path)
	
	if output_info is not None and os.path.exists(output_info):
		if overwrite: os.unlink(output_info)
		else:
			if logfile is not None: logger.error('output file \"%s\" already exists.' % output_info)
			raise AlreadyExistError('Output information file already exists. Exiting...')
			
	if output_added is not None and os.path.exists(output_added):
		if overwrite: os.unlink(output_added)
		else:
			if logfile is not None: logger.error('output file \"%s\" already exists.' % output_added)
			raise AlreadyExistError('Output added profile already exists. Exiting...')
			
	if output_smoothed is not None and os.path.exists(output_smoothed):
		if overwrite: os.unlink(output_smoothed)
		else:
			if logfile is not None: logger.error('output file \"%s\" already exists.' % output_smoothed)
			raise AlreadyExistError('Output smoothed profile already exists. Exiting...')
	
	if os.path.splitext(plot1)[1] != os.path.splitext(plot2)[1]:
		if logfile is not None: logger.error('plots must have the same extension (had \"%s\" and \"%s\").' % (plot1,plot2))
		raise MiscError('Plots must have the same extension! Exiting...')

	if os.path.splitext(plot1)[1] != os.path.splitext(plot3)[1]:
		if logfile is not None: logger.error('plots must have the same extension (had \"%s\" and \"%s\").' % (plot1,plot3))
		raise MiscError('Plots must have the same extension! Exiting...')

	
	# Select data based on frequency, epoch, and instrument information
	goodfiles       = []
	snrs            = []
	all_freqs       = {}
	all_bws         = {}
	all_obsnchans   = {}
	all_backends    = {}
	other_freqs     = {}
	other_bws       = {}
	other_obsnchans = {}
	other_backends  = {}
	print 'Selecting and checking the files. Please wait...'
	
	for i, fichier in zip(range(Nfiles),files):
		progress_bar(float(i+1)/float(Nfiles),25)
	
		# Make sure the file is a valid psrchive file
		try:
			arch = load_archive(fichier)
		except:
			continue
			
		sumw       = get_sum_weights_open(arch)
		epoch      = get_epoch_open(arch)
		
		freq2, bw2 = get_frequency_info_open(arch)
		if not all_freqs.has_key(freq2): all_freqs[freq2] = 1
		else: all_freqs[freq2] += 1
		
		if not all_bws.has_key(bw2): all_bws[bw2] = 1
		else: all_bws[bw2] += 1
		
		try:
			# Why this try? Because LuMP files do not seem to have this parameter in their header
			obsnchan2  = get_obsnchan(fichier)
		except:
			if logfile is not None: logger.warn('Unable to determine the obsnchan parameter for file \"%s\".' % fichier)
			print 'Warning: unable to determine the obsnchan parameter for file \"%s\".' % fichier
			obsnchan2  = -1
		
		if not all_obsnchans.has_key(obsnchan2): all_obsnchans[obsnchan2] = 1
		else: all_obsnchans[obsnchan2] += 1
		
		try:
			backend2   = get_backend(fichier)
		except:
			if logfile is not None: logger.warn('Unable to determine the backend parameter for file \"%s\".' % fichier)
			print 'Warning: unable to determine the backend parameter for file \"%s\".' % fichier
			backend2   = 'unknown'
		
		if not all_backends.has_key(backend2): all_backends[backend2] = 1
		else: all_backends[backend2] += 1
		
		try:
			scale2     = get_scale_open(arch)
		except:
			if logfile is not None: logger.warn('Unable to determine the scale parameter for file \"%s\".' % fichier)
			print 'Warning: unable to determine the scale parameter for file \"%s\".' % fichier
			scale2     = 'unknown'
		
		try:
			sum_bins   = get_sum_bins(fichier)
		except:
			if logfile is not None: logger.warn('Unable to determine the sum bins parameter for file \"%s\".' % fichier)
			print 'Warning: unable to determine the sum bins parameter for file \"%s\".' % fichier
			sum_bins   = -1
		
		dedisp     = get_dedispersed(fichier)
		
				
		# Check that the file is not empty
		if sumw == 0.0:
			if logfile is not None: logger.debug('Skipping file \"%s\" with sum(weights) == 0.' % (os.path.basename(fichier)))
			print 'Skipping file \"%s\" with sum(weights) == 0.' % (os.path.basename(fichier))
			continue
	
		# Weak test for NaN values (weak since we do not test all the data)
		amps  = get_first_profile_open(arch)
		if numpy.isnan(amps).any():
			if logfile is not None: logger.debug('Skipping file \"%s\" with NaN values.' % (os.path.basename(fichier)))
			print 'Skipping file \"%s\" with NaN values.' % (os.path.basename(fichier))
			continue
	
		# Check that the epoch is in the requested range
		if epoch < tmin:      
			if logfile is not None: logger.debug('Skipping file \"%s\" with epoch %.1f < %.1f.' % (os.path.basename(fichier),epoch,tmin))
			print 'Skipping file \"%s\" with epoch %.1f < %.1f.' % (os.path.basename(fichier),epoch,tmin)
			continue
		if epoch > tmax:      
			if logfile is not None: logger.debug('Skipping file \"%s\" with epoch %.1f > %.1f.' % (os.path.basename(fichier),epoch,tmax))
			print 'Skipping file \"%s\" with epoch %.1f > %.1f.' % (os.path.basename(fichier),epoch,tmax)
			continue
		
		# Check that the frequency and bandwidth are in the requested range
		dfreq      = numpy.abs(freq - freq2)
		dbw        = numpy.abs(bw - bw2)
		if freq != 0. and dfreq > ftol:
			if logfile is not None: logger.debug('Skipping file \"%s\" with freq %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),freq2,freq,ftol))
			print 'Skipping file \"%s\" with freq %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),freq2,freq,ftol)
			if not other_freqs.has_key(freq2): other_freqs[freq2] = 1
			else: other_freqs[freq2] += 1
			continue
		if bw != 0. and dbw > btol:
			if logfile is not None: logger.debug('Skipping file \"%s\" with bandwidth %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),bw2,bw,btol))
			print 'Skipping file \"%s\" with bandwidth %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),bw2,bw,btol)
			if not other_bws.has_key(bw2): other_bws[bw2] = 1
			else: other_bws[bw2] += 1
			continue
		
		# Check that obsnchan parameter is as expected
		# Note: this is done to make sure than LEAP mode and normal mode observations are not combined at this stage.
		# Why not using nchan instead? Because it is set to 1 if the data file has been scrunched!
		if obsnchan != 0 and obsnchan2 != obsnchan:
			if logfile is not None: logger.debug('Skipping file \"%s\" with obsnchan %d != %d.' % (os.path.basename(fichier),obsnchan2,obsnchan))
			print 'Skipping file \"%s\" with obsnchan %d != %d.' % (os.path.basename(fichier),obsnchan2,obsnchan)
			if not other_obsnchans.has_key(obsnchan2): other_obsnchans[obsnchan2] = 1
			else: other_obsnchans[obsnchan2] += 1
			continue
		
		# Check that the backend matches the requested one
		if backend != '0' and backend2 != backend:
			if logfile is not None: logger.debug('Skipping file \"%s\" with backend %s != %s.' % (os.path.basename(fichier),backend2,backend))
			print 'Skipping file \"%s\" with backend %s != %s.' % (os.path.basename(fichier),backend2,backend)
			if not other_backends.has_key(backend2): other_backends[backend2] = 1
			else: other_backends[backend2] += 1
			continue
		
		# Check that the data units are as expected
		if scale != '0' and scale2 != scale:
			if logfile is not None: logger.debug('Skipping file \"%s\" with scale %s != %s.' % (os.path.basename(fichier),scale2,scale))
			print 'Skipping file \"%s\" with scale %s != %s.' % (os.path.basename(fichier),scale2,scale)
			continue
		
		# This test seems to eliminate a number of badly calibrated files
		if maxsum != 0. and sum_bins > maxsum:
			if logfile is not None: logger.debug('Skipping file \"%s\" with all:sum %.3le > %.3le.' % (os.path.basename(fichier),sum_bins,maxsum))
			print 'Skipping file \"%s\" with all:sum %.3le > %.3le.' % (os.path.basename(fichier),sum_bins,maxsum)
			continue
		
		# If forced alignment is not enabled, make sure the data are dedispersed (otherwise: random alignment)
		if not forcealign and not dedisp:
			if logfile is not None: logger.debug('Skipping file \"%s\": not dedispersed (force alignment mode disabled).' % os.path.basename(fichier))
			print 'Skipping file \"%s\": not dedispersed (force alignment mode disabled).' % os.path.basename(fichier)
			continue
		
		#
		
		goodfiles.append(fichier)
		snr    = get_snr(fichier)
		snrs.append(snr)
	
	#
	
	if output_info is not None:
		outf = open(output_info,'w+')
		outf.write('Frequencies: %s\n' % all_freqs)
		outf.write('Bandwidths:  %s\n' % all_bws)
		outf.write('Obsnchans:   %s\n' % all_obsnchans)
		outf.write('Backends:    %s\n' % all_backends)
		outf.close()
	
	if logfile is not None: logger.debug('Other frequencies found (and number of entries): %s' % other_freqs)
	print '\nOther frequencies found (and number of entries):'
	print other_freqs
	if logfile is not None: logger.debug('Other bandwidths found (and number of entries): %s' % other_bws)
	print '\nOther bandwidths found (and number of entries):'
	print other_bws
	if logfile is not None: logger.debug('Other obsnchan values found (and number of entries): %s' % other_obsnchans)
	print '\nOther obsnchan values found (and number of entries):'
	print other_obsnchans
	if logfile is not None: logger.debug('Other backends found (and number of entries): %s' % other_backends)
	print '\nOther backends found (and number of entries):'
	print other_backends
	
	#
	
	Nfiles = len(goodfiles)	
	if Nfiles == 0:
		if logfile is not None: logger.error('no data files selected! Exiting here.')
		raise NoFilesError('No data files selected! Exiting here.')
	
	if logfile is not None: logger.debug('Selected %d files.' % (Nfiles))
	print '\nSelected %d files.' % (Nfiles)
	snrs   = numpy.array(snrs)
	idx    = numpy.argsort(snrs)[::-1]
	concat = []
	snrs2  = []
	totlen = []

	# Concatenate the data for the highest SNR profiles and keep track of the SNR at each summation step
	if nprof == 0: nprof = Nfiles
	elif nprof > Nfiles:
		if logfile is not None: logger.warn('requested concatenation of %d profiles, but only %d files were selected. Will add up all selected profiles together.' % (nprof,Nfiles))
		print 'Warning: requested concatenation of %d profiles, but only %d files were selected. Will add up all selected profiles together.' % (nprof,Nfiles)
		nprof = Nfiles
	
	if logfile is not None: logger.debug('%d profiles with the best SNRs:' % nprof)
	print '\n%d profiles with the best SNRs:' % nprof
	for i in idx[:nprof]:
		if logfile is not None: logger.debug('%s %s' % (goodfiles[i], snrs[i]))
		print goodfiles[i], snrs[i]
		concat.append(goodfiles[i])
	
	#
	
	flags = ['-R','-T']
	if forcealign: flags.append('-P')
	
	snrprev   = 0.
	for i in range(len(concat)):
		if logfile is not None: logger.debug('adding file \"%s\"...' % concat[i])
		print '\nAdding file \"%s\"...' % concat[i]
		if i == 0: psraddfiles = [concat[i]]
		else:      psraddfiles = [concat[i],addedprof]
		
		# psradd sometimes complains about the "Predictor" not being a "TEMPO polyco". Try to prevent this from happening!
		parf = extract_parfile(concat[i])
		parf, status = fix_parfile(parf)
		if status == True:
			if logfile is not None: logger.debug('Possible Tempo predictor issue prevented here.')
			print 'Possible Tempo predictor issue prevented here.'
			write_parfile(parf,'CleanParFile.par')
			flags.append('-E CleanParFile.par')
		
		flags_line = ''
		for flag in flags: flags_line += ' ' + flag
		
		try:
			add_files(psraddfiles,addedprof,flags_line)
			if logfile is not None: logger.debug('Added files %s together.' % psraddfiles)
		except PsrchiveError, e:
			if logfile is not None: 
				logger.error(e.msg)
				logger.error('Command: %s' % e.cmd)
			print 'Failed to create file \"%s\".' % addedprof
		
		if os.path.exists('CleanParFile.par'): os.unlink('CleanParFile.par')
		
		snr     = get_snr(addedprof)
		dsnr    = snr - snrprev
		snrs2.append(snr)
		snrprev = snr
		if logfile is not None: logger.debug('(Obs #%d/%d) Total SNR at this stage: %.1f. Difference: %.1f' % (i+1,len(concat),snr,dsnr))
		print '(Obs #%d/%d) Total SNR at this stage: %.1f. Difference: %.1f' % (i+1,len(concat),snr,dsnr)
		length  = get_length(addedprof)
		totlen.append(length)
	
	xs   = numpy.arange(1.,len(snrs2)+1.)
	nmax = xs[numpy.argmax(snrs2)]
	
	## IMPORTANT NOTE: THIS COMMAND IS USEFUL FOR CHECKING THE PROCEDURE: psradd -T -r 1484 -o tmp.prof -v *.DFTp
		
	
	# Finally, smooth the profile using psrsmooth
	flags = ['-n','-W']
	flags_line = ''
	for flag in flags: flags_line += ' ' + flag
	
	try:
		smooth_file(addedprof,smoothedprof,flags_line)
		if logfile is not None: logger.debug('Smoothed file \"%s\" to \"%s\".' % (addedprof,smoothedprof))
		print '\nSmoothed file \"%s\" to \"%s\".' % (addedprof,smoothedprof)
	except PsrchiveError, e:
		if logfile is not None: 
			logger.error(e.msg)
			logger.error('Command: %s' % e.cmd)
		print '\nFailed to create file \"%s\".' % smoothedprof
	
	
	# Shift the added and smoothed profiles
	if shiftmax is True:
		shift = get_max_shift(smoothedprof)
		if logfile is not None: logger.debug('will rotate added and smoothed profile by %f in phase...' % shift)
		print '\nWill rotate added and smoothed profile by %f in phase...' % shift
		
		try:
			rotate_profile(addedprof,shift)
		except PsrchiveError, e:
			if logfile is not None: 
				logger.error(e.msg)
				logger.error('Command: %s' % e.cmd)
			print 'Failed to rotate file \"%s\".' % addedprof
		
		try:
			rotate_profile(smoothedprof,shift)
		except PsrchiveError, e:
			if logfile is not None: 
				logger.error(e.msg)
				logger.error('Command: %s' % e.cmd)
			print 'Failed to rotate file \"%s\".' % smoothedprof
	else:
		shift = 0.
	
	
	# Output the profiles to ascii files
	if output_added is not None:
		if logfile is not None: logger.debug('will save added profile to file \"%s\"...' % output_added)
		print '\nWill save added profile to file \"%s\"...' % output_added
		
		try:
			output_profile(addedprof,output_added)
		except PsrchiveError, e:
			if logfile is not None: 
				logger.error(e.msg)
				logger.error('Command: %s' % e.cmd)
			print 'Failed to make an ascii file from \"%s\".' % addedprof
		
	if output_smoothed is not None:
		if logfile is not None: logger.debug('will save smoothed profile to file \"%s\"...' % output_smoothed)
		print '\nWill save smoothed profile to file \"%s\"...' % output_smoothed
		
		try:
			output_profile(smoothedprof,output_smoothed)
		except PsrchiveError, e:
			if logfile is not None: 
				logger.error(e.msg)
				logger.error('Command: %s' % e.cmd)
			print 'Failed to make an ascii file from \"%s\".' % smoothedprof
	
	
	# Make some summary plots
	if noplots: 
		if logfile is not None: logger.info('no plots requested. Ending here.')
		return nmax
	
	import matplotlib
	pext = os.path.splitext(plot1)[1]
	if pext == '.ps': 
		ps = True
		if matplotlib.get_backend() == 'ps': pass
		else:                                matplotlib.use('ps')
	else: 
		ps = False
		if matplotlib.get_backend() == 'agg': pass
		else:                                 matplotlib.use('agg')
	from matplotlib import pyplot as P
	from matplotlib.ticker import FormatStrFormatter
	P.rcParams["legend.fontsize"] = 11
	
	if kwargs.has_key('dpi'): dpi = kwargs['dpi']
	else:                     dpi = DEF_DPI
	
	if not sortsnr: concat.sort()
	
	fig    = P.figure()
	ax     = fig.add_subplot(111)
	y      = 0.
	dy     = 0.5
	ys     = []
	labels = []
	jinit  = 1e6
	j      = jinit
	
	for fichier in concat:
		xdata, ydata, extent = extract_data(fichier, 'phase', 'intens', rotation=-shift)
		ydata -= ydata.min()
		ydata /= ydata.max()
		ydata += y
		
		xdata  = numpy.append(xdata,xdata[:len(xdata)/2]+1.)
		ydata  = numpy.append(ydata,ydata[:len(ydata)/2])
		
		ax.fill_between(xdata,ydata,y,facecolor='w',lw=0.,zorder=j)
		ax.plot(xdata,ydata,c='k',zorder=j+1)
		ys.append(y)
		
		epoch = get_epoch(fichier)
		snr   = get_snr(fichier)
		
		labels.append('MJD %.1f, SNR = %.1f' % (epoch,snr))
		y   += dy
		j   -= 2
	
	y += dy
	dy = 1.
	for fichier in [addedprof,smoothedprof]:
		xdata, ydata, extent = extract_data(fichier, 'phase', 'intens')
		ydata -= ydata.min()
		ydata /= ydata.max()
		ydata += y
		
		xdata  = numpy.append(xdata,xdata[:len(xdata)/2]+1.)
		ydata  = numpy.append(ydata,ydata[:len(ydata)/2])		
		
		ax.plot(xdata,ydata,c='r')
		ys.append(y)
		y   += dy
		
	labels.append('Summed profile, SNR = %.1f' % get_snr(addedprof))
	labels.append('Smoothed summed profile, SNR = %.1f' % get_snr(smoothedprof))
	
	if maxline: 
		arch     = load_archive(smoothedprof)
		arch.remove_baseline()
		prof     = arch.get_data()[0][0][0]
		idx      = numpy.argmax(prof)
		xmaxline = numpy.linspace(0.,1.,len(prof))[idx]
		ax.axvline(xmaxline,linestyle='--',color='b',zorder=jinit+1)
		if xmaxline+1.<1.5: ax.axvline(xmaxline+1.,linestyle='--',color='b',zorder=jinit+1)
	
	ax.spines['left'].set_color('none')
	ax.spines['right'].set_color('none')
	ax.spines['top'].set_color('none')
	ax.set_xlabel('Pulse Phase')
	ax.set_ylabel('Intensity (a.u.)')
	ax.xaxis.set_ticks_position('bottom')
	ax.yaxis.set_tick_params(length=0.)
	ax.set_xlim([0.,1.5])
	xlim0, xlim1 = ax.get_xlim()
	ylim0, ylim1 = ax.get_ylim()
	P.setp(ax.get_yticklabels(),visible=False)
	
	ax2 = ax.twinx()
	ax2.yaxis.tick_right()
	ax2.yaxis.set_tick_params(length=0.)
	ys  = 0.25 + numpy.array(ys)
	ax2.set_yticks(ys)
	ax2.set_yticklabels(labels)
	ax2.set_ylim([ylim0,ylim1])
	
	if forcealign: ax.text(0.5*(xlim0+xlim1),ylim1-0.025*(ylim1-ylim0),'Force alignment enabled (\'-P\' flag in psradd)',ha='center',va='center')
	
	fig.set_size_inches(8.,0.67*(len(concat)+2))
	if ps: fig.savefig(plot1)
	else:  fig.savefig(plot1,bbox_inches='tight',dpi=dpi)
	P.close(fig)
	
	# 
	
	fig  = P.figure(figsize=(8,6))
	ax   = fig.add_subplot(111)
	ax.plot(xs,snrs2,'o-')
	ax.axvline(nmax,ls='--',c='r')
	
	ax.set_xlabel('Number of profiles added')
	ax.set_ylabel('SNR of concatenated profile')
	
	ax.set_xlim([0.75,len(snrs2)+0.25])
	xlim0, xlim1 = ax.get_xlim()
	ylim0, ylim1 = ax.get_ylim()
	ax.text(0.5*(xlim0+xlim1),ylim1-0.05*(ylim1-ylim0),'Best SNR found for N = %d' % nmax,ha='center',va='center')
	
	if ps: fig.savefig(plot2)
	else:  fig.savefig(plot2,bbox_inches='tight',dpi=dpi)
	P.close(fig)
	
	#

	fig     = P.figure(figsize=(8,6))
	ax      = fig.add_subplot(111)
	ax.plot(totlen,snrs2,'o-')
	
	ax.set_xscale('log')
	ax.set_xlabel('Total integration time (s)')
	ax.set_yscale('log')
	ax.set_ylabel('SNR of concatenated profile')
	
	deltax  = numpy.log10(totlen).max() - numpy.log10(totlen).min()
	xl      = numpy.log10(totlen).min() - 0.1 * deltax
	xr      = numpy.log10(totlen).max() + 0.1 * deltax
	ax.set_xlim([numpy.power(10.,xl),numpy.power(10.,xr)])
	
	deltay  = numpy.log10(snrs2).max() - numpy.log10(snrs2).min()
	yl      = numpy.log10(snrs2).min() - 0.1 * deltay
	yr      = numpy.log10(snrs2).max() + 0.1 * deltay
	ax.set_ylim([numpy.power(10.,yl),numpy.power(10.,yr)])
	
	ax.xaxis.set_minor_formatter(FormatStrFormatter("%d"))
	ax.yaxis.set_minor_formatter(FormatStrFormatter("%d"))
	ax.tick_params(which='major',length=8)
	ax.tick_params(which='minor',length=4,labelsize=8)
	for label in ax.get_xmajorticklabels(): label.set_rotation(45.)
	for label in ax.get_xminorticklabels(): label.set_rotation(45.)
	
	
	if not nosnrfit:
		try:
			polyfit = numpy.polyfit(numpy.log10(totlen),numpy.log10(snrs2),1,full=True)
			a       = polyfit[0][0]
			b       = numpy.power(10.,polyfit[0][1])
			print '\nBest-fit of the snr vs time curve: b * (time)**a with'
			print 'a = %.3le and b = %.3le' % (a,b)
			print 'Chi-square residuals: %.3f\n' % polyfit[1][0] 
			yfit    = b*numpy.power(totlen,a)
			ax.plot(totlen,yfit,'--',label='Best fit (coeff = %.3f)' % a)
			ax.legend(loc='lower center')
		except:
			pass
	
	if ps: fig.savefig(plot3)
	else:  fig.savefig(plot3,bbox_inches='tight',dpi=dpi)
	P.close(fig)
	
	#
	
	if logfile is not None: 
		logger.info('finished.')
		terminate_logging()
	return nmax
			
#


if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	if not args.automax:
		make_templates(	datadir         = args.datadir, \
				dataext         = args.dataext, \
				tmin            = args.tmin, \
				tmax            = args.tmax, \
				freq            = args.freq, \
				ftol            = args.ftol, \
				bw              = args.bw, \
				btol            = args.btol, \
				backend         = args.backend, \
				obsnchan        = args.obsnchan, \
				scale           = args.scale, \
				maxsum          = args.maxsum, \
				nprof           = args.nprof, \
				addedprof       = args.addedprof, \
				smoothedprof    = args.smoothedprof, \
				forcealign      = args.forcealign, \
				output_info     = args.output_info, \
				output_added    = args.output_added, \
				output_smoothed = args.output_smoothed, \
				clk_corr_file   = args.clk_corr_file, \
				noclock         = args.noclock, \
				noplots         = args.noplots, \
				plot1           = args.plot1, \
				plot2           = args.plot2, \
				plot3           = args.plot3, \
				sortsnr         = args.sortsnr, \
				maxline         = args.maxline, \
				overwrite       = args.overwrite, \
				shiftmax        = args.shiftmax, \
				nosnrfit        = args.nosnrfit, \
				logfile         = args.logfile, \
				dpi             = args.dpi )
	else:
		nmax = make_templates( 	datadir         = args.datadir, \
					dataext         = args.dataext, \
					tmin            = args.tmin, \
					tmax            = args.tmax, \
					freq            = args.freq, \
					ftol            = args.ftol, \
					bw              = args.bw, \
					btol            = args.btol, \
					obsnchan        = args.obsnchan, \
					backend         = args.backend, \
					scale           = args.scale, \
					maxsum          = args.maxsum, \
					nprof           = 0, \
					addedprof       = args.addedprof, \
					smoothedprof    = args.smoothedprof, \
					forcealign      = args.forcealign, \
					output_info     = args.output_info, \
					output_added    = args.output_added, \
					output_smoothed = args.output_smoothed, \
					clk_corr_file   = args.clk_corr_file, \
					noclock         = args.noclock, \
					noplots         = True, \
					plot1           = args.plot1, \
					plot2           = args.plot2, \
					plot3           = args.plot3, \
					sortsnr         = args.sortsnr, \
					maxline         = args.maxline, \
					overwrite       = args.overwrite, \
					shiftmax        = args.shiftmax, \
					nosnrfit        = args.nosnrfit, \
					logfile         = args.logfile, \
					dpi             = args.dpi )
		
		make_templates(	datadir         = args.datadir, \
				dataext         = args.dataext, \
				tmin            = args.tmin, \
				tmax            = args.tmax, \
				freq            = args.freq, \
				ftol            = args.ftol, \
				bw              = args.bw, \
				btol            = args.btol, \
				obsnchan        = args.obsnchan, \
				backend         = args.backend, \
				scale           = args.scale, \
				maxsum          = args.maxsum, \
				nprof           = nmax, \
				addedprof       = args.addedprof, \
				smoothedprof    = args.smoothedprof, \
				forcealign      = args.forcealign, \
				output_info     = args.output_info, \
				output_added    = args.output_added, \
				output_smoothed = args.output_smoothed, \
				clk_corr_file   = args.clk_corr_file, \
				noclock         = args.noclock, \
				noplots         = args.noplots, \
				plot1           = args.plot1, \
				plot2           = args.plot2, \
				plot3           = args.plot3, \
				sortsnr         = args.sortsnr, \
				maxline         = args.maxline, \
				overwrite       = True, \
				shiftmax        = args.shiftmax, \
				nosnrfit        = args.nosnrfit, \
				logfile         = args.logfile, \
				dpi             = args.dpi )
	
	goodbye()
