import os
import sys
import glob
import argparse

try:
	import psrchive as p
	from misc_tools import *
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass

# scrunch_data.py: a script for scrunching data files
# Author:      Lucas Guillemot
# Last update: 16 Sep 2014
# Version:     2.0


# Some default declarations
DEF_DATA_DIR   = '.'
DEF_DATA_EXT   = 'refold'
DEF_DEST_DIR   = '.'
DEF_DEST_EXT   = 'scrunched'
DEF_SITE       = 'ncyobs'
DEF_DEDISPERSE = False   
DEF_PSCRUNCH   = False
DEF_BSCRUNCH   = False
DEF_TSCRUNCH   = False
DEF_FSCRUNCH   = False
DEF_TSCR_FAC   = None
DEF_TSCR_NSUB  = None
DEF_TSCR_TSUB  = None
DEF_FSCR_FAC   = None
DEF_FSCR_NCHAN = None
DEF_MORENCHAN  = False
DEF_LOGFILE    = None

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for scrunching data files.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-destdir',type=str,default=DEF_DEST_DIR,help='Directory in which the refolded data files will be stored (default: \"%s\").' % DEF_DEST_DIR)
	parser.add_argument('-destext',type=str,default=DEF_DEST_EXT,help='Extension to be given to refolded data files (default: \"%s\").' % DEF_DEST_EXT)
	parser.add_argument('-parfile',type=str,default=None,action='append',help='Path to a tempo2 par file to use for refolding the data. Multiple par files can be passed (default: None).')
	parser.add_argument('-partmin',type=float,default=None,action='append',help='Start of validity interval of the par file(s) (default: 0).')
	parser.add_argument('-partmax',type=float,default=None,action='append',help='Start of validity interval of the par file(s) (default: 99999).')
	parser.add_argument('-dm',type=float,default=None,help='New DM value to install in data files (default: None).')
	parser.add_argument('-dm_from_parfile',action='store_true',default=False,help='If set, will install new DM values in data files based on the par file DM value and derivatives (disables the -dm option) (default: False).')
	parser.add_argument('-site',type=str,default=DEF_SITE,help='Site to be passed to pam for the refolding (default: \"%s\").' % DEF_SITE)
	parser.add_argument('-tmin',type=float,default=0.,help='Minimum MJD (default: 0).')
	parser.add_argument('-tmax',type=float,default=99999.,help='Maximum MJD (default: 99999).')
	parser.add_argument('-dedisperse',action='store_true',default=False,help='If set, the data will be dedispersed (default: False).')
	parser.add_argument('-pscrunch',action='store_true',default=False,help='If set, polarization information will be scrunched (default: False).')
	parser.add_argument('-bscrunch',action='store_true',default=False,help='If set, phase information will be scrunched (default: False).')
	parser.add_argument('-tscrunch',action='store_true',default=False,help='If set, time information will be scrunched (default: False).')
	parser.add_argument('-fscrunch',action='store_true',default=False,help='If set, frequency information will be scrunched (default: False).')
	parser.add_argument('-tscrunch_factor',type=int,default=None,help='Scrunch time information by this factor (default: None).')
	parser.add_argument('-tscrunch_nsub',type=int,default=None,help='Scrunch time information to this many subints (default: None).')
	parser.add_argument('-tscrunch_tsub',type=float,default=None,help='Scrunch time information to this subint length, in seconds (default: None).')
	parser.add_argument('-fscrunch_factor',type=int,default=None,help='Scrunch frequency information by this factor. Scrunch all information if not set (default: None).')
	parser.add_argument('-fscrunch_nchan',type=int,default=None,help='Scrunch frequency information to this many channels (default: None).')
	parser.add_argument('-morenchan',action='store_true',dest='morenchan',default=False,help='If true and the number of freq channels is not a multiple of the requested factor, get more freq channels (default: False).')
	parser.add_argument('-lessnchan',action='store_false',dest='morenchan')
	parser.add_argument('-forcescrunch',action='store_true',default=False,help='If set, will force the data scrunching, even if the input and output data files are the same (default: False).')
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not refolded data files should be overwritten (default: False).')
	parser.add_argument('-logfile',type=str,default=DEF_LOGFILE,help='Path to an output log file.')
	return parser

#

def scrunch_data(	datadir         = DEF_DATA_DIR, \
			dataext         = DEF_DATA_EXT, \
			destdir         = DEF_DEST_DIR, \
			destext         = DEF_DEST_EXT, \
			parfile         = None, \
			partmin         = None, \
			partmax         = None, \
			dm              = None, \
			dm_from_parfile = None, \
			site            = DEF_SITE, \
			tmin            = 0., \
			tmax            = 99999., \
			dedisperse      = DEF_DEDISPERSE, \
			pscrunch        = DEF_PSCRUNCH, \
			bscrunch        = DEF_BSCRUNCH, \
			tscrunch        = DEF_TSCRUNCH, \
			fscrunch        = DEF_FSCRUNCH, \
			tscrunch_factor = DEF_TSCR_FAC, \
			tscrunch_nsub   = DEF_TSCR_NSUB, \
			tscrunch_tsub   = DEF_TSCR_TSUB, \
			fscrunch_factor = DEF_FSCR_FAC, \
			fscrunch_nchan  = DEF_FSCR_NCHAN, \
			morenchan       = DEF_MORENCHAN, \
			forcescrunch    = False, \
			overwrite       = False, \
			logfile         = DEF_LOGFILE ):
	
	# Make some initial checks
	if logfile is not None:
		locargs = locals()
		logger  = initialize_logging(os.path.basename(__file__),logfile=logfile)
		logger.info('running scrunch_data with arguments:')
		logger.info(locargs)
	
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
		
	if not os.path.isdir(destdir):
		if logfile is not None: logger.warn('destination directory \"%s\" does not exist. Will create it.' % destdir)
		print 'Destination directory does not exist. Will create it.'
		os.mkdir(destdir)
		
	if destext[0] == '.': destext = destext[1:]
	
	if parfile is None:
		if dm_from_parfile:
			if logfile is not None: logger.error('dm_from_parfile requested but no par file was provided!')
			raise MiscError('Error: dm_from_parfile requested but no par file was provided!')
	else:
		if type(parfile) is not list:
			parfile = [parfile]
		
		if partmin is not None:
			if type(partmin) is not list:
				partmin = [partmin]
			
			if not len(partmin) == len(parfile):
				if logfile is not None: logger.error('must provide as many partmin values as par files!')
				raise MiscError('Error: must provide as many partmin values as par files!')
		else:
			partmin = [0.] * len(parfile)
		
		if partmax is not None:
			if type(partmax) is not list:
				partmax = [partmax]
				
			if not len(partmax) == len(parfile):
				if logfile is not None: logger.error('must provide as many partmax values as par files!')
				raise MiscError('Error: must provide as many partmax values as par files!')
		else:
			partmax = [99999.] * len(parfile)
			
		pfiles = ParFiles()
		for i in range(len(parfile)): pfiles.add_parfile(parfile[i],partmin[i],partmax[i])
	
	
	if tscrunch_factor is not None:
		if tscrunch_nsub is not None:
			if logfile is not None: logger.error('tscrunch_factor and tscrunch_nsub options cannot be used together.')
			raise MiscError('Error: tscrunch_factor and tscrunch_nsub options cannot be used together.')
			
		if tscrunch_tsub is not None:
			if logfile is not None: logger.error('tscrunch_factor and tscrunch_tsub options cannot be used together.')
			raise MiscError('Error: tscrunch_factor and tscrunch_tsub options cannot be used together.')
	
	if tscrunch_nsub is not None:
		if tscrunch_tsub is not None:
			if logfile is not None: logger.error('tscrunch_nsub and tscrunch_tsub options cannot be used together.')
			raise MiscError('Error: tscrunch_nsub and tscrunch_tsub options cannot be used together.')
			
	if not tscrunch and any(fac is not None for fac in [tscrunch_factor,tscrunch_nsub,tscrunch_tsub]):
		tscrunch = True
	
	if fscrunch_factor is not None and fscrunch_nchan is not None:
	        if logfile is not None: logger.error('fscrunch_factor and fscrunch_nchan options cannot be used together.')
		raise MiscError('Error: fscrunch_factor and fscrunch_nchan options cannot be used together.')

	if not fscrunch and (fscrunch_factor is not None or fscrunch_nchan is not None):
		fscrunch = True
	
	if not pscrunch and not bscrunch and not tscrunch and not fscrunch:
		if logfile is not None: logger.error('no scrunching requested! Exiting here.')
		raise MiscError('Error: no scrunching requested! Exiting here.')
	

	# Select data based on epoch information
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
			
		goodfiles.append(fichier)
		
	Nfiles = len(goodfiles)
	if Nfiles == 0:
		if logfile is not None: logger.warn('No data files selected for scrunching! Exiting here.')
		raise NoFilesError('No data files selected for scrunching! Exiting here.')
		
	if logfile is not None: logger.debug('Selected %d files.' % (Nfiles))
	print '\nSelected %d files.' % (Nfiles)
	
	#
	
	for fichier in goodfiles:
		if logfile is not None: logger.debug('Processing file \"%s\"...' % fichier)
		print '\nProcessing file \"%s\"...' % fichier
		destfich = os.path.basename(fichier)
		destfich = destfich.replace('.'+dataext,'.'+destext)
		destfich = os.path.join(destdir,destfich)
		
		if os.path.exists(destfich) and not overwrite:
			if logfile is not None: logger.debug('File \"%s\" already exists. Will not overwrite it.' % destfich)
			print 'File \"%s\" already exists. Will not overwrite it.' % destfich
			continue
		
		#
		
		flags    = []
		epoch    = get_epoch(fichier)
			
		
		if parfile is not None:
			pfile = pfiles.get_parfile_for_epoch(epoch)
			flags.append('-E %s' % pfile)
		
		if dm_from_parfile:
			DM    = get_dm_from_parfile(pfile,epoch)
			flags.append('-d %f' % DM)
		elif dm is not None:
			DM    = float(dm)
			flags.append('-d %f' % DM)
		else:
			DM    = None
		
		if site is not None: flags.append('--site %s' % site)
		
		if dedisperse: flags.append('-D')
		
		if pscrunch:   flags.append('-p')
		
		if bscrunch:
			nbin = get_nbin(fichier)
			flags.append('-b %d' % nbin)
		
		"""
		if tscrunch:
			flags.append('-T')
			if tscrunch_factor is not None: 
				# Determine optimal tscrunching factor
				nsubint = get_nsubint(fichier)
				if nsubint % tscrunch_factor == 0: tscr_fac = tscrunch_factor
				else:
					if morensub: trange = range(tscrunch_factor-1,0,-1)
					else:        trange = range(tscrunch_factor,nsubint+1)

					for fac in trange:
						if nsubint % fac == 0:
							if logfile is not None: logger.warn('Nsubint = %d not a multiple of %d. Will tscrunch by %d instead.' % (nsubint,tscrunch_factor,fac))
							print 'Nsubint = %d not a multiple of %d. Will tscrunch by %d instead.' % (nsubint,tscrunch_factor,fac)
							tscr_fac = fac
							break
				
				flags.append('-t %d' % tscr_fac)
				nsubint2 = nsubint / tscr_fac
			elif tscrunch_nsub is not None:
				# Determine optimal tscrunching factor
				nsubint = get_nsubint(fichier)
				if nsubint % tscrunch_nsub != 0:
					if morensub: trange = range(tscrunch_nsub,nsubint+1)
					else:        trange = range(tscrunch_nsub-1,0,-1)

					for fac in trange:
						if nsubint % fac == 0:
							if logfile is not None: logger.warn('Nsubint = %d not a multiple of %d. Will tscrunch to %d bins instead.' % (nsubint,tscrunch_nsub,fac))
							print 'Nsubint = %d not a multiple of %d. Will tscrunch to %d bins instead.' % (nsubint,tscrunch_nsub,fac)
							nsubint2 = fac
							break
				else: nsubint2 = tscrunch_nsub

				flags.append('--setnsub %d' % nsubint2)
			elif tscrunch_tsub is not None:
				length   = get_length(fichier)
				nsubint2 = int(numpy.ceil(length / tscrunch_tsub))
				
				if nsubint2 == 1:
					if logfile is not None: logger.warn('length = %.1f s is less than the required tscrunch_tsub of %.1f. Will only produce one bin.' % (length,tscrunch_tsub))
					print 'Warning: length = %.1f is less than the required tscrunch_tsub of %.1f. Will only produce one bin.' % (length,tscrunch_tsub)
				
				flags.append('--settsub %f' % tscrunch_tsub)
			elif tscrunch_divide is not None:
				length   = get_length(fichier)
				tsub     = length / float(tscrunch_divide)
				
				# this is the theoretical output number of bins -- in practice the actual number of bins is often different
				nsubint2 = tscrunch_divide
				
				flags.append('--settsub %f' % tsub)
			else:
				nsubint2 = 1
		"""
		
		if tscrunch:
			flags.append('-T')
			nsubint = get_nsubint(fichier)
			
			if tscrunch_factor is not None:
				flags.append('-t %d' % tscrunch_factor)
				
				nsubint2 = nsubint / tscrunch_factor
				if nsubint%tscrunch_factor != 0: nsubint2 += 1
			elif tscrunch_nsub is not None:
				flags.append('--setnsub %d' % tscrunch_nsub)
				factor   = nsubint / tscrunch_nsub
				if nsubint%tscrunch_nsub != 0: factor += 1
				
				nsubint2 = nsubint / factor
				if nsubint%factor != 0: nsubint2 += 1
			elif tscrunch_tsub is not None:
				flags.append('--settsub %f' % tscrunch_tsub)
				duration = get_first_subint_duration(fichier)
				factor   = int(tscrunch_tsub / duration)
				
				nsubint2 = nsubint / factor
				if nsubint%factor != 0: nsubint2 += 1
			else:
				nsubint2 = 1
							
		"""
		if fscrunch:
			nchan = get_nchan(fichier)
			flags.append('-F')
			if fscrunch_factor is not None:
				# Determine optimal fscrunching factor
				if nchan % fscrunch_factor == 0: fscr_fac = fscrunch_factor
				else:
					if morenchan: frange = range(fscrunch_factor-1,0,-1)
					else:         frange = range(fscrunch_factor,nchan+1)
					
					for fac in frange:
						if nchan % fac == 0:
							if logfile is not None: logger.warn('Nchan = %d not a multiple of %d. Will fscrunch by %d instead.' % (nchan,fscrunch_factor,fac))
							print 'Nchan = %d not a multiple of %d. Will fscrunch by %d instead.' % (nchan,fscrunch_factor,fac)
							fscr_fac = fac
							break
				
				
				flags.append('-f %d' % fscr_fac)
				nchan2 = nchan / fscr_fac
			elif fscrunch_nchan is not None:
				# Determine optimal fscrunching factor
				if nchan % fscrunch_nchan != 0:
					if morenchan: frange = range(fscrunch_nchan,nchan+1)
					else:         frange = range(fscrunch_nchan-1,0,-1)
					
					for fac in frange:
						if nchan % fac == 0:
							if logfile is not None: logger.warn('Nchan = %d not a multiple of %d. Will fscrunch to %d bins instead.' % (nchan,fscrunch_nchan,fac))
							print 'Nchan = %d not a multiple of %d. Will fscrunch to %d bins instead.' % (nchan,fscrunch_nchan,fac)
							nchan2 = fac
							break
				else: nchan2 = fscrunch_nchan
				
				flags.append('--setnchn %d' % nchan2)
			else:
				nchan2 = 1
		"""
		
		if fscrunch:
			flags.append('-F')
			nchan = get_nchan(fichier)
			
			if fscrunch_factor is not None:
				flags.append('-f %d' % fscrunch_factor)
				
				nchan2 = nchan / fscrunch_factor
				if nchan%fscrunch_factor != 0: nchan2 += 1
			elif fscrunch_nchan is not None:
				# The setnchn option behaves differently from other such pam flags: unlike other options, this one requires that 
				# the initial number of channels be a multiple of the new one EXACTLY. The optimal fscrunching factor must 
				# therefore be determined.
				
				if nchan%fscrunch_nchan != 0:
					if morenchan: frange = range(fscrunch_nchan,nchan+1)
					else:         frange = range(fscrunch_nchan-1,0,-1)
					
					for fac in frange:
						if nchan % fac == 0:
							if logfile is not None: logger.warn('Nchan = %d not a multiple of %d. Will fscrunch to %d bins instead.' % (nchan,fscrunch_nchan,fac))
							print 'Nchan = %d not a multiple of %d. Will fscrunch to %d bins instead.' % (nchan,fscrunch_nchan,fac)
							nchan2 = fac
							break
				else: nchan2 = fscrunch_nchan
				
				flags.append('--setnchn %d' % nchan2)
			else:
				nchan2 = 1
		
		# If the destination file already exists, do a last test to see if the properties are the same or not.
		if os.path.exists(destfich) and overwrite:
			diff = False
			
			# if par file is provided, check that the destination file has the same info
			if not diff and parfile is not None and not same_ephemeris(destfich,pfile): diff = True
			
			# if par file not provided, check that the destination file and the orig file have the same info
			if not diff and parfile is None and not same_ephemeris(destfich,extract_parfile(fichier)): diff = True
			
			# if DM is provided, check that the destination file has the same DM
			if not diff and DM is not None and not same_dm(destfich,DM): diff = True
			
			# if DM not provided, check that the destination file and the orig file have the same DM
			if not diff and DM is None and not same_dm(destfich,get_dm(fichier)): diff = True
			
			# if site is provided, check that the destination file has the same site
			if not diff and site is not None and get_site(destfich) != site: diff = True
			
			# if dedispersion is required, check the destination file
			if not diff and dedisperse and not get_dedispersed(destfich): diff = True
			
			# if polarization scrunching is required, check the destination file
			if not diff and pscrunch and get_npol(destfich) != 1: diff = True
			
			# if phase scrunching is required, check the destination file
			if not diff and bscrunch and get_nbin(destfich) != 1: diff = True
			
			# if time scrunching is required, check the destination file
			if not diff and tscrunch and get_nsubint(destfich) != nsubint2: diff = True
			
			# if frequency scrunching is required, check the destination file
			if not diff and fscrunch and get_nchan(destfich) != nchan2: diff = True
			
			#
			
			if not diff and not forcescrunch:
				if logfile is not None: logger.debug('Destination file exists and seems to be identical in target properties. Continuing...')
				print 'Destination file exists and seems to be identical in target properties. Continuing...'
				continue
			else:
				os.unlink(destfich)
		
		
		# Now scrunch the data!
		flags_line = ''
		for flag in flags: flags_line += ' ' + flag
		
		try:
			scrunch_file(fichier,destfich,flags_line)
			if logfile is not None: logger.info('Created file \"%s\".' % destfich)
			print 'Created file \"%s\".' % destfich
		except PsrchiveError, e:
			if logfile is not None: logger.error(e.msg)
			logger.error('Command: %s' % e.cmd)
			print 'Failed to create file \"%s\".' % destfich
		
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
	

	scrunch_data(	datadir         = args.datadir, \
			dataext         = args.dataext, \
			destdir         = args.destdir, \
			destext         = args.destext, \
			parfile         = args.parfile, \
			partmin         = args.partmin, \
			partmax         = args.partmax, \
			dm              = args.dm, \
			dm_from_parfile = args.dm_from_parfile, \
			site            = args.site, \
			tmin            = args.tmin, \
			tmax            = args.tmax, \
			dedisperse      = args.dedisperse, \
			pscrunch        = args.pscrunch, \
			bscrunch        = args.bscrunch, \
			tscrunch        = args.tscrunch, \
			fscrunch        = args.fscrunch, \
			tscrunch_factor = args.tscrunch_factor, \
			tscrunch_nsub   = args.tscrunch_nsub, \
			tscrunch_tsub   = args.tscrunch_tsub, \
			fscrunch_factor = args.fscrunch_factor, \
			fscrunch_nchan  = args.fscrunch_nchan, \
			morenchan       = args.morenchan, \
			forcescrunch    = args.forcescrunch, \
			overwrite       = args.overwrite, \
			logfile         = args.logfile )
	
	goodbye()
