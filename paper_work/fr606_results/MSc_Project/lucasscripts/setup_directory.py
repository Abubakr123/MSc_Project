import os
import sys
import glob
import argparse
import cPickle as pickle

try:
	import psrchive as p
	from misc_tools import *
	import pulsars
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass

# setup_directory.py: script for setting up the working directory for a given pulsar.
# Author:             Lucas Guillemot
# Last update:        20 Avr 2015
# Version:            1.8



# Some default declarations
DEF_DESTDIR     = '.'
DEF_OBSLIST     = '/backup/lguillem/pulsar_list/obslist.pickle'
DEF_BACKENDS    = ['NUPPI','BON']
DEF_DATAEXTS    = {'NUPPI': ['zap'], 'BON': ['zap']}
DEF_EXTDATADIR  = None
DEF_EXTDATAEXT  = 'ar'
DEF_DATADIR     = 'data'
DEF_PLOTDIR     = 'plots'
DEF_TEMPLATEDIR = 'templates'
DEF_LINKSDIR    = 'links'
DEF_REFOLDDIR   = 'refolded'
DEF_SCRUNCHDIR  = 'scrunched'
DEF_LOGFILE     = None

#

def get_parser():
	parser = argparse.ArgumentParser(description='setup_directory.py: a script for setting up the working directory for a given pulsar.')
	parser.add_argument('-pulsar',type=str,required=True,help='Pulsar name.')
	parser.add_argument('-destdir',type=str,default=DEF_DESTDIR,help='Name of the destination working directory (default: \"%s\").' % DEF_DESTDIR)
	parser.add_argument('-backend',type=str,default=DEF_BACKENDS,nargs='+',dest='backends',help='Will select data files recorded with this backend or list of backends (default: %s).' % DEF_BACKENDS)
	parser.add_argument('-dataext',type=str,action='append',dest='exts',nargs=2,help='Data extension to add to the list of accepted file extensions, for a given backend. Expects two arguments: backend and extension (default: %s).' % DEF_DATAEXTS)
	parser.add_argument('-extdatadir',type=str,default=DEF_EXTDATADIR,help='If provided, will look for observation files in this directory. Database look up will be skipped (default: None).')
	parser.add_argument('-extdataext',type=str,default=DEF_EXTDATAEXT,help='Extension of the data files in extdatadir to include (default: \"%s\").' % DEF_EXTDATAEXT)
	parser.add_argument('-datadir',type=str,default=DEF_DATADIR,help='Directory under destdir containing the data files (default: \"%s\").' % DEF_DATADIR)
	parser.add_argument('-linksdir',type=str,default=DEF_LINKSDIR,help='Directory under datadir containing links to the original data files (default: \"%s\").' % DEF_LINKSDIR)
	parser.add_argument('-refolddir',type=str,default=DEF_REFOLDDIR,help='Directory under datadir containing the refolded data files (default: \"%s\").' % DEF_REFOLDDIR)
	parser.add_argument('-scrunchdir',type=str,default=DEF_SCRUNCHDIR,help='Directory under datadir containing the scrunched data files (default: \"%s\").' % DEF_SCRUNCHDIR)
	parser.add_argument('-plotdir',type=str,default=DEF_PLOTDIR,help='Directory under destdir containing the plots (default: \"%s\").' % DEF_PLOTDIR)
	parser.add_argument('-templatedir',type=str,default=DEF_TEMPLATEDIR,help='Directory under destdir containing the template profiles (default: \"%s\").' % DEF_TEMPLATEDIR)
	parser.add_argument('-obslist',type=str,default=DEF_OBSLIST,help='Path to a pickle file containing a dictionary of pulsars and observation files (default: \"%s\").' % DEF_OBSLIST)
	parser.add_argument('-quick',action='store_true',default=False,help='If set, the backend name will be looked for only once, and will be used for all other datafiles (default: None).')
	parser.add_argument('-logfile',type=str,default=DEF_LOGFILE,help='Path to an output log file.')
	return parser

#

def setup_directory(	pulsar, \
			destdir     = DEF_DESTDIR, \
			obslist     = DEF_OBSLIST, \
			backends    = DEF_BACKENDS, \
			dataexts    = DEF_DATAEXTS, \
			extdatadir  = DEF_EXTDATADIR, \
			extdataext  = DEF_EXTDATAEXT, \
			datadir     = DEF_DATADIR, \
			plotdir     = DEF_PLOTDIR, \
			templatedir = DEF_TEMPLATEDIR, \
			linksdir    = DEF_LINKSDIR, \
			refolddir   = DEF_REFOLDDIR, \
			scrunchdir  = DEF_SCRUNCHDIR, \
			quick       = False, \
			logfile     = DEF_LOGFILE ):
	
	# Make some initial checks
	if logfile is not None:
		locargs = locals()
		logger  = initialize_logging(os.path.basename(__file__),logfile=logfile)
		logger.info('running setup_directory with arguments:')
		logger.info(locargs)
	
	if extdatadir is None:
		if not os.path.exists(obslist):
			if logfile is not None: logger.error('observation list \"%s\" does not exist!' % obslist)
			raise ExistError('Error: observation list does not exist!')
		
		try:
			known_psrs = pulsars.pulsars()
			psr        = known_psrs.find_pulsar(pulsar)
		except:
			if logfile is not None: logger.error('unknown pulsar \"%s\" !' % pulsar)
			raise PulsarError('Error: unknown pulsar!')
		
		#
		
		obsdict = pickle.load(open(obslist,'rb'))
		if not obsdict.has_key(psr):
			if logfile is not None: logger.error('pulsar \"%s\" not found in observation dictionary!' % psr)
			raise PulsarError('Error: pulsar not found in observation dictionary!')
	
		observations = obsdict[psr]
		
		if len(observations) == 0:
			if logfile is not None: logger.error('no observations found for this pulsar: \"%s\".' % psr)
			raise PulsarError('Error: no observations found for this pulsar.')
			
			if len(backends) == 0:
				if logfile is not None: logger.error('empty list of backends!')
				raise MiscError('Error: empty list of backends!')
			else:
				backends = list(set(backends))
				
			if len(dataexts) == 0:
				if logfile is not None: logger.error('empty data extensions dictionary!')
				raise MiscError('Error: empty data extensions dictionary!')
			else:
				for b in backends:
					if not dataexts.has_key(b):
						if logfile is not None: logger.error('no extension(s) to select for backend \"%s\"!' % b)
						raise MiscError('incomplete data extensions dictionary!')
					elif len(dataexts[b]) == 0:
						if logfile is not None: logger.error('no extension(s) to select for backend \"%s\"!' % b)
						raise MiscError('incomplete data extensions dictionary!')
	else:
		if not os.path.isdir(extdatadir):
			if logfile is not None: logger.error('data directory \"%s\" does not exist!' % extdatadir)
			raise ExistError('Error: data directory does not exist!')
		else:
			if extdataext[0] == '.': extdataext = extdataext[1:]
			observations = glob.glob(os.path.join(extdatadir,'*.'+extdataext))
			
			if len(observations) == 0:
				if logfile is not None: logger.error('no observation files found in directory \"%s\" and with extension \"%s\".' % (extdatadir,extdataext))
				raise NoFilesError('Error: no observations files with the requested extension found in the requested directory.')
		
	observations.sort()
	
	
	# Now select data files with the right extensions and backends
	archives = {}
	backend  = 'Unknown'
	
	for i in xrange(len(observations)):
		progress_bar(float(i+1)/float(len(observations)),25)
		archive = observations[i]
		
		if quick:
			if backend is 'Unknown':
				try:
					arch    = load_archive(archive)
					backend = get_backend(archive)
				except:
					continue
		else:
			try:
				arch    = load_archive(archive)
				backend = get_backend(archive)
			except:
				continue
			
		if extdatadir is None:
			if backend not in backends: continue
			
			ext     = os.path.splitext(archive)[1]
			if ext[0] == '.': ext = ext[1:]
		
			if dataexts.has_key(backend):
				if ext not in dataexts[backend]: continue
			else:
				if logfile is not None: logger.warn('No data extension rule given for backend %s. Continuing...' % backend)
				print 'No data extension rule given for backend %s. Continuing...' % backend
				continue	
			
			if archives.has_key(backend): archives[backend].append(archive)
			else: archives[backend] = [archive]
		else:
			if backend not in backends: backends.append(backend)
			
			if archives.has_key(backend): archives[backend].append(archive)
			else: archives[backend] = [archive]
			
		
	if len(archives) == 0:
		if logfile is not None: logger.warn('no valid data files found for this pulsar! Exiting here.')
		raise NoFilesError('No valid data files found for this pulsar! Exiting here.')
	
	
	# Create directories
	if not os.path.isdir(destdir):
		if logfile is not None: logger.info('Created directory \"%s\".' % destdir)
		print 'Created directory \"%s\".' % destdir
		os.mkdir(destdir)
	
	datadir      = os.path.join(destdir,datadir)
	if not os.path.isdir(datadir):
		if logfile is not None: logger.info('Created directory \"%s\".' % datadir)
		print 'Created directory \"%s\".' % datadir
		os.mkdir(datadir)
	
	plotdir      = os.path.join(destdir,plotdir)
	if not os.path.isdir(plotdir): 
		if logfile is not None: logger.info('Created directory \"%s\".' % plotdir)
		print 'Created directory \"%s\".' % plotdir
		os.mkdir(plotdir)
	
	tpldir       = os.path.join(destdir,templatedir)
	if not os.path.isdir(tpldir): 
		if logfile is not None: logger.info('Created directory \"%s\".' % tpldir)
		print 'Created directory \"%s\".' % tpldir
		os.mkdir(tpldir)
	
	linksdir     = os.path.join(datadir,linksdir)
	if not os.path.isdir(linksdir): 
		if logfile is not None: logger.info('Created directory \"%s\".' % linksdir)
		print 'Created directory \"%s\".' % linksdir
		os.mkdir(linksdir)
	
	refolddir    = os.path.join(datadir,refolddir)
	if not os.path.isdir(refolddir): 
		if logfile is not None: logger.info('Created directory \"%s\".' % refolddir)
		print 'Created directory \"%s\".' % refolddir
		os.mkdir(refolddir)
	
	scrunchdir   = os.path.join(datadir,scrunchdir)
	if not os.path.isdir(scrunchdir): 
		if logfile is not None: logger.info('Created directory \"%s\".' % scrunchdir)
		print 'Created directory \"%s\".' % scrunchdir
		os.mkdir(scrunchdir)
	
	
	
	# Now create links to the original data...
	newlinks = False
	
	for backend in backends: 
		if not archives.has_key(backend): continue
		else: observations = archives[backend]
		
		linksdir2   = os.path.join(linksdir,backend)
		if not os.path.isdir(linksdir2): os.mkdir(linksdir2)
		
		refolddir2  = os.path.join(refolddir,backend)
		if not os.path.isdir(refolddir2): os.mkdir(refolddir2)
		
		scrunchdir2 = os.path.join(scrunchdir,backend)
		if not os.path.isdir(scrunchdir2): os.mkdir(scrunchdir2)
		
		#
		
		for archive in observations:
			dest = os.path.join(linksdir2,os.path.basename(archive))
			if not os.path.exists(dest):
				os.symlink(archive,dest)
				if logfile is not None: logger.info('Created link to \"%s\".' % archive)
				print 'Created link to \"%s\".' % archive
				newlinks = True
	#
	
	if logfile is not None: 
		logger.info('finished.')
		terminate_logging()
	
	return newlinks
	
#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	dataexts = DEF_DATAEXTS
	if args.exts is not None:
		for ext in args.exts:
			if dataexts.has_key(ext[0]): dataexts[ext[0]].append(ext[1])
			else: dataexts[ext[0]] = [ext[1]]
	
	setup_directory(	args.pulsar, \
				destdir     = args.destdir, \
				obslist     = args.obslist, \
				backends    = args.backends, \
				dataexts    = dataexts, \
				extdatadir  = args.extdatadir, \
				extdataext  = args.extdataext, \
				datadir     = args.datadir, \
				plotdir     = args.plotdir, \
				templatedir = args.templatedir, \
				linksdir    = args.linksdir, \
				refolddir   = args.refolddir, \
				scrunchdir  = args.scrunchdir, \
				quick       = args.quick, \
				logfile     = args.logfile )
	
	goodbye()
