import os
import sys
import subprocess
import numpy
import argparse

try:
	import psrchive as p
	from misc_tools import *
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass
		
# plotone.py:  script for producing simple plots out of psrchive data.
# Author:      Lucas Guillemot
# Last update: 18 Sep 2014
# Version:     1.37



# Some default declarations
DEF_X           = 'phase'
DEF_Y           = 'intens'
DATA_CHOICE_X   = ['phase','freq','time']
DATA_CHOICE_Y   = ['intens','phase','freq','time']
DEF_GRAPH       = 'graph.png'
DEF_CM          = 'hot'
DEF_WIDTH       = 8.
DEF_HEIGHT      = 6.
DEF_DPI         = 120
DEF_MAX_ZSCORE  = 3.
PATH_TO_GNUPLOT = '/usr/bin/gnuplot'

#

def get_parser():
	parser = argparse.ArgumentParser(description='A script for producing various plots from a single data file.')
	parser.add_argument('-file',type=str,required=True,help='Input data file.')
	parser.add_argument('-x',type=str,default=DEF_X, \
				choices=DATA_CHOICE_X,help='Quantity to be plotted in the x-axis (default: \'%s\').' % DEF_X)
	parser.add_argument('-y',type=str,default=DEF_Y, \
				choices=DATA_CHOICE_Y,help='Quantity to be plotted in the y-axis (default: \'%s\').' % DEF_Y)
	parser.add_argument('-ascii',action='store_true',default=False,help='If set, will produce an ascii plot in the terminal (default: False).')
	parser.add_argument('-graph',type=str,default=DEF_GRAPH,help='Name of the output graph. If None, will run in interactive mode (default: \'%s\').' % DEF_GRAPH)
	parser.add_argument('-nobaseremove',action='store_true',default=False,help='Whether or not the baseline should be removed (default: False).')
	parser.add_argument('-nodedisp',action='store_true',default=False,help='Whether or not the data should be dedispersed (default: False).')
	parser.add_argument('-rebinx',type=int,default=1,help='Rebin the data in the x-direction by this factor (default: 1).')
	parser.add_argument('-rebiny',type=int,default=1,help='Rebin the data in the y-direction by this factor (default: 1).')
	parser.add_argument('-width',type=float,default=DEF_WIDTH,help='Width of the graph in inches (default: %f).' % DEF_WIDTH)
	parser.add_argument('-height',type=float,default=DEF_HEIGHT,help='Height of the graph in inches (default: %f).' % DEF_HEIGHT)
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
	parser.set_defaults(titlefreq=False)
		
	parser.add_argument('-titlesnr',action='store_true',dest='titlesnr',help='If set, the SNR will be given in subplot titles (default: False).')
	parser.add_argument('-notitlesnr',action='store_false',dest='titlesnr')
	parser.set_defaults(titlesnr=False)
	
	parser.add_argument('-cm',type=str,default=DEF_CM,help='Matplotlib color map to use (default: \'%s\').' % DEF_CM)
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	return parser

#

def extract_data(	archive, \
			x            = DEF_X, \
			y            = DEF_Y, \
			nobaseremove = False, \
			nodedisp     = False, \
			rebinx       = 1, \
			rebiny       = 1, \
			rotation     = None):

	# Make some tests
	if not os.path.exists(archive): raise ExistError('Error: file does not exist!')
		
	try:
		arch = load_archive(archive)
	except:
		raise PsrchiveError('Error: file does not seem to be a valid psrchive file!')
	
	if x not in DATA_CHOICE_X or y not in DATA_CHOICE_Y: raise MiscError('Error: not implemented yet.')
	
	if rebinx > 1:
		if x == 'phase':
			nbins = arch.get_nbin()
			if nbins % rebinx != 0: raise MiscError('Error: number of phase bins not a multiple of rebinning factor.')
			arch.bscrunch_to_nbin(nbins/rebinx)
		elif x == 'freq':
			nchan = arch.get_nchan()
			if nchan % rebinx != 0: raise MiscError('Error: number of frequency channels not a multiple of rebinning factor.')
			arch.fscrunch_to_nchan(nchan/rebinx)
		elif x == 'time':
			nsubint = arch.get_nsubint()
			if nsubint % rebinx != 0: raise MiscError('Error: number of subintegrations not a multiple of rebinning factor.')
			arch.tscrunch_to_nsub(nsubint/rebinx)
	
	if rebiny > 1:
		if y == 'phase':
			nbins = arch.get_nbin()
			if nbins % rebiny != 0: raise MiscError('Error: number of phase bins not a multiple of rebinning factor.')
			arch.bscrunch_to_nbin(nbins/rebiny)
		elif y == 'freq':
			nchan = arch.get_nchan()
			if nchan % rebiny != 0: raise MiscError('Error: number of frequency channels not a multiple of rebinning factor.')
			arch.fscrunch_to_nchan(nchan/rebiny)
		elif y == 'time':
			nsubint = arch.get_nsubint()
			if nsubint % rebiny != 0: raise MiscError('Error: number of subintegrations not a multiple of rebinning factor.')
			arch.tscrunch_to_nsub(nsubint/rebiny)	
	
	if rotation is not None:
		try:
			rotation = float(rotation)
		except:
			raise MiscError('Failed to convert parameter rotation into a float.')
	
	# Now prepare the data
	if rotation is not None: arch.rotate_phase(rotation)
	
	if not nobaseremove: arch.remove_baseline()
	if not nodedisp: arch.dedisperse()
	arch.pscrunch()
	
	xdata  = []
	ydata  = []
	extent = []
	
	if y == 'intens':
		if x == 'phase':
			nbins  = arch.get_nbin()
			arch.tscrunch()
			arch.fscrunch()
			xdata  = numpy.linspace(0.,1.,nbins,endpoint=False)
			ydata  = numpy.ndarray.flatten(arch.get_data())
		elif x == 'freq':
			freq   = arch.get_centre_frequency()
			bw     = arch.get_bandwidth()
			nchan  = arch.get_nchan()
			arch.bscrunch_to_nbin(1)
			arch.tscrunch()
			xdata  = numpy.linspace(freq-0.5*bw,freq+0.5*bw,nchan,endpoint=False)
			ydata  = numpy.ndarray.flatten(arch.get_data())
		elif x == 'time':
			length  = arch.integration_length() / 60.
			nsubint = arch.get_nsubint()
			arch.bscrunch_to_nbin(1)
			arch.fscrunch()
			xdata  = numpy.linspace(0.,length,nsubint,endpoint=False)
			ydata  = numpy.ndarray.flatten(arch.get_data())
	elif y == 'phase':
		if x == 'phase':
			raise MiscError('Error: invalid choice for the plot (phase vs phase)!')
		elif x == 'freq':
			freq   = arch.get_centre_frequency()
			bw     = arch.get_bandwidth()
			arch.tscrunch()
			ydata  = arch.get_data()[0,0,:,:]
			ydata  = numpy.transpose(ydata)
			extent = [freq-0.5*bw,freq+0.5*bw,0.,1.]
		elif x == 'time':
			length = arch.integration_length() / 60.
			arch.fscrunch()
			ydata  = arch.get_data()[:,0,0,:]
			ydata  = numpy.transpose(ydata)
			extent = [0.,length,0.,1.]
	elif y == 'freq':
		freq   = arch.get_centre_frequency()
		bw     = arch.get_bandwidth()
		
		if x == 'phase':
			arch.tscrunch()
			ydata  = arch.get_data()[0,0,:,:]
			extent = [0.,1.,freq-0.5*bw,freq+0.5*bw]
		elif x == 'freq':
			raise MiscError('Error: invalid choice for the plot (freq vs freq)!')
		elif x == 'time':
			length = arch.integration_length() / 60.
			arch.bscrunch_to_nbin(1)
			ydata  = arch.get_data()[:,0,:,0]
			ydata  = numpy.transpose(ydata)
			extent = [0.,length,freq-0.5*bw,freq+0.5*bw]
	elif y == 'time':
		length = arch.integration_length() / 60.
		
		if x == 'phase':
			arch.fscrunch()
			ydata  = arch.get_data()[:,0,0,:]
			extent = [0.,1.,0.,length]
		elif x == 'freq':
			freq   = arch.get_centre_frequency()
			bw     = arch.get_bandwidth()
			arch.bscrunch_to_nbin(1)
			ydata  = arch.get_data()[:,0,:,0]
			extent = [freq-0.5*bw,freq+0.5*bw,0.,length]
		elif x == 'time':
			raise MiscError('Error: invalid choice for the plot (time vs time)!')
			
	return xdata, ydata, extent
	

#

def plotthree(	archive, \
		graph        = DEF_GRAPH, \
		nobaseremove = False, \
		nodedisp     = False, \
		rebinx       = 1, \
		rebint       = 1, \
		rebinf       = 1, \
		width        = 3.*DEF_WIDTH, \
		height       = DEF_HEIGHT, \
		norm         = False, \
		clean        = False, \
		maxz         = DEF_MAX_ZSCORE, \
		**kwargs):
		
	# Get the data first
	xdata1, ydata1, extent1 = extract_data(archive, 'phase', 'intens', nobaseremove, nodedisp, rebinx, 1)
	xdata2, ydata2, extent2 = extract_data(archive, 'phase', 'time',   nobaseremove, nodedisp, rebinx, rebint)
	xdata3, ydata3, extent3 = extract_data(archive, 'phase', 'freq',   nobaseremove, nodedisp, rebinx, rebinf)
	
	xdatas  = [xdata1,xdata2,xdata3]
	ydatas  = [ydata1,ydata2,ydata3]
	exts    = [extent1,extent2,extent3]
	xlabels = ['Pulse Phase','Pulse Phase','Pulse Phase']
	ylabels = ['Intensity (a. u.)','Time (minutes)','Frequency (MHz)']
	
	#
	
	import matplotlib
	if graph is None: 
		if matplotlib.get_backend() == 'QtAgg': pass
		else:                                   matplotlib.use('QtAgg') 
	else:
		if matplotlib.get_backend() == 'agg': pass
		else:                                 matplotlib.use('agg')
	from matplotlib import pyplot as P
	P.rcParams["xtick.major.size"] = 6
	P.rcParams["ytick.major.size"] = 6
	P.rcParams["xtick.minor.size"] = 3
	P.rcParams["ytick.minor.size"] = 3
	P.rcParams["font.size"]        = 12.
	P.rcParams["axes.labelsize"]   = 16.
	
	if kwargs.has_key('dpi'): dpi = kwargs['dpi']
	else:                     dpi = DEF_DPI
	
	import matplotlib.cm as cm
	if kwargs.has_key('cm'):
		if kwargs['cm'] in dir(cm):
			cmap = kwargs['cm']
		else:
			print 'Color map %s is not a valid matplotlib color map. Reverting to %s...' % (kwargs['cm'],DEF_CM)
			cmap = DEF_CM
	else:
		cmap = DEF_CM
	
	fig = P.figure(figsize=(width,height))
	
	#
	
	for xdata, ydata, extent, xlabel, ylabel, idx in zip(xdatas,ydatas,exts,xlabels,ylabels,range(1,4)):
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
				ydata = norm2D(ydata,0.5)
				
		# Now plot the data
		ax = fig.add_subplot(1,3,idx)
		
		if dim == 1:
			ax.plot(xdata,ydata,'k-')
		elif dim == 2:
			ax.get_xaxis().set_tick_params(which='both',direction='out')
			ax.get_yaxis().set_tick_params(which='both',direction='out')
			ax.imshow(ydata,origin='lower',aspect='auto',cmap=cmap,extent=extent,interpolation='nearest')
	
		ax.set_xlabel(xlabel)
		ax.set_ylabel(ylabel)
		ax.minorticks_on()
	
	if graph is None: P.show()
	else: 
		fig.savefig(graph,bbox_inches='tight',dpi=dpi)
		P.close(fig)
	return
				
		
	

#

def plotone(	archive, \
		x            = DEF_X, \
		y            = DEF_Y, \
		ascii        = False, \
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
		**kwargs):
	
	# First make some tests
	if ascii:
		if y != 'intens':
			raise MiscError('Ascii output only implemented for 1D plot')
			
		if not os.path.exists(PATH_TO_GNUPLOT):
			raise MiscError('Error: gnuplot not found.')
		
	# Get the data first
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
	
	# Get axis labels
	if y == 'intens':
		ylabel = 'Intensity (a. u.)'
		if x == 'phase':  xlabel = 'Pulse Phase'
		elif x == 'freq': xlabel = 'Frequency (MHz)'
		elif x == 'time': xlabel = 'Time (minutes)'
	elif y == 'phase':
		ylabel = 'Pulse Phase'
		if x == 'phase':  raise MiscError('Error: invalid choice for the plot (phase vs phase)!')
		elif x == 'freq': xlabel = 'Frequency (MHz)'
		elif x == 'time': xlabel = 'Time (minutes)'
	elif y == 'freq':
		ylabel = 'Frequency (MHz)'
		if x == 'phase':  xlabel = 'Pulse Phase'
		elif x == 'freq': raise MiscError('Error: invalid choice for the plot (freq vs freq)!')
		elif x == 'time': xlabel = 'Time (minutes)'
	elif y == 'time':
		ylabel = 'Time (minutes)'
		if x == 'phase':  xlabel = 'Pulse Phase'
		elif x == 'freq': xlabel = 'Frequency (MHz)'
		elif x == 'time': raise MiscError('Error: invalid choice for the plot (time vs time)!')
	
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
	if ascii:
		gnuplot = subprocess.Popen([PATH_TO_GNUPLOT],stdin=subprocess.PIPE)
		gnuplot.stdin.write("set term dumb 96 48\n")
		gnuplot.stdin.write("set xlabel \"%s\"\n" % xlabel)
		gnuplot.stdin.write("set ylabel \"%s\"\n" % ylabel)
		
		if dim == 1:
			gnuplot.stdin.write("plot '-' using 1:2 with linespoints \n")
			for xdat, ydat in zip(xdata,ydata): gnuplot.stdin.write("%f %f\n" % (xdat,ydat))
			gnuplot.stdin.write("e\n")
		
		gnuplot.stdin.flush()
		return
	
	# If not ascii output, use matplotlib
	import matplotlib
	if graph is None: 
		if matplotlib.get_backend() == 'QtAgg': pass
		else:                                   matplotlib.use('QtAgg') 
	else:
		if matplotlib.get_backend() == 'agg': pass
		else:                                 matplotlib.use('agg')
	from matplotlib import pyplot as P
	P.rcParams["xtick.major.size"] = 6
	P.rcParams["ytick.major.size"] = 6
	P.rcParams["xtick.minor.size"] = 3
	P.rcParams["ytick.minor.size"] = 3
	P.rcParams["font.size"]        = 12.
	P.rcParams["axes.labelsize"]   = 16.
	
	if kwargs.has_key('dpi'): dpi = kwargs['dpi']
	else:                     dpi = DEF_DPI

	fig = P.figure(figsize=(width,height))
	ax  = fig.add_subplot(111)
	
	if dim == 1:
		ax.plot(xdata,ydata,'k-')
	elif dim == 2:
		import matplotlib.cm as cm
		
		if kwargs.has_key('cm'):
			if kwargs['cm'] in dir(cm):
				cmap = kwargs['cm']
			else:
				print 'Color map %s is not a valid matplotlib color map. Reverting to %s...' % (kwargs['cm'],DEF_CM)
				cmap = DEF_CM
		else:
			cmap = DEF_CM
		
		ax.get_xaxis().set_tick_params(which='both',direction='out')
		ax.get_yaxis().set_tick_params(which='both',direction='out')
		ax.imshow(ydata,origin='lower',aspect='auto',cmap=cmap,extent=extent,interpolation='nearest')
	
	if xlabel is not None: ax.set_xlabel(xlabel)
	if ylabel is not None: ax.set_ylabel(ylabel)
	
	ylim  = ax.get_ylim()
	ytext = ylim[0] + 0.95 * (ylim[1]-ylim[0])
	titleobj = fig.suptitle(title,fontsize=10,ha='center',va='center')
	
	ax.minorticks_on()
	
	if graph is None: P.show()
	else: 
		fig.savefig(graph,bbox_inches='tight',dpi=dpi,bbox_extra_artists=[titleobj])
		P.close(fig)
	
	return
	
	
#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()
	
	
	plotone(	args.file, \
			x            = args.x, \
			y            = args.y, \
			ascii        = args.ascii, \
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
			cm           = args.cm, \
			dpi          = args.dpi)
	
	goodbye()
