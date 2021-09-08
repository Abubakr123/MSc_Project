import os
import sys
import glob
import numpy
import scipy.stats as s
import argparse
import commands

try:
	import psrchive as p
	from misc_tools import *
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass


# make_toas.py: script for producing times of arrival from Nancay pulsar timing data.
# Author:       Lucas Guillemot
# Last update:  19 Dec 2014
# Version:      1.47




# Some default declarations
DEF_DATA_DIR       = '.'
DEF_DATA_EXT       = 'DFTp'
DEF_TOA_FILE       = 'TOAs.tim'
DEF_FREQ           = None
DEF_FTOL           = 50.
DEF_BW             = None
DEF_BTOL           = 0.
DEF_OBSNCHAN       = None
DEF_BACKEND        = None
DEF_ALGORITHM      = 'PGS'
ALGO_CHOICES       = ['PGS','GIS','PIS','ZPS','SIS','FDM','COF','RVM']
DEF_FORMAT         = 'tempo2'
FORMAT_CHOICES     = ['parkes','tempo2','itoa','princeton']
DEF_VAPOPTIONS     = []
DEF_OBSCODE        = None
DEF_PLOT_DIR       = '.'
DEF_PLOT_SUFFIX    = '_residuals.png'
DEF_LISTRES        = None
DEF_WIDTH          = 8.
DEF_HEIGHT         = 8.
DEF_LOGFILE        = None
DEF_DPI            = 100

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for producing times of arrival from Nancay pulsar timing data.')
	parser.add_argument('-template',type=str,required=True,nargs='*',help='Template or list of templates to use for producing TOAs.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-toafile',type=str,default=DEF_TOA_FILE,help='Name of output TOA file (default: \"%s\").' % DEF_TOA_FILE)
	parser.add_argument('-tmin',type=float,default=0.,help='Minimum MJD (default: 0).')
	parser.add_argument('-tmax',type=float,default=99999.,help='Maximum MJD (default: 99999).')
	parser.add_argument('-freq',type=float,default=DEF_FREQ,help='Observations at frequencies different from that value +/- ftol will be skipped. If None, skip frequency selection (default: None).')
	parser.add_argument('-ftol',type=float,default=DEF_FTOL,help='Tolerance in frequency (default: %f).' % DEF_FTOL)
	parser.add_argument('-bw',type=float,default=DEF_BW,help='Observations with bandwidths different from that value +/- btol will be skipped. If None, skip bandwidth selection (default: None).')
	parser.add_argument('-btol',type=float,default=DEF_BTOL,help='Tolerance in bandwidth (default: %f).' % DEF_BTOL)
	parser.add_argument('-obsnchan',type=int,default=DEF_OBSNCHAN,help='Observations with obsnchan parameter different from that value will be skipped. If None, skip obsnchan selection (default: None).')
	parser.add_argument('-backend',type=str,default=DEF_BACKEND,help='Observations with backend different from that value will be skipped. If None, skip backend selection (default: None).')
	parser.add_argument('-algorithm',type=str,default=DEF_ALGORITHM,choices=ALGO_CHOICES,help='Phase shift algorithm (default: \"%s\").' % DEF_ALGORITHM)
	parser.add_argument('-fscrunch',action='store_true',default=False,help='If set, frequency information will be scrunched (default: False).')
	parser.add_argument('-tscrunch',action='store_true',default=False,help='If set, time information will be scrunched (default: False).')
	parser.add_argument('-discardzerow',action='store_true',default=False,help='If set, will discard zero weight profiles (default: False).')
	parser.add_argument('-denoisestd',action='store_true',default=False,help='If set, will denoise the standard profile (default: False).')
	parser.add_argument('-format',type=str,default=DEF_FORMAT,choices=FORMAT_CHOICES,help='Output format for the TOAs (default: \"%s\").' % DEF_FORMAT)
	parser.add_argument('-vapoptions',type=str,nargs='*',default=DEF_VAPOPTIONS,help='vap option or list of vap options to be displayed in the TOA output file (default: None).')
	parser.add_argument('-obscode',type=str,default=DEF_OBSCODE,help='Will replace the observatory code to be written in the output TOA file with this one. If None, will leave the observatory code unchanged (default: None).')
	parser.add_argument('-showinstrument',action='store_true',default=False,help='If set, and if format is tempo2, will display the instrument name for each TOA (default: False).')
	parser.add_argument('-showreceiver',action='store_true',default=False,help='If set, and if format is tempo2, will display the receiver name for each TOA (default: False).')
	parser.add_argument('-showtemplate',action='store_true',default=False,help='If set, will display the template profile automatically picked up by pat for each TOA (default: False).')
	parser.add_argument('-showlength',action='store_true',default=False,help='If set, will display the observation length for each TOA (default: False).')
	parser.add_argument('-showbw',action='store_true',default=False,help='If set, will display the observation bandwidth for each TOA (default: False).')
	parser.add_argument('-shownbins',action='store_true',default=False,help='If set, will display the number of bins for each TOA (default: False).')
	parser.add_argument('-shownch',action='store_true',default=False,help='If set, will display the number of pre-dedispersion frequency channels in bandwidth for each TOA (default: False).')
	parser.add_argument('-showsnr',action='store_true',default=False,help='If set, will display the signal-to-noise for each TOA (default: False).')
	parser.add_argument('-miscflag',type=str,default=None,help='If set, will display this flag for each TOA (default: None).')
	parser.add_argument('-plotres',action='store_true',default=False,help='If set, will make residual plots for each observation (default: False).')
	parser.add_argument('-plotdir',type=str,default=DEF_PLOT_DIR,help='Directory in which the residual plots will be stored (default: \"%s\").' % DEF_PLOT_DIR)
	parser.add_argument('-plotsuffix',type=str,default=DEF_PLOT_SUFFIX,help='Suffix for the residual plots (default: \"%s\").' % DEF_PLOT_SUFFIX)
	parser.add_argument('-listres',type=str,default=DEF_LISTRES,help='Name of an output file containing a list of residuals and chi-square values for each observation (default: None).')
	parser.add_argument('-width',type=float,default=DEF_WIDTH,help='Width of the graph in inches (default: %f).' % DEF_WIDTH)
	parser.add_argument('-height',type=float,default=DEF_HEIGHT,help='Height of the graph in inches (default: %f).' % DEF_HEIGHT)
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not the output TOA file will be overwritten (default: False).')
	parser.add_argument('-logfile',type=str,default=DEF_LOGFILE,help='Path to an output log file.')
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	return parser

#

def make_toas(	template, \
		datadir        = DEF_DATA_DIR, \
		dataext        = DEF_DATA_EXT, \
		toafile        = DEF_TOA_FILE, \
		tmin           = 0., \
		tmax           = 99999., \
		freq           = DEF_FREQ, \
		ftol           = DEF_FTOL, \
		bw             = DEF_BW, \
		btol           = DEF_BTOL, \
		obsnchan       = DEF_OBSNCHAN, \
		backend        = DEF_BACKEND, \
		algorithm      = DEF_ALGORITHM, \
		fscrunch       = False, \
		tscrunch       = False, \
		discardzerow   = False, \
		denoisestd     = False, \
		format         = DEF_FORMAT, \
		vapoptions     = DEF_VAPOPTIONS, \
		obscode        = DEF_OBSCODE, \
		showinstrument = False, \
		showreceiver   = False, \
		showtemplate   = False, \
		showlength     = False, \
		showbw         = False, \
		shownbins      = False, \
		shownch        = False, \
		showsnr        = False, \
		miscflag       = None, \
		plotres        = False, \
		plotdir        = DEF_PLOT_DIR, \
		plotsuffix     = DEF_PLOT_SUFFIX, \
		listres        = DEF_LISTRES, \
		width          = DEF_WIDTH, \
		height         = DEF_HEIGHT, \
		overwrite      = False, \
		logfile        = DEF_LOGFILE, \
		**kwargs ):
	
	# Make some initial checks
	if logfile is not None:
		locargs = locals()
		logger  = initialize_logging(os.path.basename(__file__),logfile=logfile)
		logger.info('running make_toas with arguments:')
		logger.info(locargs)

	if type(template) is str: template = [template]
	
	if not type(template) is list:
		if logfile is not None: logger.error('must pass a list of template profiles.')
		raise MiscError('Must pass a list of template profiles.')
	
	for tpl in template:
		if not os.path.exists(tpl):
			if logfile is not None: logger.error('template file \"%s\" does not exist!' % tpl)
			raise ExistError('Error: template file does not exist!')
			
		try:
			arch = load_archive(tpl)
		except:
			if logfile is not None: logger.error('template profile \"%s\" does not seem to be a valid psrchive file!' % tpl)
			raise PsrchiveError('Error: template profile does not seem to be a valid psrchive file!')
	
	if not os.path.isdir(datadir):
		if logfile is not None: logger.error('data directory \"%s\" does not exist!' % datadir)
		raise ExistError('Error: data directory does not exist!')
		
	if dataext[0] == '.': dataext = dataext[1:]
	
	files  = glob.glob(os.path.join(datadir,'*.' + dataext))
	files.sort()
	Nfiles = len(files)
	if Nfiles == 0:
		if logfile is not None: logger.error('no data files selected! Check data directory and extension: \"%s\" \"%s\".' % (datadir,dataext))
		raise NoFilesError('Error: no data files selected! Check data directory and extension.')
		
	if os.path.exists(toafile):
		if overwrite: os.unlink(toafile)
		else:
			if logfile is not None: logger.error('TOA output file \"%s\" already exists.' % toafile)
			raise AlreadyExistError('TOA output file already exists. Exiting...')
	
	if freq is not None:
		try:
			freq = float(freq)
		except:
			if logfile is not None: logger.error('failed to convert frequency \"%s\" into a float.' % freq)
			raise MiscError('Failed to convert frequency into a float.')
	
	if bw is not None:
		try:
			bw  = float(bw)
		except:
			if logfile is not None: logger.error('failed to convert bandwidth \"%s\" into a float.' % bw)
			raise MiscError('Failed to convert bandwidth into a float.')
	
	if obsnchan is not None:
		try:
			obsnchan = int(obsnchan)
		except:
			if logfile is not None: logger.error('failed to convert obsnchan \"%s\" into an int.' % obsnchan)
			raise MiscError('Failed to convert obsnchan into an int.')
	
	if not algorithm in ALGO_CHOICES:
		if logfile is not None: logger.error('invalid algorithm choice: \"%s\".' % algorithm)
		raise MiscError('Invalid algorithm choice.')
	
	if not format in FORMAT_CHOICES:
		if logfile is not None: logger.error('invalid format choice: \"%s\".' % format)
		raise MiscError('Invalid format choice.')
	
	if plotres:
		if not os.path.isdir(plotdir): os.mkdir(plotdir)
	
	if listres is not None:
		if os.path.exists(listres):
			if overwrite: os.unlink(listres)
			else:
				if logfile is not None: logger.error('residual list file \"%s\" already exists.' % listres)
				raise AlreadyExistError('Residual list file already exists. Exiting...')
	
	# Select data based on frequency, epoch, and instrument information
	goodfiles = []
	
	for fichier in files:
		# Make sure the file is a valid psrchive file
		try:
			arch = load_archive(fichier)
		except:
			continue
	
		# Check that the file is not empty
		sumw  = get_sum_weights_open(arch)
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
		epoch = get_epoch_open(arch)
		if epoch < tmin:
			if logfile is not None: logger.debug('Skipping file \"%s\" with epoch %.1f < %.1f.' % (os.path.basename(fichier),epoch,tmin))
			print 'Skipping file \"%s\" with epoch %.1f < %.1f.' % (os.path.basename(fichier),epoch,tmin)
			continue
		if epoch > tmax:
			if logfile is not None: logger.debug('Skipping file \"%s\" with epoch %.1f > %.1f.' % (os.path.basename(fichier),epoch,tmax))
			print 'Skipping file \"%s\" with epoch %.1f > %.1f.' % (os.path.basename(fichier),epoch,tmax)
			continue
			
		# Check that the frequency and bandwidth are in the requested range
		if freq is not None:
			freq2 = get_frequency_info_open(arch)[0]
			dfreq = numpy.abs(freq - freq2)
			if dfreq > ftol:
				if logfile is not None: logger.debug('Skipping file \"%s\" with freq %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),freq2,freq,ftol))
				print 'Skipping file \"%s\" with freq %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),freq2,freq,ftol)
				continue
			
		if bw is not None:
			bw2   = get_frequency_info_open(arch)[1]
			dbw        = numpy.abs(bw - bw2)
			if dbw > btol:
				if logfile is not None: logger.debug('Skipping file \"%s\" with bandwidth %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),bw2,bw,btol))
				print 'Skipping file \"%s\" with bandwidth %.1f != %.1f (+/- %.1f).' % (os.path.basename(fichier),bw2,bw,btol)
				continue
		
		# Check that the obsnchan parameter is as expected
		if obsnchan is not None:
			obsnchan2 = get_obsnchan(fichier)
			if obsnchan2 != obsnchan:
				if logfile is not None: logger.debug('Skipping file \"%s\" with obsnchan %d != %d.' % (os.path.basename(fichier),obsnchan2,obsnchan))
				print 'Skipping file \"%s\" with obsnchan %d != %d.' % (os.path.basename(fichier),obsnchan2,obsnchan)
				continue
		
		# Check that the backend matches the requested one
		if backend is not None:
			backend2 = get_backend(fichier)
			if backend2 != backend:
				if logfile is not None: logger.debug('Skipping file \"%s\" with backend %s != %s.' % (os.path.basename(fichier),backend2,backend))
				print 'Skipping file \"%s\" with backend %s != %s.' % (os.path.basename(fichier),backend2,backend)
				continue
		
		goodfiles.append(fichier)
		
	Nfiles = len(goodfiles)
	if Nfiles == 0:
		if logfile is not None: logger.error('no data files selected for TOA production! Exiting here.')
		raise NoFilesError('No data files selected for TOA production! Exiting here.')
	
	if logfile is not None: logger.debug('Selected %d files.' % (Nfiles))
	print '\nSelected %d files.' % Nfiles
	
	
	# Start constructing the pat command
	if logfile is not None: logger.debug('Will use the following template profile(s): %s' % template)
	print '\nWill use the following template profile(s): %s' % template
	
	if len(template) == 1:
		templates  = '\"%s\"' % template[0]
	else:
		templates  = '\"'
		for tpl in template[:-1]: templates += '%s ' % tpl
		templates += '%s\"' % template[-1]
		
	patcmd  = 'pat -a %s' % templates
	
	patcmd += ' -A %s' % algorithm
	
	if fscrunch:     patcmd += ' -F'
	
	if tscrunch:     patcmd += ' -T'
	
	if discardzerow: patcmd += ' -d'
	
	if denoisestd:   patcmd += ' -D'
	
	if format == 'tempo2' and (showinstrument or showreceiver):
		patcmd += ' -f \"%s' % format
		if showinstrument: patcmd += ' i'
		if showreceiver:   patcmd += ' r'
		patcmd += '\"'
	else:
		patcmd += ' -f %s' % format 
	
	if len(vapoptions) > 0:
		if len(vapoptions) == 1: 
			vapoptstr  = '\"%s\"' % vapoptions[0]
		else:
			vapoptstr  = '\"'
			for vapoption in vapoptions[:-1]: vapoptstr += '%s ' % vapoption
			vapoptstr += '%s\"' % vapoptions[-1]
		patcmd += ' -C %s' % vapoptstr
	
	
	# Now run pat!
	if logfile is not None: logger.debug('Running pat, with command: %s' % patcmd)
	print '\nRunning pat, with command: %s' % patcmd

	outf = open(toafile,'w+')
	outf.write('FORMAT 1\n')
	
	stds   = []
	shifts = []
	errs   = []
	
	for i in range(Nfiles):
		fichier  = goodfiles[i]
		
		arch           = load_archive(fichier)
		epoch          = get_epoch_open(arch)
		subint_lengths = get_subint_lengths_open(arch)
		freq, bw       = get_frequency_info_open(arch)
		backend        = get_backend(fichier)
		nbins          = get_nbin_open(arch)
		nchan          = get_nchan_open(arch)
		site           = get_site_open(arch)
		bw            /= float(nchan)
		snr            = get_snr_open(arch)

		try:
			obsnchan = get_obsnchan(fichier)
		except:
			obsnchan = -1

		if logfile is not None: logger.debug('Working on \"%s\"...' % os.path.basename(fichier))
		print '\nWorking on \"%s\"...' % os.path.basename(fichier)
		if logfile is not None: logger.debug('(Obs #%d/%d) epoch = %.3f, freq = %.3f, backend = %s' % (i+1,Nfiles,epoch,freq,backend))
		print '(Obs #%d/%d) epoch = %.3f, freq = %.3f, backend = %s' % (i+1,Nfiles,epoch,freq,backend)
		
		# First get the template profile picked out by pat automatically, and the phase shift and error
		cmd    = patcmd + ' -r %s' % fichier
		if not fscrunch: cmd += ' -F'
		if not tscrunch: cmd += ' -T'
		output = commands.getoutput(cmd).split('\n')
		
		try:
			data  = output[0].split()
			std   = data[1]
			shift = float(data[-3])
			err   = float(data[-1])
		except:
			std   = 'unknown'
			shift = -1.
			err   = -1.
			
			for elem in output:
				if 'Tempo' in elem:     continue
				if 'itoa_code' in elem: continue
				if 'WARNING' in elem:   continue
				if 'mismatch' in elem:  continue
				if 'Error' in elem or 'fault' in elem:     
					print 'Error encountered while running pat!'
					break
				
				data  = elem.split()
				if len(data) < 4: continue
				
				try:
					std   = data[1]
					shift = float(data[-3])
					err   = float(data[-1])
				except:
					pass
				
				break
		
		# Now get the TOA and write it to a file
		cmd      = patcmd + ' %s' % fichier
		output   = commands.getoutput(cmd).split('\n')
		idx_freq, idx_sub = 0, 0
		
		for line in output[1:]:
			if len(line) < 5:       continue
			if 'Tempo' in line:     continue
			if 'itoa_code' in line: continue
			if 'WARNING' in line:   continue
			if 'mismatch' in line:  continue
			if 'Error' in line or 'fault' in line: continue
			data = line.split()
			if len(data) < 5:       continue
		
			if format == 'tempo2':
				data[0] = os.path.basename(fichier)
				
				if obscode is None: data[4] = site
				else:               data[4] = obscode
				
				line  = ' '
				for dat in data: line += '%s ' % dat
				if showtemplate: line += ' -tmplt %s ' % std 
				if showlength:   line += ' -tobs %.1f ' % subint_lengths[idx_sub]
				if showbw:       line += ' -bw %.1f ' % bw
				if shownbins:    line += ' -nbin %d ' % nbins
				if shownch:      line += ' -nch %d ' % obsnchan
				if showsnr:      line += ' -snr %.1f ' % snr
				if miscflag is not None: line += ' -misc %s ' % miscflag 
				line += '\n'
			else:
				line  = line.rstrip('\n')
				if showtemplate: line += ' -tmplt %s ' % std
				if showlength:   line += ' -tobs %.1f ' % subint_lengths[idx_sub]
				if showbw:       line += ' -bw %.1f ' % bw
				if shownbins:    line += ' -nbin %d ' % nbins
				if shownch:      line += ' -nch %d ' % obsnchan
				if showsnr:      line += ' -snr %.1f ' % snr
				if miscflag is not None: line += ' -misc %s ' % miscflag
				line += '\n'
				
			outf.write(line)
			idx_freq += 1
			if idx_freq == nchan:
				idx_freq = 0
				idx_sub += 1
		
		# Identify the standard profile automatically chosen by pat
		for tpl in template:
			if std in tpl: break
		
		err /= float(nbins)		
		if logfile is not None: logger.debug('Profile selected by pat: %s, shift = %f, err = %f' % (tpl, shift, err))
		print 'Profile selected by pat: %s, shift = %f, err = %f' % (tpl, shift, err)
		stds.append(tpl)
		shifts.append(shift)
		errs.append(err)
		
	outf.close()
	
	#
	
	if not plotres and listres is None: return
	
	
	if plotres:
		if logfile is not None: logger.debug('Now making residual plots...')
		print '\nNow making residual plots...\n'
		
		import matplotlib
		pext = os.path.splitext(plotsuffix)[1]
		if pext == '.ps':
			ps = True
			if matplotlib.get_backend() == 'ps': pass
			else:                                matplotlib.use('ps')
		else:
			ps = False
			if matplotlib.get_backend() == 'agg': pass
			else:                                 matplotlib.use('agg')
		from matplotlib import pyplot as P
		
		if kwargs.has_key('dpi'): dpi = kwargs['dpi']
		else:                     dpi = DEF_DPI
	
	
	if listres is not None:
		fich = open(listres,'w+')
		fich.write('# EPOCH FREQ SHIFT ERR CHISQ CHISQRED STD FILENAME\n')
		fich.close()
	
	
	for i, fichier, std, shift, err in zip(range(Nfiles), goodfiles, stds, shifts, errs):
		progress_bar(float(i+1)/float(Nfiles),25)
		
		#
		
		arch1 = load_archive(std)
		arch1.pscrunch()
		arch1.tscrunch()
		arch1.fscrunch()
		arch1.remove_baseline()
		prof1 = numpy.ndarray.flatten(arch1.get_data())
		
		epoch = get_epoch(fichier)
		freq  = get_frequency(fichier)
		arch2 = load_archive(fichier)
		arch2.pscrunch()
		arch2.tscrunch()
		arch2.fscrunch()
		arch2.remove_baseline()
		arch2.rotate_phase(shift)
		prof2 = numpy.ndarray.flatten(arch2.get_data())
		
		# Stuff below is adapted from pat.C "diff_profiles"
		
		# This fixes a problem with the normalization
		if (prof2.sum() > 10.): prof2 /= 100.
		
		# These tests make sure we are not dealing with NaN values
		if numpy.isnan(prof1).any(): continue
		if numpy.isnan(prof2).any(): continue
		
		nbins    = len(prof2)
		scale    = (float(nbins) * (prof1*prof2).sum() - prof2.sum() * prof1.sum())
		scale   /= (float(nbins) * (prof1*prof1).sum() - prof1.sum() * prof1.sum())
		offset   = (scale * prof1.sum() - prof2.sum()) / float(nbins)
		
		# Difference
		prof3    = prof1.copy()
		prof3   -= offset
		prof3   *= scale
		diff     = prof2 - prof3
		sumsq    = (diff*diff).sum()
		rmsdiff  = diff.std()
		
		if plotres:
			graph  = os.path.basename(fichier)
			graph  = os.path.splitext(graph)[0] + plotsuffix
			graph  = os.path.join(plotdir,graph)
			
			# Now plot the results!
			fig      = P.figure(figsize=(width,height))
			P.subplots_adjust(left=0.05,right=0.95,bottom=0.075,top=0.95)
			ax1      = fig.add_subplot(211)
			ax2      = fig.add_subplot(212)	
			
			ax2.plot(numpy.linspace(0.,1.,len(prof3)),prof3,c='r',label='Standard')
			ax2.scatter(numpy.linspace(0.,1.,len(prof2)),prof2,c='k',marker='+',label='Shifted data')
			
			ax1.plot(numpy.linspace(0.,1.,len(diff)),diff,c='b',label='Difference')
			
			ax1.set_xlim([0.,1.])
			ax2.set_xlim([0.,1.])
				
			ax1.set_xlabel('Pulse Phase')
			ax2.set_xlabel('Pulse Phase')
			
			ax1.set_ylabel('Intensity (a.u.)')
			ax2.set_ylabel('Intensity (a.u.)')
			
			P.setp(ax1.get_yticklabels(),visible=False)
			P.setp(ax2.get_yticklabels(),visible=False)
			
			ax1.minorticks_on()
			ax2.minorticks_on()
		
			ax1.legend(loc='upper center',frameon=False)
			ax2.legend(loc='upper center',scatterpoints=1,frameon=False)
		
			title = 'MJD %.1f, freq = %.0f MHz, shift = %.2le +/- %.2le, sumsq = %.2le' % (epoch,freq,shift,err,sumsq)
			fig.suptitle(title,fontsize=10)
			
			if ps: fig.savefig(graph)
			else:  fig.savefig(graph,dpi=dpi)
			P.close(fig)
		
		#print epoch, freq, shift, err, sumsq, rmsdiff, std, os.path.basename(fichier)
		
		if listres is not None:
			fich = open(listres,'a+')
			fich.write('%f %f %le %le %le %le %s %s\n' % (epoch, freq, shift, err, sumsq, rmsdiff, std, os.path.basename(fichier)))
			fich.close()
	
	print '\n'
	
	if logfile is not None: 
		logger.info('finished.')
		terminate_logging()
	
	return
	
	
#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	make_toas(	args.template, \
			datadir        = args.datadir, \
			dataext        = args.dataext, \
			toafile        = args.toafile, \
			tmin           = args.tmin, \
			tmax           = args.tmax, \
			freq           = args.freq, \
			ftol           = args.ftol, \
			bw             = args.bw, \
			btol           = args.btol, \
			obsnchan       = args.obsnchan, \
			backend        = args.backend, \
			algorithm      = args.algorithm, \
			fscrunch       = args.fscrunch, \
			tscrunch       = args.tscrunch, \
			discardzerow   = args.discardzerow, \
			denoisestd     = args.denoisestd, \
			format         = args.format, \
			vapoptions     = args.vapoptions, \
			obscode        = args.obscode, \
			showinstrument = args.showinstrument, \
			showreceiver   = args.showreceiver, \
			showtemplate   = args.showtemplate, \
			showlength     = args.showlength, \
			showbw         = args.showbw, \
			shownbins      = args.shownbins, \
			shownch        = args.shownch, \
			showsnr        = args.showsnr, \
			miscflag       = args.miscflag, \
			plotres        = args.plotres, \
			plotdir        = args.plotdir, \
			plotsuffix     = args.plotsuffix, \
			listres        = args.listres, \
			width          = args.width, \
			height         = args.height, \
			overwrite      = args.overwrite, \
			logfile        = args.logfile, \
			dpi            = args.dpi )
			
	goodbye()
