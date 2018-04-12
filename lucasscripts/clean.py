import os
import glob
import argparse

try:
	from misc_tools import *
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass

# clean.py:    simple script for cleaning files in a directory based on their extension
# Author:      Lucas Guillemot
# Last update: 16 Sep 2014
# Version:     1.03


# Some default declarations
DEF_DATA_EXT = 'refold'

#

def get_parser():
	parser = argparse.ArgumentParser(description='A simple script for cleaning files in a directory based on their extension.')
	parser.add_argument('-datadir',type=str,required=True,help='Directory containing the data files to clean.')
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to clean (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-logfile',type=str,default=None,help='Path to an output log file.')
	return parser

#

def clean(	datadir, \
		dataext = DEF_DATA_EXT, \
		logfile = None ):
	
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
	
	archives = glob.glob(os.path.join(datadir,'*.' + dataext))
	archives.sort()
	
	if len(archives) == 0:
		if logfile is not None: logger.error('no data files selected! Check data directory and extension: \"%s\" \"%s\".' % (datadir,dataext))
		raise NoFilesError('Error: no data files selected! Check data directory and extension.')
		
	for archive in archives:
		if not os.path.exists(archive): 
			if logfile is not None: logger.error('file \"%s\" does not exist!' % archive)
			raise ExistError('Error: file does not exist!')
		
	# Now clean the data
	for archive in archives:
		os.unlink(archive)
		if logfile is not None: logger.info('Deleted file \"%s\".' % archive)
		print 'Deleted file \"%s\".' % archive
		
	return
	
#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	clean(	args.datadir, \
		args.dataext, \
		args.logfile )
		
	goodbye()
