import os
import sys
import glob
import numpy
import argparse

try:
	from misc_tools import *
	from plotone import plotone
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass
	
# multiplot.py: script for producing plots for a list of psrchive data files.
# Author:       Lucas Guillemot
# Last Update:  6 Sep 2014
# Version:      1.0



# Some default declarations
DEF_DATA_DIR   = '.'
DEF_DATA_EXT   = 'DFTp'
DEF_DEST_DIR   = '.'
DEF_X          = 'phase'
DEF_Y          = 'intens'
DATA_CHOICE_X  = ['phase','freq','time']
DATA_CHOICE_Y  = ['intens','phase','freq','time']
DEF_SUFFIX     = '_graph.png'
DEF_CM         = 'hot'
DEF_WIDTH      = 8.
DEF_HEIGHT     = 6.
DEF_DPI        = 120

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for producing plots for a list of psrchive data files.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-destdir',type=str,default=DEF_DEST_DIR,help='Directory in which the output plot files will be stored (default: \"%s\").' % DEF_DEST_DIR)
	parser.add_argument('-x',type=str,default=DEF_X, \
				choices=DATA_CHOICE_X,help='Quantity to be plotted in the x-axis (default: \"%s\").' % DEF_X)
	parser.add_argument('-y',type=str,default=DEF_Y, \
				choices=DATA_CHOICE_Y,help='Quantity to be plotted in the y-axis (default: \"%s\").' % DEF_Y)
	parser.add_argument('-suffix',type=str,default=DEF_SUFFIX,help='Suffix for the output plot files (default: \"%s\").' % DEF_SUFFIX)
	parser.add_argument('-nobaseremove',action='store_true',default=False,help='Whether or not the baseline should be removed (default: False).')
	parser.add_argument('-nodedisp',action='store_true',default=False,help='Whether or not the data should be dedispersed (default: False).')
	parser.add_argument('-rebinx',type=int,default=1,help='Rebin the data in the x-direction by this factor (default: 1).')
	parser.add_argument('-rebiny',type=int,default=1,help='Rebin the data in the y-direction by this factor (default: 1).')
	parser.add_argument('-width',type=float,default=DEF_WIDTH,help='Width of individual subplots in inches (default: %f).' % DEF_WIDTH)
	parser.add_argument('-height',type=float,default=DEF_HEIGHT,help='Height of individual subplots in inches (default: %f).' % DEF_HEIGHT)
	parser.add_argument('-norm',action='store_true',default=False,help='If set, each row of 2D data will be normalized (default: False).')
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not the plot should be overwritten (default: False).')
	
	parser.add_argument('-titlepsr',action='store_true',dest='titlepsr',help='If set, the pulsar name will be given in subplot titles (default: False).')
	parser.add_argument('-notitlepsr',action='store_false',dest='titlepsr')
	parser.set_defaults(titlepsr=True)
	
	parser.add_argument('-titlemjd',action='store_true',dest='titlemjd',help='If set, the pulsar name will be given in subplot titles (default: True).')
	parser.add_argument('-notitlemjd',action='store_false',dest='titlemjd')
	parser.set_defaults(titlemjd=True)
	
	parser.add_argument('-titletobs',action='store_true',dest='titletobs',help='If set, the pulsar name will be given in subplot titles (default: True).')
	parser.add_argument('-notitletobs',action='store_false',dest='titletobs')
	parser.set_defaults(titletobs=True)
	
	parser.add_argument('-titlefreq',action='store_true',dest='titlefreq',help='If set, the observing frequency will be given in the subplot titles (default: False).')
	parser.add_argument('-notitlefreq',action='store_false',dest='titlefreq')
	parser.set_defaults(titlefreq=True)
		
	parser.add_argument('-titlesnr',action='store_true',dest='titlesnr',help='If set, the SNR will be given in subplot titles (default: False).')
	parser.add_argument('-notitlesnr',action='store_false',dest='titlesnr')
	parser.set_defaults(titlesnr=True)
	
	parser.add_argument('-cm',type=str,default=DEF_CM,help='Matplotlib color map to use (default: \"%s\").' % DEF_CM)
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	return parser
	
#

def multiplot(	datadir      = DEF_DATA_DIR, \
		dataext      = DEF_DATA_EXT, \
		destdir      = DEF_DEST_DIR, \
		x            = DEF_X, \
		y            = DEF_Y, \
		suffix       = DEF_SUFFIX, \
		nobaseremove = False, \
		nodedisp     = False, \
		rebinx       = 1, \
		rebiny       = 1, \
		width        = DEF_WIDTH, \
		height       = DEF_HEIGHT, \
		norm         = False, \
		overwrite    = False, \
		titlepsr     = False, \
		titlemjd     = True, \
		titletobs    = True, \
		titlefreq    = False, \
		titlesnr     = False, \
		cm           = DEF_CM, \
		dpi          = DEF_DPI ):
		
	# Make some initial checks
	if not os.path.isdir(datadir):
		raise ExistError('Error: data directory does not exist!')
	
	if dataext[0] == '.': dataext = dataext[1:]
	
	archives = glob.glob(os.path.join(datadir,'*.' + dataext))
	
	if len(archives) == 0:
		raise NoFilesError('Error: no data files selected! Check data directory and extension.')
	
	if not os.path.isdir(destdir):
		print 'Destination directory does not exist. Will create it.'
		os.mkdir(destdir)

	for archive in archives:
		if not os.path.exists(archive): raise ExistError('Error: file does not exist!')
		
		try:
			arch = load_archive(archive)
		except:
			raise PsrchiveError('Error: file does not seem to be a valid psrchive file!')
			
		#
		
		destgraph  = os.path.basename(archive)
		destgraph  = os.path.splitext(destgraph)[0]
		destgraph  = os.path.join(destdir,destgraph) + suffix
		
		if os.path.exists(destgraph):
			if overwrite: os.unlink(destgraph)
			else:
				raise AlreadyExistError('Output plot already exists. Exiting...')
	
	archives.sort()
			
	# Now make the plots
	for archive in archives:
		destgraph  = os.path.basename(archive)
		destgraph  = os.path.splitext(destgraph)[0]
		destgraph  = os.path.join(destdir,destgraph) + suffix
		
		try:
			plotone(	archive, \
					x            = x, \
					y            = y, \
					ascii        = False, \
					graph        = destgraph, \
					nobaseremove = nobaseremove, \
					nodedisp     = nodedisp, \
					rebinx       = rebinx, \
					rebiny       = rebiny, \
					width        = width, \
					height       = height, \
					norm         = norm, \
					clean        = False, \
					titlepsr     = titlepsr, \
					titlemjd     = titlemjd, \
					titletobs    = titletobs, \
					titlefreq    = titlefreq, \
					titlesnr     = titlesnr, \
					cm           = cm, \
					dpi          = dpi )
			
			print 'Created file \"%s\".' % destgraph
		except:
			print 'Failed to create file \"%s\".' % destgraph
			pass
	
	return

#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	multiplot(	datadir      = args.datadir, \
			dataext      = args.dataext, \
			destdir      = args.destdir, \
			x            = args.x, \
			y            = args.y, \
			suffix       = args.suffix, \
			nobaseremove = args.nobaseremove, \
			nodedisp     = args.nodedisp, \
			rebinx       = args.rebinx, \
			rebiny       = args.rebiny, \
			width        = args.width, \
			height       = args.height, \
			norm         = args.norm, \
			overwrite    = args.overwrite, \
			titlepsr     = args.titlepsr, \
			titlemjd     = args.titlemjd, \
			titletobs    = args.titletobs, \
			titlefreq    = args.titlefreq, \
			titlesnr     = args.titlesnr, \
			cm           = args.cm, \
			dpi          = args.dpi )
			
	goodbye()
