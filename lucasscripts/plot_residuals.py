import os
import sys
import numpy
import commands
import datetime
import argparse
import statsmodels.api as sm

# TODO:
# multiple par files

try:
	from misc_tools import *
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass


# plot_residuals.py: script for plotting TOA residuals and calculating various statistics.
# Author:            Lucas Guillemot
# Last update:       4 Nov 2014
# Version:           1.1




# Some default declarations
DEF_WMIN           = 1.e-3
DEF_OUTPUT_WEIGHTS = None
DEF_OUTPUT_FLAGGED = None
DEF_OUTPUT_STATS   = None
DEF_OUTPUT_TIM     = None
DEF_PGRAM_PTS      = 1000
DEF_BINOPHASE      = 0
DEF_BINDOY         = 0
DEF_GRAPH          = 'residuals.svg'
DEF_WIDTH          = 16.
DEF_HEIGHT         = 24.
DEF_POINTSIZE      = 3.
DEF_DPI            = 120

#

def get_parser():
	parser = argparse.ArgumentParser(description='a script for plotting TOA residuals and calculating various statistics.')
	parser.add_argument('-parfile',type=str,required=True,help='Path to a tempo2 par file to use for calculating the residuals.')
	parser.add_argument('-timfile',type=str,required=True,help='Path to a tim file containing the TOA information.')
	
	parser.add_argument('-preres',action='store_true',dest='preres',help='If set, use pre-fit residuals in the analysis (default: True).')
	parser.add_argument('-postres',action='store_false',dest='preres',help='If set, use post-fit residuals in the analysis instead (default: False).')
	parser.set_defaults(preres=True)
	
	parser.add_argument('-discard_flagged',action='store_true',dest='discard_flagged',help='If set, TOAs flagged as bad will be discarded from the analysis (default: False).')
	parser.set_defaults(discard_flagged=False)
	
	parser.add_argument('-wmin',type=float,default=DEF_WMIN,help='TOAs with weights as calculated from a robust linear regression smaller than this value will be discarded (default: %le).' % DEF_WMIN)
	parser.add_argument('-output_weights',type=str,default=DEF_OUTPUT_WEIGHTS,help='Name of an output file to store the weight information in (default: \'%s\').' % DEF_OUTPUT_WEIGHTS)
	parser.add_argument('-output_flagged',type=str,default=DEF_OUTPUT_FLAGGED,help='Name of an output file to store information on the archives flagged as bad in (default: \'%s\').' % DEF_OUTPUT_FLAGGED)
	parser.add_argument('-output_stats',type=str,default=DEF_OUTPUT_STATS,help='Name of an output file to store TOA statistics in (default: \'%s\').' % DEF_OUTPUT_STATS)
	parser.add_argument('-output_tim',type=str,default=DEF_OUTPUT_TIM,help='Name of an output file to store selected TOAs in (default: \'%s\').' % DEF_OUTPUT_TIM)
	parser.add_argument('-pgrampts',type=int,default=DEF_PGRAM_PTS,help='Number of frequency values to be used for calculating the periodogram (default: %d).' % DEF_PGRAM_PTS)
	parser.add_argument('-binophase',type=int,default=DEF_BINOPHASE,help='If set, will bin the residuals in orbital phase by this amount (default: %d).' % DEF_BINOPHASE)
	parser.add_argument('-bindoy',type=int,default=DEF_BINDOY,help='If set, will bin the residuals in doy of year (default: %d).' % DEF_BINDOY)
	parser.add_argument('-graph',type=str,default=DEF_GRAPH,help='Name of the output graph showing the analysis results (default: \'%s\').' % DEF_GRAPH)
	parser.add_argument('-width',type=float,default=DEF_WIDTH,help='Width of the graph in inches (default: %f).' % DEF_WIDTH)
	parser.add_argument('-height',type=float,default=DEF_HEIGHT,help='Height of the graph in inches (default: %f).' % DEF_HEIGHT)
	parser.add_argument('-pointsize',type=float,default=DEF_POINTSIZE,help='Size of the points in the residuals plots (default: %f).' % DEF_POINTSIZE)
	parser.add_argument('-urlprefix',type=str,default=None,help='Prefix for the destination URLs, for svg outputs (default: None).')
	parser.add_argument('-urlsuffix',type=str,default=None,help='Suffix for the destination URLs, for svg outputs (default: None).')
	parser.add_argument('-dpi',type=int,default=DEF_DPI,help='Dots per inches for the output plot (default: %d).' % DEF_DPI)
	parser.add_argument('-overwrite',action='store_true',default=False,help='Whether or not the output files should be overwritten (default: False).')
	return parser

#

def plot_residuals(	parfile, \
			timfile, \
			preres          = True, \
			discard_flagged = False, \
			wmin            = DEF_WMIN, \
			output_weights  = DEF_OUTPUT_WEIGHTS, \
			output_flagged  = DEF_OUTPUT_FLAGGED, \
			output_stats    = DEF_OUTPUT_STATS, \
			output_tim      = DEF_OUTPUT_TIM, \
			pgrampts        = DEF_PGRAM_PTS, \
			binophase       = DEF_BINOPHASE, \
			bindoy          = DEF_BINDOY, \
			graph           = DEF_GRAPH, \
			width           = DEF_WIDTH, \
			height          = DEF_HEIGHT, \
			pointsize       = DEF_POINTSIZE, \
			urlprefix       = None, \
			urlsuffix       = None, \
			overwrite       = False, \
			**kwargs ):
		
	# Make some tests
	if not os.path.exists(parfile):
		print 'Error: par file does not exist! Exiting...'
		raise ExistError('Par file does not exist! Exiting...')
	
	if not os.path.exists(timfile):
		print 'Error: tim file does not exist! Exiting...'
		raise ExistError('Tim file does not exist! Exiting...')
	
	if output_weights is not None and os.path.exists(output_weights):
		if overwrite: os.unlink(output_weights)
		else:
			raise AlreadyExistError('Output file of weights already exists. Exiting...')
	
	if output_weights is not None:
		tempdir = os.path.dirname(output_weights)
		if tempdir != '' and not os.path.isdir(tempdir):
			os.mkdir(tempdir)
	
	if output_flagged is not None and os.path.exists(output_flagged):
		if overwrite: os.unlink(output_flagged)
		else:
			raise AlreadyExistError('Output file of flagged archives already exists. Exiting...')
	
	if output_flagged is not None:
		tempdir = os.path.dirname(output_flagged)
		if tempdir != '' and not os.path.isdir(tempdir):
			os.mkdir(tempdir)
			
	if output_stats is not None and os.path.exists(output_stats):
		if overwrite: os.unlink(output_stats)
		else:
			raise AlreadyExistError('Output file of TOA statistics already exists. Exiting...')
	
	if output_stats is not None:
		tempdir = os.path.dirname(output_stats)
		if tempdir != '' and not os.path.isdir(tempdir):
			os.mkdir(tempdir)
			
	if output_tim is not None and os.path.exists(output_tim):
		if overwrite: os.unlink(output_tim)
		else:
			raise AlreadyExistError('Output file of selected TOAs already exists. Exiting...')
	
	if output_tim is not None:
		tempdir = os.path.dirname(output_tim)
		if tempdir != '' and not os.path.isdir(tempdir):
			os.mkdir(tempdir)
	
	if binophase < 0 or binophase == 1:
		raise MiscError('binophase parameter must be greater than 1!')
	
	if bindoy < 0 or bindoy == 1:
		raise MiscError('bindoy parameter must be greater than 1!')
	
	if graph is not None and os.path.exists(graph):
		if overwrite: os.unlink(graph)
		else:
			raise AlreadyExistError('Output plot already exists. Exiting...')
	
	if graph is not None:
		tempdir = os.path.dirname(graph)
		if tempdir != '' and not os.path.isdir(tempdir):
			os.mkdir(tempdir)

	if graph is not None:
		graphext = os.path.splitext(graph)[1]
		if graphext.upper() == '.SVG': svg_enabled = True
		else:                          svg_enabled = False
	else:
		svg_enabled = False
		
	
	# Run tempo2 to get pre- and post-fit residuals
	nobs             = get_number_toas(timfile)
	tmpfile          = 'TeMp.DaT'
	t2cmd            = '''tempo2 -output general2 -nofit -f %s %s -nobs %d -s \"residuals {FILE} {SAT} {BAT} {FREQ} {PRE} {POST} {ERR} {BINPHASE}\\n\" |grep residuals > %s'''
	cmd              = t2cmd % (parfile,timfile,nobs+2,tmpfile)
	print '\nRunning tempo2 with command: %s ...\n' % cmd
	os.system(cmd)
	
	# Now read the data
	dtype            = [('datafile',object),('sat',numpy.float64),('bat',numpy.float64),('freq',float),('preres',float),('postres',float),('uncres',float),('binphase',float)]
	
	try:
		data     = numpy.genfromtxt(tmpfile,dtype=dtype,usecols=(1,2,3,4,5,6,7,8),unpack=True)
		os.unlink(tmpfile)
	except:
		print 'Error encountered while running tempo2. Exiting...'
		raise MiscError('Error encountered while running tempo2. Exiting...')
	
	#
	
	f0               = get_freq_from_parfile(parfile,epoch=0.5*(data['bat'].min()+data['bat'].max()))
	nobs_orig        = len(data)
	nobs             = len(data)
	
	if preres: res   = data['preres']  / 1.e-6
	else:      res   = data['postres'] / 1.e-6
	wavg             = numpy.average(res,weights=1./data['uncres'])
	res             -= wavg
	unc              = data['uncres']
	
	years            = [mjd_to_year(data['bat'][i]) for i in xrange(nobs)]
	years            = numpy.array(years)
	doys             = [mjd_to_doy(data['bat'][i]) for i in xrange(nobs)]
	doys             = numpy.array(doys)
	colors           = [get_freq_color(data['freq'][i])[0] for i in xrange(nobs)]
	colors           = numpy.array(colors)
	for i in xrange(nobs): 
		if numpy.isinf(data['binphase'][i]): data['binphase'][i] = -1.
	
	# Flag outliers
	rlmx             = data['bat'] - 0.5*(data['bat'].min()+data['bat'].max())
	rlmx             = sm.add_constant(rlmx)
	rlmfit           = sm.RLM(res,rlmx,M=sm.robust.norms.AndrewWave()).fit()
	params           = rlmfit.params
	weights          = rlmfit.weights
	#print rlmfit.summary(yname='y',xname=['var_%d' % i for i in range(len(rlmfit.params))])
	
	if output_weights is not None:
		outf     = open(output_weights,'w+')
		outf.write('# ARCHIVE SAT BAT RES FREQ ERR WEIGHT\n')
		for i in xrange(len(weights)): 
			if discard_flagged and weights[i] < wmin: continue
			outf.write('%-50s %.9f\t%.9f\t%15.3f\t%.3f\t%.3f\t%.3f\n' % (data['datafile'][i],data['sat'][i],data['bat'][i],res[i],data['freq'][i],data['uncres'][i],weights[i]))
		outf.close()
	
	flagged_idx      = weights < wmin
	flagged_files    = data['datafile'][flagged_idx]
	flagged_sats     = data['sat'][flagged_idx]
	flagged_bats     = data['bat'][flagged_idx]
	flagged_preres   = data['preres'][flagged_idx]
	flagged_postres  = data['postres'][flagged_idx]
	flagged_binphase = data['binphase'][flagged_idx]
	flagged_res      = res[flagged_idx]
	flagged_doys     = doys[flagged_idx]	
	flagged_freqs    = data['freq'][flagged_idx]
	flagged_uncres   = data['uncres'][flagged_idx]
	flagged_weights  = weights[flagged_idx]
	nflagged         = len(flagged_files)
	
	if discard_flagged:
		idx      = numpy.invert(flagged_idx)
		data     = data[idx]
		res      = res[idx]
		unc      = unc[idx]
		years    = years[idx]
		doys     = doys[idx]
		colors   = colors[idx]
		nobs     = len(data)
	
	if output_flagged is not None:
		outf     = open(output_flagged,'w+')
		outf.write('# ARCHIVE SAT BAT RES FREQ ERR WEIGHT\n')
		for i in xrange(nflagged): outf.write('%-50s %.9f\t%.9f\t%15.3f\t%.3f\t%.3f\t%.3f\n' % (flagged_files[i],flagged_sats[i],flagged_bats[i],res[i],flagged_freqs[i],flagged_uncres[i],flagged_weights[i]))
		outf.close()
	
	# Bin the data in orbital phase and day of year
	if binophase > 0:
		ophase_bins_lo    = numpy.linspace(0.,1.,binophase,endpoint=False)
		ophase_bins_hi    = ophase_bins_lo + (ophase_bins_lo[1]-ophase_bins_lo[0])
		binned_ophase_res = numpy.zeros(binophase)
		binned_ophase_unc = numpy.zeros(binophase)
		
		for i in range(binophase):
			blo  = ophase_bins_lo[i]
			bhi  = ophase_bins_hi[i]
			idx  = (data['binphase'] >= blo) & (data['binphase'] < bhi)
			
			res2 = res[idx]
			if len(res2) == 0: continue
			unc2 = unc[idx]
			
			binned_ophase_res[i] = numpy.average(res2,weights=1./unc2)
			binned_ophase_unc[i] = numpy.sqrt(float(len(res2))) / (1./unc2).sum()
	
	if bindoy > 0:
		doy_bins_lo    = numpy.linspace(0.,366.,bindoy,endpoint=False)
		doy_bins_hi    = doy_bins_lo + (doy_bins_lo[1]-doy_bins_lo[0])
		binned_doy_res = numpy.zeros(bindoy)
		binned_doy_unc = numpy.zeros(bindoy)
		
		for i in range(bindoy):
			blo  = doy_bins_lo[i]
			bhi  = doy_bins_hi[i]
			idx  = (doys >= blo) & (doys < bhi)
			
			res2 = res[idx]
			if len(res2) == 0: continue
			unc2 = unc[idx]
			
			binned_doy_res[i] = numpy.average(res2,weights=1./unc2)
			binned_doy_unc[i] = numpy.sqrt(float(len(res2))) / (1./unc2).sum()
			
	
	# Calculate the periodogram
	idx              = numpy.argsort(data['bat'])
	sorted_bats      = data['bat'][idx]
	spanmax          = sorted_bats.max() - sorted_bats.min()
	spanmin          = (sorted_bats[1:]-sorted_bats[:-1]).min()
	spanmin          = max(spanmin,0.5/24.)
	pgram_times      = numpy.logspace(numpy.log10(spanmin),numpy.log10(spanmax),pgrampts)
	pgram_freqs      = 1./pgram_times
	pgram            = periodogram(data['bat'],res,data['uncres'],pgram_freqs)
	maxidx           = numpy.argmax(pgram)
	
	# Characterize the residuals (rms, red chisq, etc.)
	wgt, sumwgt, sum_pre, sumsq_pre, rms_pre, chisq_pre = 0., 0., 0., 0., 0., 0.
	
	dist             = res / data['uncres']
	nfree            = get_number_free_parameters(parfile)
	absdist          = numpy.abs(dist)
	idx              = numpy.argsort(absdist)
	sorted_absdist   = absdist[idx]
	sorted_res       = res[idx]
	sorted_unc       = data['uncres'][idx]
	wrms             = []
	redchisq         = []
	
	for i in range(nobs):
		wgt        = 1./(sorted_unc[i]*sorted_unc[i])
		sumsq_pre += wgt*sorted_res[i]*sorted_res[i]
		sum_pre   += wgt*sorted_res[i]
		sumwgt    += wgt
		
		rms_pre    = numpy.sqrt((sumsq_pre-sum_pre*sum_pre/sumwgt)/sumwgt)
		wrms.append(rms_pre)
		
		chisq_pre += ((sorted_res[i] - sum_pre / sumwgt) / sorted_unc[i])**2.
		dof        = (i+1) - nfree - 1
		if dof <= 0: rchisq_pre = -1.
		else:        rchisq_pre = chisq_pre / float(dof)
		
		redchisq.append(rchisq_pre)
	
	wrms             = numpy.array(wrms)
	redchisq         = numpy.array(redchisq) 
	
		
	# Save the selected TOAs into a tim file
	if output_tim is not None:
		TOAdata          = read_TOA_data(timfile,keep_commented=False)
		outf             = open(output_tim,'w+')
		outf.write('FORMAT 1\n')
		
		if nflagged == 0:
			for elem in TOAdata:
				outf.write(elem)
		else:
			for elem in TOAdata:
				if 'ref_mjd' in elem: continue
				elemdata  = elem.split()
				freq      = elemdata[1]
				epoch     = elemdata[2]
				dep       = numpy.abs(flagged_sats - numpy.float64(epoch))
				i         = numpy.argmin(dep)
				defr      = numpy.abs(flagged_freqs - numpy.float(freq))[i]
				if dep[i] < 1.e-6 and defr < 1.: elem = '# ' + elem
				outf.write(elem)
		outf.close()
	
	
	# Now get the statistics
	line    = 'Statistics:\n'
	line   += '-----------\n'
	line   += 'Total number of TOAs:      ' + str(nobs_orig) + '\n'
	line   += 'Number of selected TOAs:   ' + str(nobs) + '\n'
	line   += 'Number of flagged TOAs:    ' + str(nflagged) + '\n'
	line   += 'Min. epoch (MJD):          ' + str(data['bat'].min()) + '\n'
	line   += 'Max. epoch (MJD):          ' + str(data['bat'].max()) + '\n'
	
	minerr  = data['uncres'].min()
	maxerr  = data['uncres'].max()
	avgerr  = data['uncres'].mean()
	mederr  = numpy.median(data['uncres'])
	stderr  = data['uncres'].std()
	line   += 'Min. TOA error (mu-s):     ' + str(minerr) + '\n'
	line   += 'Max. TOA error (mu-s):     ' + str(maxerr) + '\n'
	line   += 'Avg. TOA error (mu-s):     ' + str(avgerr) + '\n'
	line   += 'Median TOA error (mu-s):   ' + str(mederr) + '\n'
	line   += 'Stddev. TOA error (mu-s):  ' + str(stderr) + '\n'
	
	line   += 'Weighted RMS (mu-s):       ' + str(wrms[-1])
	if preres: line += ' (Pre-fit)\n'
	else:      line += ' (Post-fit)\n'
	
	line   += 'Reduced chi-squared:       ' + str(redchisq[-1])
	if preres: line += ' (Pre-fit)\n'
	else:      line += ' (Post-fit)\n'
	
	line   += 'Max. power in periodogram: ' + str(pgram[maxidx]) + '\n'
	line   += 'Frequency (per day):       ' + str(pgram_freqs[maxidx]) + '\n'
	line   += 'Period (day):              ' + str(pgram_times[maxidx]) + '\n'
	
	print line
	if output_stats is not None:
		outf = open(output_stats,'w+')
		outf.write(line + '\n')
		outf.close()
	
	# Now let's plot the results!
	import matplotlib
	if graph is None: 
		if matplotlib.get_backend() == 'QtAgg': pass
		else:                                   matplotlib.use('QtAgg') 
	else:
		if matplotlib.get_backend() == 'agg': pass
		else:                                 matplotlib.use('agg')
	
	from matplotlib import pyplot as P
	from matplotlib import ticker
	P.rcParams["xtick.major.size"] = 6
	P.rcParams["ytick.major.size"] = 6
	P.rcParams["xtick.minor.size"] = 3
	P.rcParams["ytick.minor.size"] = 3
	P.rcParams["font.size"]        = 12.
	P.rcParams["axes.labelsize"]   = 14.
	
	if kwargs.has_key('dpi'): dpi = kwargs['dpi']
	else:                     dpi = DEF_DPI
	
	fig = P.figure(figsize=(width,height))
	fig.subplots_adjust(wspace=0.35)
	
	# Residuals versus time plot
	ax1   = fig.add_subplot(511)
	xdict = {}
	ydict = {}
	rdict = {}
	fdict = {}
	cols  = []
	
	for i in xrange(nobs):
		if urlprefix is not None and urlsuffix is not None:
			plotlink  = urlprefix
			plotlink += os.path.splitext(os.path.basename(data['datafile'][i]))[0]
			plotlink += urlsuffix
			if not os.path.exists(plotlink): plotlink = None
		else:	
			plotlink = None
		
		if xdict.has_key(colors[i]):
			xdict[colors[i]].append(data['bat'][i])
			ydict[colors[i]].append(res[i])
			rdict[colors[i]].append(data['uncres'][i])
			fdict[colors[i]].append(plotlink)
		else:
			cols.append(colors[i])
			xdict[colors[i]] = [data['bat'][i]]
			ydict[colors[i]] = [res[i]]
			rdict[colors[i]] = [data['uncres'][i]]
			fdict[colors[i]] = [plotlink]
	
	if not svg_enabled:
		for i, col in enumerate(cols):
			ax1.errorbar(	xdict[col], \
					ydict[col], \
					yerr       = rdict[col], \
					color      = col, \
					ecolor     = col, \
					capsize    = 2.,\
					linewidth  = 0.,\
					elinewidth = 1.,\
					marker     = 's',\
					mew        = 0.,\
					ms         = pointsize )
		
		if not discard_flagged and nflagged > 0:
			ax1.scatter(flagged_bats,flagged_res,marker='o',s=64.,c='r')
	else:
		if not discard_flagged and nflagged > 0:
			ax1.scatter(flagged_bats,flagged_res,marker='o',s=64.,c='r')
			
		for i, col in enumerate(cols):
			sc   = ax1.scatter(	xdict[col], \
						ydict[col], \
						color        = col, \
						marker       = 's', \
						linewidth    = 0., \
						s            = 2.*pointsize*pointsize )
			
			sc.set_urls(fdict[col])
			
			ax1.errorbar(	xdict[col], \
					ydict[col], \
					yerr       = rdict[col], \
					fmt        = None, \
					color      = col, \
					ecolor     = col, \
					capsize    = 2.,\
					linewidth  = 0.,\
					elinewidth = 1. )
	
	dt   = data['bat'].max() - data['bat'].min()
	tmin = data['bat'].min() - 0.05 * dt
	tmax = data['bat'].max() + 0.05 * dt
	
	dr   = (res+data['uncres']).max() - (res-data['uncres']).min()
	rmin = (res-data['uncres']).min() - 0.1 * dr
	rmax = (res+data['uncres']).max() + 0.1 * dr
	
	ax1.set_xlim([tmin,tmax])
	ax1.set_xlabel('Time (MJD)')
	ax1.set_ylim([rmin,rmax])
	if preres: reslabel = 'Pre-fit residuals ($\mu$s)'
	else:      reslabel = 'Post-fit residuals ($\mu$s)'
	ax1.set_ylabel(reslabel)
	ax1.ticklabel_format(useOffset=False)
	ax1.text(0.5*(tmin+tmax),rmax-0.1*dr,'W$_\mathrm{rms}$ = %.3f $\mu$s' % wrms[-1],ha='center',va='center')
	ax1.minorticks_on()
	
	ax1bisy = ax1.twiny()
	xlim    = ax1.get_xlim()
	ax1bisy.set_xlim([mjd_to_year(xlim[0]),mjd_to_year(xlim[1])])
	ax1bisy.set_xlabel('Year')
	ax1bisy.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
	ax1bisy.xaxis.set_minor_locator(ticker.MultipleLocator(1./12.))
	ax1bisy.ticklabel_format(useOffset=False)
	
	ax1bisx = ax1.twinx()
	ylim    = ax1.get_ylim()
	pmin    = f0 * ylim[0] * 1e-6
	pmax    = f0 * ylim[1] * 1e-6
	ax1bisx.set_ylim([pmin,pmax])
	ax1bisx.set_ylabel('Pulse periods')
	ax1bisx.ticklabel_format(useOffset=False)
	ax1bisx.minorticks_on()
	
	# Histogram of residuals
	ax2 = fig.add_subplot(5,2,3)
	n, bins, edges = ax2.hist(res,range=[rmin,rmax],bins=50)
	ax2.set_xlim([rmin,rmax])
	ax2.set_xlabel(reslabel)
	ax2.set_ylim([0.,n.max()+1.])
	ax2.set_ylabel('Counts')
	ax2.minorticks_on()
	
	# Histogram of residual "distances"
	ax3 = fig.add_subplot(5,2,4)
	n, bins, edges = ax3.hist(dist,bins=50)
	ax3.set_xlabel('$N_\\sigma =$ (res - avg. res) / unc.')
	ax3.set_ylim([0.,n.max()+1.])
	ax3.set_ylabel('Counts')
	ax3.minorticks_on()
	
	# Plot of residuals versus binary phase
	ax4   = fig.add_subplot(5,2,5)
	
	if binophase > 0:
		if not all(binned_ophase_res[i] == 0. for i in range(binophase)):
			ax4.errorbar(	0.5*(ophase_bins_lo+ophase_bins_hi), \
					binned_ophase_res, \
					xerr       = 0.5*(ophase_bins_hi-ophase_bins_lo), \
					yerr       = binned_ophase_unc, \
					color      = 'b', \
					ecolor     = 'b', \
					capsize    = 2., \
					linewidth  = 1., \
					linestyle  = 'dashed', \
					elinewidth = 1. )
			
			dr2   = (binned_ophase_res+binned_ophase_unc).max() - (binned_ophase_res-binned_ophase_unc).min()
			rmin2 = (binned_ophase_res-binned_ophase_unc).min() - 0.1 * dr2
			rmax2 = (binned_ophase_res+binned_ophase_unc).max() + 0.1 * dr2
			ax4.set_ylim([rmin2,rmax2])
	else:
		xdict = {}
		ydict = {}
		rdict = {}
		fdict = {}
		cols  = []
		
		for i in xrange(nobs):
			if urlprefix is not None and urlsuffix is not None:
				plotlink  = urlprefix
				plotlink += os.path.splitext(os.path.basename(data['datafile'][i]))[0]
				plotlink += urlsuffix
				if not os.path.exists(plotlink): plotlink = None
			else:	
				plotlink = None
		
			if xdict.has_key(colors[i]):
				xdict[colors[i]].append(data['binphase'][i])
				ydict[colors[i]].append(res[i])
				rdict[colors[i]].append(data['uncres'][i])
				fdict[colors[i]].append(plotlink)
			else:
				cols.append(colors[i])
				xdict[colors[i]] = [data['binphase'][i]]
				ydict[colors[i]] = [res[i]]
				rdict[colors[i]] = [data['uncres'][i]]
				fdict[colors[i]] = [plotlink]
		
		if not svg_enabled:
			for i, col in enumerate(cols):
				ax4.errorbar(	xdict[col], \
						ydict[col], \
						yerr       = rdict[col], \
						color      = col, \
						ecolor     = col, \
						capsize    = 2.,\
						linewidth  = 0.,\
						elinewidth = 1.,\
						marker     = 's',\
						mew        = 0.,\
						ms         = pointsize )
			
			if not discard_flagged and nflagged > 0:
				ax4.scatter(flagged_binphase,flagged_res,marker='o',s=64.,c='r')
		else:
			if not discard_flagged and nflagged > 0:
				ax4.scatter(flagged_binphase,flagged_res,marker='o',s=64.,c='r')
				
			for i, col in enumerate(cols):
				sc   = ax4.scatter(	xdict[col], \
							ydict[col], \
							color        = col, \
							marker       = 's', \
							linewidth    = 0., \
							s            = 2.*pointsize*pointsize )
				
				sc.set_urls(fdict[col])
				
				ax4.errorbar(	xdict[col], \
						ydict[col], \
						yerr       = rdict[col], \
						fmt        = None, \
						color      = col, \
						ecolor     = col, \
						capsize    = 2.,\
						linewidth  = 0.,\
						elinewidth = 1. )
		
		ax4.set_ylim([rmin,rmax])
	
	ax4.set_xlim([0.,1.])
	ax4.set_xlabel('Orbital Phase')
	ax4.set_ylabel(reslabel)
	ax4.minorticks_on()
	
	ax4bisx = ax4.twinx()
	ylim    = ax4.get_ylim()
	pmin    = f0 * ylim[0] * 1e-6
	pmax    = f0 * ylim[1] * 1e-6
	ax4bisx.set_ylim([pmin,pmax])
	ax4bisx.set_ylabel('Pulse periods')
	ax4bisx.ticklabel_format(useOffset=False)
	ax4bisx.minorticks_on()
	
	# Plot of residuals versus day-of-year
	ax5   = fig.add_subplot(5,2,6)
	
	if bindoy > 0:
		ax5.errorbar(	0.5*(doy_bins_lo+doy_bins_hi), \
				binned_doy_res, \
				xerr       = 0.5*(doy_bins_hi-doy_bins_lo), \
				yerr       = binned_doy_unc, \
				color      = 'b', \
				ecolor     = 'b', \
				capsize    = 2., \
				linewidth  = 1., \
				linestyle  = 'dashed', \
				elinewidth = 1. )
		
		dr3   = (binned_doy_res+binned_doy_unc).max() - (binned_doy_res-binned_doy_unc).min()
		rmin3 = (binned_doy_res-binned_doy_unc).min() - 0.1 * dr3
		rmax3 = (binned_doy_res+binned_doy_unc).max() + 0.1 * dr3
		ax5.set_ylim([rmin3,rmax3])
	else:
		xdict = {}
		ydict = {}
		rdict = {}
		fdict = {}
		cols  = []
		
		for i in xrange(nobs):
			if urlprefix is not None and urlsuffix is not None:
				plotlink  = urlprefix
				plotlink += os.path.splitext(os.path.basename(data['datafile'][i]))[0]
				plotlink += urlsuffix
				if not os.path.exists(plotlink): plotlink = None
			else:	
				plotlink = None
		
			if xdict.has_key(colors[i]):
				xdict[colors[i]].append(doys[i])
				ydict[colors[i]].append(res[i])
				rdict[colors[i]].append(data['uncres'][i])
				fdict[colors[i]].append(plotlink)
			else:
				cols.append(colors[i])
				xdict[colors[i]] = [doys[i]]
				ydict[colors[i]] = [res[i]]
				rdict[colors[i]] = [data['uncres'][i]]
				fdict[colors[i]] = [plotlink]
		
		if not svg_enabled:
			for i, col in enumerate(cols):
				ax5.errorbar(	xdict[col], \
						ydict[col], \
						yerr       = rdict[col], \
						color      = col, \
						ecolor     = col, \
						capsize    = 2.,\
						linewidth  = 0.,\
						elinewidth = 1.,\
						marker     = 's',\
						mew        = 0.,\
						ms         = pointsize )
			
			if not discard_flagged and nflagged > 0:
				ax5.scatter(flagged_doys,flagged_res,marker='o',s=64.,c='r')
		else:
			if not discard_flagged and nflagged > 0:
				ax5.scatter(flagged_doys,flagged_res,marker='o',s=64.,c='r')
				
			for i, col in enumerate(cols):
				sc   = ax5.scatter(	xdict[col], \
							ydict[col], \
							color        = col, \
							marker       = 's', \
							linewidth    = 0., \
							s            = 2.*pointsize*pointsize )
				
				sc.set_urls(fdict[col])
				
				ax5.errorbar(	xdict[col], \
						ydict[col], \
						yerr       = rdict[col], \
						fmt        = None, \
						color      = col, \
						ecolor     = col, \
						capsize    = 2.,\
						linewidth  = 0.,\
						elinewidth = 1. )
		
		ax5.set_ylim([rmin,rmax])
	
	ax5.set_xlim([0.,366.])
	ax5.set_xlabel('Day of Year')
	ax5.set_ylabel(reslabel)
	ax5.minorticks_on()
	
	ax5bisx = ax5.twinx()
	ylim    = ax5.get_ylim()
	pmin    = f0 * ylim[0] * 1e-6
	pmax    = f0 * ylim[1] * 1e-6
	ax5bisx.set_ylim([pmin,pmax])
	ax5bisx.set_ylabel('Pulse periods')
	ax5bisx.ticklabel_format(useOffset=False)
	ax5bisx.minorticks_on()
	
	# Plot of residuals vs frequency
	ax6   = fig.add_subplot(5,2,7)
	xdict = {}
	ydict = {}
	rdict = {}
	fdict = {}
	cols  = []
	
	for i in xrange(nobs):
		if urlprefix is not None and urlsuffix is not None:
			plotlink  = urlprefix
			plotlink += os.path.splitext(os.path.basename(data['datafile'][i]))[0]
			plotlink += urlsuffix
			if not os.path.exists(plotlink): plotlink = None
		else:	
			plotlink = None
	
		if xdict.has_key(colors[i]):
			xdict[colors[i]].append(data['freq'][i])
			ydict[colors[i]].append(res[i])
			rdict[colors[i]].append(data['uncres'][i])
			fdict[colors[i]].append(plotlink)
		else:
			cols.append(colors[i])
			xdict[colors[i]] = [data['freq'][i]]
			ydict[colors[i]] = [res[i]]
			rdict[colors[i]] = [data['uncres'][i]]
			fdict[colors[i]] = [plotlink]
	
	if not svg_enabled:
		for i, col in enumerate(cols):
			ax6.errorbar(	xdict[col], \
					ydict[col], \
					yerr       = rdict[col], \
					color      = col, \
					ecolor     = col, \
					capsize    = 2.,\
					linewidth  = 0.,\
					elinewidth = 1.,\
					marker     = 's',\
					mew        = 0.,\
					ms         = pointsize )
		
		if not discard_flagged and nflagged > 0:
			ax6.scatter(flagged_freqs,flagged_res,marker='o',s=64.,c='r')
	else:
		if not discard_flagged and nflagged > 0:
			ax6.scatter(flagged_freqs,flagged_res,marker='o',s=64.,c='r')
			
		for i, col in enumerate(cols):
			sc   = ax6.scatter(	xdict[col], \
						ydict[col], \
						color        = col, \
						marker       = 's', \
						linewidth    = 0., \
						s            = 2.*pointsize*pointsize )
			
			sc.set_urls(fdict[col])
			
			ax6.errorbar(	xdict[col], \
					ydict[col], \
					yerr       = rdict[col], \
					fmt        = None, \
					color      = col, \
					ecolor     = col, \
					capsize    = 2.,\
					linewidth  = 0.,\
					elinewidth = 1. )
	
	ax6.set_xlabel('Frequency (MHz)')
	ax6.set_ylim([rmin,rmax])
	ax6.set_ylabel(reslabel)
	ax6.minorticks_on()
	
	ax6bisx = ax6.twinx()
	ylim    = ax6.get_ylim()
	pmin    = f0 * ylim[0] * 1e-6
	pmax    = f0 * ylim[1] * 1e-6
	ax6bisx.set_ylim([pmin,pmax])
	ax6bisx.set_ylabel('Pulse periods')
	ax6bisx.ticklabel_format(useOffset=False)
	ax6bisx.minorticks_on()
	
	# Plot of TOA uncertainties
	ax7   = fig.add_subplot(5,2,8)
	xdict = {}
	ydict = {}
	rdict = {}
	fdict = {}
	cols  = []
	
	for i in xrange(nobs):
		if urlprefix is not None and urlsuffix is not None:
			plotlink  = urlprefix
			plotlink += os.path.splitext(os.path.basename(data['datafile'][i]))[0]
			plotlink += urlsuffix
			if not os.path.exists(plotlink): plotlink = None
		else:	
			plotlink = None
	
		if xdict.has_key(colors[i]):
			xdict[colors[i]].append(data['uncres'][i])
			ydict[colors[i]].append(res[i])
			rdict[colors[i]].append(data['uncres'][i])
			fdict[colors[i]].append(plotlink)
		else:
			cols.append(colors[i])
			xdict[colors[i]] = [data['uncres'][i]]
			ydict[colors[i]] = [res[i]]
			rdict[colors[i]] = [data['uncres'][i]]
			fdict[colors[i]] = [plotlink]
	
	if not svg_enabled:
		for i, col in enumerate(cols):
			ax7.errorbar(	xdict[col], \
					ydict[col], \
					yerr       = rdict[col], \
					color      = col, \
					ecolor     = col, \
					capsize    = 2.,\
					linewidth  = 0.,\
					elinewidth = 1.,\
					marker     = 's',\
					mew        = 0.,\
					ms         = pointsize )
		
		if not discard_flagged and nflagged > 0:
			ax7.scatter(flagged_uncres,flagged_res,marker='o',s=64.,c='r')
	else:
		if not discard_flagged and nflagged > 0:
			ax7.scatter(flagged_uncres,flagged_res,marker='o',s=64.,c='r')
			
		for i, col in enumerate(cols):
			sc   = ax7.scatter(	xdict[col], \
						ydict[col], \
						color        = col, \
						marker       = 's', \
						linewidth    = 0., \
						s            = 2.*pointsize*pointsize )
			
			sc.set_urls(fdict[col])
			
			ax7.errorbar(	xdict[col], \
					ydict[col], \
					yerr       = rdict[col], \
					fmt        = None, \
					color      = col, \
					ecolor     = col, \
					capsize    = 2.,\
					linewidth  = 0.,\
					elinewidth = 1. )
	
	ax7.set_xlabel('TOA uncertainty ($\mu$s)')
	ax7.set_xscale('log')
	ax7.set_ylim([rmin,rmax])
	ax7.set_ylabel(reslabel)
	ax7.minorticks_on()
	
	ax7bisx = ax7.twinx()
	ylim    = ax7.get_ylim()
	pmin    = f0 * ylim[0] * 1e-6
	pmax    = f0 * ylim[1] * 1e-6
	ax7bisx.set_ylim([pmin,pmax])
	ax7bisx.set_ylabel('Pulse periods')
	ax7bisx.minorticks_on()
	
	# Periodogram plot
	ax8 = fig.add_subplot(5,2,9)
	ax8.plot(pgram_freqs,pgram)
	ax8.set_xlim([pgram_freqs.min(),pgram_freqs.max()])
	ax8.set_xlabel('Frequency (d$^{-1}$)')
	ax8.set_ylabel('Power')
	ax8.ticklabel_format(useOffset=False)
	ax8.set_xscale('log')
	ax8.minorticks_on()
	
	# Plots of Wrms and red-chisq as a function of the residual "distance"
	ax9  = fig.add_subplot(5,2,10)
	idxs = numpy.arange(1,len(wrms)+1)
	ax9.plot(idxs,wrms,'b')
	ax9.set_xlabel('TOA index (sorted by $|N_\\sigma|$)')
	ax9.set_ylabel('Weighted RMS ($\mu$s)')
	ax9.yaxis.label.set_color('b')
	ax9.minorticks_on()
	
	ax9bisx = ax9.twinx()
	idx     = redchisq >= 0.
	ax9bisx.plot(idxs[idx],redchisq[idx],'r')
	ax9bisx.set_ylim([0.,1.05*redchisq.max()])
	ax9bisx.set_ylabel('Reduced $\chi^2$')
	ax9bisx.yaxis.label.set_color('r')
	ax9bisx.minorticks_on()
	
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
	
	plot_residuals(	parfile         = args.parfile, \
			timfile         = args.timfile, \
			preres          = args.preres, \
			discard_flagged = args.discard_flagged, \
			wmin            = args.wmin, \
			output_weights  = args.output_weights, \
			output_flagged  = args.output_flagged, \
			output_stats    = args.output_stats, \
			output_tim      = args.output_tim, \
			pgrampts        = args.pgrampts, \
			binophase       = args.binophase, \
			bindoy          = args.bindoy, \
			graph           = args.graph, \
			width           = args.width, \
			height          = args.height, \
			pointsize       = args.pointsize, \
			urlprefix       = args.urlprefix, \
			urlsuffix       = args.urlsuffix, \
			overwrite       = args.overwrite, \
			dpi             = args.dpi )
	
	goodbye()
