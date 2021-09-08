import os
import sys
import glob
import numpy
import argparse

try:
	import psrchive as p
	from misc_tools import *
	from plotone import extract_data
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass

# plotmulti.py: script for producing simple plots out of multiple psrchive data files.
# Author:       Lucas Guillemot
# Last update:  28 Oct 2014
# Version:      1.11



# Some default declarations
DEF_DATA_DIR   = '.'
DEF_DATA_EXT   = 'DFTp'
DEF_X          = 'phase'
DEF_Y          = 'intens'
DATA_CHOICE_X  = ['phase','freq','time']
DATA_CHOICE_Y  = ['intens','phase','freq','time']
DEF_GRAPH      = 'graph.png'
DEF_CM         = 'hot'
DEF_WIDTH      = 2.4
DEF_HEIGHT     = 1.5
DEF_DPI        = 100
DEF_MAX_ZSCORE = 3.

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for producing various plots from multiple data files.')
	parser.add_argument('-datadir',type=str,default=DEF_DATA_DIR,help='Directory containing the input data files (default: \"%s\").' % DEF_DATA_DIR)
	parser.add_argument('-dataext',type=str,default=DEF_DATA_EXT,help='Extension of data files to read from (default: \"%s\").' % DEF_DATA_EXT)
	parser.add_argument('-x',type=str,default=DEF_X, \
				choices=DATA_CHOICE_X,help='Quantity to be plotted in the x-axis (default: \'%s\').' % DEF_X)
	parser.add_argument('-y',type=str,default=DEF_Y, \
				choices=DATA_CHOICE_Y,help='Quantity to be plotted in the y-axis (default: \'%s\').' % DEF_Y)
	parser.add_argument('-graph',type=str,default=DEF_GRAPH,help='Name of the output graph. If None, will run in interactive mode (default: \'%s\').' % DEF_GRAPH)
	parser.add_argument('-nobaseremove',action='store_true',default=False,help='Whether or not the baseline should be removed (default: False).')
	parser.add_argument('-nodedisp',action='store_true',default=False,help='Whether or not the data should be dedispersed (default: False).')
	parser.add_argument('-rebinx',type=int,default=1,help='Rebin the data in the x-direction by this factor (default: 1).')
	parser.add_argument('-rebiny',type=int,default=1,help='Rebin the data in the y-direction by this factor (default: 1).')
	parser.add_argument('-width',type=float,default=DEF_WIDTH,help='Width of individual subplots in inches (default: %f).' % DEF_WIDTH)
	parser.add_argument('-height',type=float,default=DEF_HEIGHT,help='Height of individual subplots in inches (default: %f).' % DEF_HEIGHT)
	parser.add_argument('-norm',action='store_true',default=False,help='If set, each row of 2D data will be normalized (default: False).')
	parser.add_argument('-clean',action='store_true',default=False,help='If set, will calculate the z-scores of the RMSs of data rows, and rows with z-score larger than MAXZ will be blanked out (default: False).')
	parser.add_argument('-maxz',type=float,default=DEF_MAX_ZSCORE,help='Maximum acceptable z-score (default: %f).' % DEF_MAX_ZSCORE)
	
	parser.add_argument('-titlepsr',action='store_true',dest='titlepsr',help='If set, the pulsar name will be given in subplot titles (default: False).')
	parser.add_argument('-notitlepsr',action='store_false',dest='titlepsr')
	parser.set_defaults(titlepsr=False)
	
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
	parser.set_defaults(titlesnr=False)
	
	parser.add_argument('-freqcolor',action='store_true',dest='freqcolor',help='If set, pulse profiles for different frequencies will be plotted with different colors (default: True).')
	parser.add_argument('-nofreqcolor',action='store_false',dest='freqcolor')
	parser.set_defaults(freqcolor=True)
	
	parser.add_argument('-ncol',type=int,default=None,help='Force the number of columns in the output plot to be this value (default: None).')
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not the plot should be overwritten (default: False).')
	parser.add_argument('-cm',type=str,default=DEF_CM,help='Matplotlib color map to use (default: \'%s\').' % DEF_CM)
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	return parser

#

def plotmulti(	datadir      = DEF_DATA_DIR, \
		dataext      = DEF_DATA_EXT, \
		x            = DEF_X, \
		y            = DEF_Y, \
		graph        = DEF_GRAPH, \
		nobaseremove = False, \
		nodedisp     = False, \
		rebinx       = 1, \
		rebiny       = 1, \
		width        = DEF_WIDTH, \
		height       = DEF_HEIGHT, \
		norm         = False, \
		clean        = False, \
		maxz         = DEF_MAX_ZSCORE, \
		titlepsr     = False, \
		titlemjd     = True, \
		titletobs    = True, \
		titlefreq    = False, \
		titlesnr     = False, \
		freqcolor    = True, \
		ncol         = None, \
		overwrite    = False, \
		**kwargs):
	
	# Make some initial checks
	if not os.path.isdir(datadir):
		raise ExistError('Error: data directory does not exist!')
		
	if dataext[0] == '.': dataext = dataext[1:]
	
	archives = glob.glob(os.path.join(datadir,'*.' + dataext))
	
	if len(archives) == 0:
		raise NoFilesError('Error: no data files selected! Check data directory and extension.')
	
	for archive in archives:
		if not os.path.exists(archive): raise ExistError('Error: file does not exist!')
		
		try:
			arch = load_archive(archive)
		except:
			raise PsrchiveError('Error: file does not seem to be a valid psrchive file!')
			
	if x not in DATA_CHOICE_X or y not in DATA_CHOICE_Y: raise MiscError('Error: not implemented yet.')
	
	if ncol is not None and ncol < 1:
		raise MiscError('Error: number of columns must be greater than 0!')
	
	if graph is not None and os.path.exists(graph):
		if overwrite: os.unlink(graph)
		else:
			raise AlreadyExistError('Output plot already exists. Exiting...')
	
	if graph is not None:
		graphdir = os.path.dirname(graph)
		if graphdir != '' and not os.path.isdir(graphdir):
			os.mkdir(graphdir)
	
	# Set up labels
	if y == 'intens':
		ylabel = 'Intensity'
		if x == 'phase':  xlabel = 'Pulse Phase'
		elif x == 'freq': xlabel = 'Frequency'
		elif x == 'time': xlabel = 'Time'
	elif y == 'phase':
		ylabel = 'Pulse Phase'
		if x == 'phase':  raise MiscError('Error: invalid choice for the plot (phase vs phase)!')
		elif x == 'freq': xlabel = 'Frequency'
		elif x == 'time': xlabel = 'Time'
	elif y == 'freq':
		ylabel = 'Frequency'
		if x == 'phase':  xlabel = 'Pulse Phase'
		elif x == 'freq': raise MiscError('Error: invalid choice for the plot (freq vs freq)!')
		elif x == 'time': xlabel = 'Time'
	elif y == 'time':
		ylabel = 'Time'
		if x == 'phase':  xlabel = 'Pulse Phase'
		elif x == 'freq': xlabel = 'Frequency'
		elif x == 'time': raise MiscError('Error: invalid choice for the plot (time vs time)!')

	
	# Sort observations by epoch
	epochs = [get_epoch(archive) for archive in archives]
	epochs = numpy.array(epochs)
	idx    = numpy.argsort(epochs)

	
	# Now extract the data and plot the results
	import matplotlib
	if graph is None: 
		if matplotlib.get_bandend() == 'QtAgg': pass
		else:                                   matplotlib.use('QtAgg') 
	else:             
		if matplotlib.get_backend() == 'agg': pass
		else:                                 matplotlib.use('agg')
	from matplotlib import pyplot as P
	import matplotlib.cm as cm
	from matplotlib.patches import Rectangle
	
	P.rcParams["xtick.major.size"] = 6
	P.rcParams["ytick.major.size"] = 6
	P.rcParams["xtick.minor.size"] = 3
	P.rcParams["ytick.minor.size"] = 3
	P.rcParams["legend.fontsize"]  = 8
	P.rcParams["font.size"]        = 12.
	P.rcParams["axes.labelsize"]   = 16.
	
	if kwargs.has_key('cm'):
		if kwargs['cm'] in dir(cm):
			cmap = kwargs['cm']
		else:
			print 'Color map %s is not a valid matplotlib color map. Reverting to %s...' % (kwargs['cm'],DEF_CM)
			cmap = DEF_CM
	else:
		cmap = DEF_CM
	
	if kwargs.has_key('dpi'): dpi = kwargs['dpi']
	else:                     dpi = DEF_DPI
	
	#
	
	if ncol is None:
		N     = len(archives)
		sqrtN = numpy.sqrt(float(N))
		if int(sqrtN)*int(sqrtN) == N:
			Nx = int(sqrtN)
			Ny = Nx
		else:
			Nx = int(numpy.floor(sqrtN) + 1.)
			Ny = float(N)/float(Nx)
			if Ny%1. != 0.: Ny = int(Ny + 1.)
			#Ny = int(numpy.floor(float(N)/float(Nx)) + 1.)
	else:
		N  = len(archives)
		Ny = int(ncol)
		
		if N%Ny == 0:
			Nx = N / Ny
		else:
			Nx = int(numpy.ceil(float(N)/float(Ny)))
	
	figx   = Ny * width
	figy   = Nx * height
	fig    = P.figure(figsize=(figx,figy))
	
	P.gca().set_xlabel(xlabel)
	P.gca().set_ylabel(ylabel)
	P.gca().xaxis.set_label_position('top') 
		
	P.setp(P.gca().get_xticklabels(),visible=False)
	P.setp(P.gca().get_yticklabels(),visible=False)
	P.setp(P.gca().xaxis.get_offset_text(),visible=False)
	P.setp(P.gca().yaxis.get_offset_text(),visible=False)
	
	P.gca().spines['top'].set_visible(False)
	P.gca().spines['bottom'].set_visible(False)
	P.gca().spines['left'].set_visible(False)
	P.gca().spines['right'].set_visible(False)
	
	P.gca().xaxis.set_major_locator(P.NullLocator())
	P.gca().yaxis.set_major_locator(P.NullLocator())
	
	if ncol is None or ncol != 1: P.subplots_adjust(left=0.1,wspace=0.1,hspace=0.1)
	else:                         P.subplots_adjust(left=0.1,wspace=0.1,hspace=0.)
	
	#
	
	j,k    = 0,1
	labels = []
	for i in idx:
		archive  = archives[i]
		print 'Working on file \'%s\'...' % archive
		freq, bw = get_frequency_info(archive)
		sub      = fig.add_subplot(Nx,Ny,j*Ny+k)
		
		j  += 1
		if j == Nx:
			j  = 0
			k += 1
		
		#
			
		xdata, ydata, extent = extract_data(archive, x, y, nobaseremove, nodedisp, rebinx, rebiny)
		shape = ydata.shape
		dim   = len(shape)
		
		# Collect rms values and eliminate statistical outliers (for this, apply a z-score test)
		if dim == 2 and clean:
			ydata = clean2D(ydata, maxz)
		
		# Data normalization
		if norm:
			if dim == 1:
				ydata = norm1D(ydata)
			elif dim == 2:
				ydata = norm2D(ydata, 0.5)
		
		# Get title
		title    = ''
		if titlepsr: 
			psr    = get_source(archive)
			if title == '': title  = psr
			else:           title += ', %s' % psr
		if titlemjd: 
			epoch  = get_epoch(archive)
			if title == '': title  = '%.0f MJD' % epoch
			else:           title += ', %.0f MJD' % epoch
		if titletobs:
			length = get_length(archive) / 60.
			if title == '': title  = '%.1f min' % length
			else:           title += ', %.1f min' % length
		if titlefreq:
			freq   = get_frequency(archive)
			if title == '': title  = '%.0f MHz' % freq
			else:           title += ', %.0f MHz' % freq
		if titlesnr: 
			snr    = get_snr(archive)
			if title == '': title  = 'SNR = %.1f' % snr
			else:           title += ', SNR = %.1f' % snr
		
		
		# Now plot the results
		if dim == 1:
			if freqcolor: 
				freqcol, freqlab = get_freq_color(freq)
				if not freqlab in labels: labels.append(freqlab)
			else:
				freqcol = 'k'
			
			sub.plot(xdata,ydata,linestyle='-',color=freqcol)
		elif dim == 2:
			sub.imshow(ydata,origin='lower',aspect='auto',cmap=cmap,extent=extent)
		
		ylim  = sub.get_ylim()
		ytext = ylim[0] + 0.875 * (ylim[1]-ylim[0])
		sub.text(0.5,ytext,title,fontsize=6,color='b',ha='center',va='center')
		P.setp(sub.get_xticklabels(),visible=False)
		P.setp(sub.get_yticklabels(),visible=False)
		P.setp(sub.xaxis.get_offset_text(),visible=False)
		P.setp(sub.yaxis.get_offset_text(),visible=False)
		
	#
	
	if dim == 1 and freqcolor:
		proxies = []
		keys    = FREQ_COLORS.keys()
		keys.sort()
		for key in keys:
			if FREQ_COLORS[key][3] in labels: proxies.append(Rectangle((0,0),1,1,fc=FREQ_COLORS[key][2]))
	
		fig.legend(proxies,labels,loc=8,ncol=len(labels),frameon=True)
	
	#
	
	if graph is None: P.show()
	else: 
		fig.savefig(graph,bbox_inches='tight',dpi=dpi)
		P.close(fig)
	return

#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	
	plotmulti(	datadir      = args.datadir, \
			dataext      = args.dataext, \
			x            = args.x, \
			y            = args.y, \
			graph        = args.graph, \
			nobaseremove = args.nobaseremove, \
			nodedisp     = args.nodedisp, \
			rebinx       = args.rebinx, \
			rebiny       = args.rebiny, \
			width        = args.width, \
			height       = args.height, \
			norm         = args.norm, \
			clean        = args.clean, \
			maxz         = args.maxz, \
			titlepsr     = args.titlepsr, \
			titlemjd     = args.titlemjd, \
			titletobs    = args.titletobs, \
			titlefreq    = args.titlefreq, \
			titlesnr     = args.titlesnr, \
			freqcolor    = args.freqcolor, \
			ncol         = args.ncol, \
			overwrite    = args.overwrite, \
			cm           = args.cm, \
			dpi          = args.dpi )
	
	goodbye()
