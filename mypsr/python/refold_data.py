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

# refold_data.py: a script for refolding data files
# Author:         Lucas Guillemot
# Last update:    6 Sep 2014
# Version:        1.24


# Some default declarations
DEF_DATA_DIR = '.'
DEF_DATA_EXT = 'zap'
DEF_DEST_DIR = '.'
DEF_DEST_EXT = 'refold'
DEF_SITE     = 'ncyobs'
DEF_LOGFILE  = None

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for refolding data files using a par file and/or installing a new DM.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-destdir',type=str,default=DEF_DEST_DIR,help='Directory in which the refolded data files will be stored (default: \"%s\").' % DEF_DEST_DIR)
	parser.add_argument('-destext',type=str,default=DEF_DEST_EXT,help='Extension to be given to refolded data files (default: \"%s\").' % DEF_DEST_EXT)
	parser.add_argument('-parfile',type=str,default=None,action='append',help='Path to a tempo2 par file to use for refolding the data. Multiple par files can be passed (default: None).')
	parser.add_argument('-partmin',type=float,default=None,action='append',help='Start of validity interval of the par file(s) (default: 0).')
	parser.add_argument('-partmax',type=float,default=None,action='append',help='Start of validity interval of the par file(s) (default: 99999).')
	parser.add_argument('-dm',type=float,default=None,help='New DM value to install in data files (default: None).')
	parser.add_argument('-dm_from_parfile',action='store_true',default=False,help='If set, will install new DM values in data files based on the par file DM value and derivatives (disables the -dm option) (default: False).')
	parser.add_argument('-forcerefold',action='store_true',default=False,help='If set, will force the data refolding, even if the input and installed par files are the same (default: False).')
	parser.add_argument('-site',type=str,default=DEF_SITE,help='Site to be passed to pam for the refolding (default: \"%s\").' % DEF_SITE)
	parser.add_argument('-tmin',type=float,default=0.,help='Minimum MJD (default: 0).')
	parser.add_argument('-tmax',type=float,default=99999.,help='Maximum MJD (default: 99999).')
	parser.add_argument('-scrunchdir',type=str,default=None,help='If set, will search for a file with a similar name in this directory for each data file considered. If a file is found, the data are not refolded again (default: None).')
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not refolded data files should be overwritten (default: False).')
	parser.add_argument('-logfile',type=str,default=DEF_LOGFILE,help='Path to an output log file.')
	return parser

#

def refold_data(	datadir         = DEF_DATA_DIR, \
			dataext         = DEF_DATA_EXT, \
			destdir         = DEF_DEST_DIR, \
			destext         = DEF_DEST_EXT, \
			parfile         = None, \
			partmin         = None, \
			partmax         = None, \
			dm              = None, \
			dm_from_parfile = False, \
			forcerefold     = False, \
			site            = DEF_SITE, \
			tmin            = 0., \
			tmax            = 99999., \
			scrunchdir      = None, \
			overwrite       = False, \
			logfile         = DEF_LOGFILE ):
	
	# Make some initial checks
	if logfile is not None:
		locargs = locals()
		logger  = initialize_logging(os.path.basename(__file__),logfile=logfile)
		logger.info('running refold_data with arguments:')
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
		if dm is None:
			if logfile is not None: logger.warn('no par file and no new DM value provided. Will only rename files.')
			print 'Warning: no par file and no new DM value provided. Will only rename files.'
			
		if dm_from_parfile:
			if logfile is not None: logger.error('dm_from_parfile requested but no par file was provided!')
			raise MiscError('Error: dm_from_parfile requested but no par file was provided!')

		if forcerefold:
			if logfile is not None: logger.error('forcerefold requested but no par file was provided!')
			raise MiscError('Error: forcerefold requested but no par file was provided!')
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
	
	if forcerefold and scrunchdir is not None:
		if logfile is not None: logger.error('scrunchdir option is incompatible with forcerefold.')
		raise MiscError('scrunchdir option is incompatible with forcerefold.')

	if scrunchdir is not None and not os.path.isdir(scrunchdir):
		if logfile is not None: logger.error('scrunchdir \"%\" does not exist.' % scrunchdir)
		raise ExistError('Error: scrunchdir does not exist.')
	elif scrunchdir is not None:
		scr_archives = glob.glob(os.path.join(scrunchdir,'*'))
		if len(scr_archives) == 0:
			if logfile is not None: logger.warn('no data files found in scrunchdir.')
			print 'Warning: no data files found in scrunchdir.'
			scrunchdir = None
		
	
	# Data set selection
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
			
		# Find appropriate par file
		if parfile is not None:
			pfile = pfiles.get_parfile_for_epoch(epoch)

		# Check whether there is already a file with a similar name in scrunchdir
		if scrunchdir is not None:
			basename = os.path.basename(fichier)
			basename = os.path.splitext(basename)[0]
			found    = False
			
			for scr_archive in scr_archives:
				basename2 = os.path.basename(scr_archive)
				basename2 = os.path.splitext(basename2)[0]
			
				if basename == basename2:
					diff  = False
					
					# if par file is provided, check that the destination file has the same info
					if not diff and parfile is not None and not same_ephemeris(scr_archive,pfile): diff = True
					
					# if DM is provided, check that the destination file has the same DM
					if not diff and dm is not None and not same_dm(scr_archive,dm): diff = True
					
					# if site is provided, check that the destination file has the same site
					if not diff and site is not None and get_site(scr_archive) != site: diff = True
					
					if not diff:
						if logfile is not None: logger.debug('Skipping file \"%s\": found similar file in scrunchdir.' % os.path.basename(fichier))
						print 'Skipping file \"%s\": found similar file in scrunchdir.' % os.path.basename(fichier)
						found = True
						break
			
			if found: continue

		goodfiles.append(fichier)

	Nfiles = len(goodfiles)
	if Nfiles == 0:
		if logfile is not None: logger.warn('No data files selected for refolding! Exiting here.')
		print 'No data files selected for refolding! Exiting here.'
		return

	if logfile is not None: logger.debug('Selected %d files.' % (Nfiles))
	print '\nSelected %d files.' % (Nfiles)

	#

	for fichier in goodfiles:
		if logfile is not None: logger.debug('Processing file \"%s\"...' % fichier)
		print '\nProcessing file \"%s\"...' % fichier
		destfich = os.path.basename(fichier)
		destfich = destfich.replace('.'+dataext,'.'+destext)
		destfich = os.path.join(destdir,destfich)
	
		# Now let's fold these data files!
		if os.path.exists(destfich):
			if not overwrite:
				if logfile is not None: logger.debug('File \"%s\" already exists. Will not overwrite it.' % destfich)
				print 'File \"%s\" already exists. Will not overwrite it.' % destfich
				continue
			else:
				if parfile is None and dm is None:
					os.unlink(destfich)
					os.symlink(os.path.abspath(fichier),destfich)
					if logfile is not None: logger.info('Created file \"%s\".' % destfich)
					print 'Created file \"%s\".' % destfich
					continue
				else:
					epoch = get_epoch(fichier)
					
					if parfile is not None:
						pfile = pfiles.get_parfile_for_epoch(epoch)
				
					if dm_from_parfile:  DM = get_dm_from_parfile(pfile,epoch)
					elif dm is not None: DM = float(dm)
					else:                DM = None

					if forcerefold:           PAR = pfile
					elif parfile is not None: PAR = pfile
					else:                     PAR = None

					if (DM is not None and not same_dm(destfich,DM)) or (parfile is not None and not same_ephemeris(destfich,pfile)):
						try:
							fold_file(fichier,destfich,DM=DM,parfile=PAR,site=site)
							if logfile is not None: logger.info('Created file \"%s\".' % destfich)
							print 'Created file \"%s\".' % destfich
						except PsrchiveError, e:
							if logfile is not None: 
								logger.error(e.msg)
								logger.error('Command: %s' % e.cmd)
							print 'Failed to create file \"%s\".' % destfich
					else:
						if logfile is not None: logger.debug('Destination file already exists, and has same par file and/or DM. Will not refold it.')
						print 'Destination file already exists, and has same par file and/or DM. Will not refold it.'
						continue
		else:
			if parfile is None and dm is None:
				os.symlink(os.path.abspath(fichier),destfich)
				if logfile is not None: logger.info('Created file \"%s\".' % destfich)
				print 'Created file \"%s\".' % destfich
				continue
			else:
				epoch = get_epoch(fichier)
				
				if parfile is not None:
					pfile = pfiles.get_parfile_for_epoch(epoch)
				
				if dm_from_parfile:  DM = get_dm_from_parfile(pfile,epoch)
				elif dm is not None: DM = float(dm)
				else:                DM = None

				if parfile is not None: PAR = pfile
				else:                   PAR = None

				try:
					fold_file(fichier,destfich,DM=DM,parfile=PAR,site=site)
					if logfile is not None: logger.info('Created file \"%s\".' % destfich)
					print 'Created file \"%s\".' % destfich
				except PsrchiveError, e:
					if logfile is not None: 
						logger.error(e.msg)
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

	refold_data(	datadir         = args.datadir, \
			dataext         = args.dataext, \
			destdir         = args.destdir, \
			destext         = args.destext, \
			parfile         = args.parfile, \
			partmin         = args.partmin, \
			partmax         = args.partmax, \
			dm              = args.dm, \
			dm_from_parfile = args.dm_from_parfile, \
			forcerefold     = args.forcerefold, \
			site            = args.site, \
			tmin            = args.tmin, \
			tmax            = args.tmax, \
			scrunchdir      = args.scrunchdir, \
			overwrite       = args.overwrite, \
			logfile         = args.logfile )

	goodbye()
