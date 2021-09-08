import os
import sys
import imp
import inspect
import argparse

try:
	from misc_tools import *
	from setup_directory import setup_directory as setupdir
	from refold_data import refold_data as refold
	from scrunch_data import scrunch_data as scrunch
	from plotone import plotone
	from plotmulti import plotmulti
	from multiplot import multiplot
	from make_stats import make_stats
	from make_templates import make_templates
	from make_toas import make_toas
	from clean import clean
except ImportError:
	print 'Warning: could not import psrchive and related functions!'
	pass
	

# driver_script.py: driver script for running pipeline-type timing analyses
# Author:           Lucas Guillemot
# Last update:      3 Oct 2014
# Version:          3.01


# Some default declarations
GOOD_FUNCNAMES = [	'setup_directory', 'refold_data', 'scrunch_data', 'clean', \
			'plotone', 'plotmulti', 'multiplot', 'make_stats', 'make_templates', 'make_toas' ]

REQUIRED_PARAMS = [	'general_pulsar', 'general_workdir', 'general_backends', 'general_dataexts', \
                   	'general_tmin', 'general_tmax', 'general_parfile', 'general_partmin', 'general_partmax', \
			'general_dm_from_parfile', 'general_site', 'general_clk_corr_file', \
			'general_logfile', 'general_overwrite', \
			'general_scrunch_ext', 'general_scrunch_dedisp', 'general_scrunch_pscrunch', \
			'general_scrunch_bscrunch', 'general_scrunch_tscrunch', 'general_scrunch_fscrunch', \
			'general_multiplot_ext', 'general_multiplot_x', 'general_multiplot_y', \
			'general_multiplot_rebinx', 'general_multiplot_rebiny', 'general_multiplot_suffix', \
			'general_multiplot_titlesnr', 'general_multiplot_titlefreq', 'general_multiplot_titlemjd', \
			'general_multiplot_titletobs', 'general_multiplot_titlepsr', \
			'general_plotmulti_ext', 'general_plotmulti_x', 'general_plotmulti_y', \
			'general_plotmulti_rebinx', 'general_plotmulti_rebiny', 'general_plotmulti_prefix', \
			'general_plotmulti_grdev', 'general_plotmulti_titlesnr', 'general_plotmulti_titlefreq', \
			'general_plotmulti_titlemjd', 'general_plotmulti_titletobs', 'general_plotmulti_titlepsr', \
			'general_stats_ext', 'general_stats_full', \
			'general_templates_update', 'general_templates_backend', 'general_templates_ext', \
			'general_templates_nprof', 'general_templates_freq', 'general_templates_ftol', \
			'general_templates_bw', 'general_templates_btol', 'general_templates_obsnchan', \
			'general_templates_shiftmax', 'general_templates_prefix', \
			'general_toas_backend', 'general_toas_ext', 'general_toas_template', \
			'general_toas_toafile', 'general_toas_freq', 'general_toas_ftol', 'general_toas_bw', \
			'general_toas_btol', 'general_toas_obsnchan', 'general_toas_algorithm', 'general_toas_plotres' ]

def get_parser():
	parser = argparse.ArgumentParser(description='Driver script for running pipeline-type timing analyses.')
	parser.add_argument('-card',type=str,required=True,help='Path to a python script containing the parameters of the analyses to perform.')
	parser.add_argument('-norefold',action='store_true',default=False,help='Disables refolding of the data.')
	parser.add_argument('-noscrunch',action='store_true',default=False,help='Disables scrunching of the data.')
	parser.add_argument('-noclean',action='store_true',default=False,help='Disables cleaning of the refolded data.')
	parser.add_argument('-noplots',action='store_true',default=False,help='Disables plotting of the data.')
	parser.add_argument('-nostats',action='store_true',default=False,help='Disables calculation of statistics.')
	parser.add_argument('-notemplates',action='store_true',default=False,help='Disables updating of template profiles.')
	parser.add_argument('-notoas',action='store_true',default=False,help='Disables extraction of TOAs.')
	return parser


def read_card(card):
	if not os.path.exists(card):
		raise ExistError('Error: card file does not exist.')
		
	try:
		card_data = imp.load_source('',card)
	except:
		raise CardError('Problem importing the card file!')
	
	# Read the card data as provided by the user
	datadict  = card_data.__dict__
	newdict   = {}
	
	keylist  = GOOD_FUNCNAMES + ['general']
	
	for key, val in datadict.items():
		for elem in keylist:
			if elem in key: newdict[key] = val
	
	# Now make sure the parameters are valid
	for key, val in newdict.items():
		if 'general' in key: continue
		for funcname in GOOD_FUNCNAMES:
			if funcname in key: break
			
		if funcname == 'setup_directory':  argspec = inspect.getargspec(setupdir)
		elif funcname == 'refold_data':    argspec = inspect.getargspec(refold)
		elif funcname == 'scrunch_data':   argspec = inspect.getargspec(scrunch)
		elif funcname == 'clean':          argspec = inspect.getargspec(clean)
		elif funcname == 'plotone':        argspec = inspect.getargspec(plotone)
		elif funcname == 'plotmulti':      argspec = inspect.getargspec(plotmulti)
		elif funcname == 'multiplot':      argspec = inspect.getargspec(multiplot)
		elif funcname == 'make_stats':     argspec = inspect.getargspec(make_stats)
		elif funcname == 'make_templates': argspec = inspect.getargspec(make_templates)
		elif funcname == 'make_toas':      argspec = inspect.getargspec(make_toas)
		else: raise MiscError('Not implemented yet.')
		
		fargspec = inspect.formatargspec(argspec)
		argskeys = argspec[0]
		
		keyarg   = key.replace(funcname + '_','')
		if keyarg not in argskeys:
			print 'Error: invalid key \"%s\" for function \"%s\"!' % (keyarg,funcname)
			raise CardError('Invalid key name.')
	
	# Finally, read the "general" options and make sure they are all there (and then make some tests)
	for keyarg in REQUIRED_PARAMS:
		if not newdict.has_key(keyarg):
			print 'Error: key \"%s\" not found in card file \"%s\"!' % (keyarg,card)
			raise CardError('Required parameter missing.')
	
	for e in newdict['general_backends']:
		if not newdict['general_dataexts'].has_key(e):
			print 'Error: extension rule unknown for backend \"%s\". Check \"general_dataexts\" parameter.' % e
			raise CardError('Problem with the general_dataexts parameter.')
	
	if any(type(e) is list for e in [newdict['general_parfile'],newdict['general_partmin'],newdict['general_partmax']]):
		if not all(type(e) is list for e in [newdict['general_partmin'],newdict['general_partmax']]):
			print 'Error: parfile, partmin, and partmax parameters must either all be strings, or all be lists.'
			raise CardError('parfile, partmin, partmax parameters error.')
		
		if 	(len(newdict['general_parfile']) != len(newdict['general_partmin'])) \
			or (len(newdict['general_parfile']) != len(newdict['general_partmax'])):
			print 'Error: parfile, partmin, and partmax parameter lists must be of the same length.'
			raise CardError('parfile, partmin, partmax parameters error.')
	
	if type(newdict['general_site']) is dict:
		for e in newdict['general_backends']:
			if not newdict['general_site'].has_key(e):
				print 'Error: site rule unknown for backend \"%s\". Check \"general_site\" parameter.' % e
				raise CardError('Problem with the general_site parameter.')
	
	if type(newdict['general_clk_corr_file']) is dict:
		for e in newdict['general_backends']:
			if not newdict['general_clk_corr_file'].has_key(e):
				print 'Error: clock correction file rule unknown for backend \"%s\". Check \"general_clk_corr_file\" parameter.' % e
				raise CardError('Problem with the clock correction file parameter.')
	
	#
	
	scrunch_list = [newdict['general_scrunch_ext'],newdict['general_scrunch_dedisp'],newdict['general_scrunch_pscrunch'],newdict['general_scrunch_bscrunch'],newdict['general_scrunch_tscrunch'],newdict['general_scrunch_fscrunch']]
	if any(type(e) is list for e in scrunch_list):
		if not all(type(e) is list for e in scrunch_list):
			print 'Error: scrunching parameters must either all be non-lists, or all lists.'
			raise CardError('scrunching parameters error.')
			
		for i_ in range(len(scrunch_list)):
			for j_ in range(i_+1,len(scrunch_list)):
				if len(scrunch_list[i_]) != len(scrunch_list[j_]):
					print 'Error: scrunching parameter lists must be of the same length.'
					raise CardError('scrunching parameters error.')
	else:
		# In that case, make these parameters lists of 1 element.
		newdict['general_scrunch_ext']      = [newdict['general_scrunch_ext']]
		newdict['general_scrunch_dedisp']   = [newdict['general_scrunch_dedisp']]
		newdict['general_scrunch_pscrunch'] = [newdict['general_scrunch_pscrunch']]
		newdict['general_scrunch_bscrunch'] = [newdict['general_scrunch_bscrunch']]
		newdict['general_scrunch_tscrunch'] = [newdict['general_scrunch_tscrunch']]
		newdict['general_scrunch_fscrunch'] = [newdict['general_scrunch_fscrunch']]
	
	# At this stage we must have lists of scrunching parameters
	if not type(newdict['general_scrunch_ext']) is list:
		print 'Error: problem converting scrunching parameters into lists.'
		raise CardError('scrunch parameters error.')
	
	#
	
	plotmulti_list = [newdict['general_plotmulti_ext'],newdict['general_plotmulti_x'],newdict['general_plotmulti_y'],newdict['general_plotmulti_rebinx'],newdict['general_plotmulti_rebiny'],newdict['general_plotmulti_prefix'],newdict['general_plotmulti_grdev'],newdict['general_plotmulti_titlesnr'],newdict['general_plotmulti_titlefreq'],newdict['general_plotmulti_titlemjd'],newdict['general_plotmulti_titletobs'],newdict['general_plotmulti_titlepsr']]
	if any(type(e) is list for e in plotmulti_list):
		if not all(type(e) is list for e in plotmulti_list):
			print 'Error: plotmulti parameters must either all be non-lists, or all lists.'
			raise CardError('plotmulti parameters error.')
			
		for i_ in range(len(plotmulti_list)):
			for j_ in range(i_+1,len(plotmulti_list)):
				if len(plotmulti_list[i_]) != len(plotmulti_list[j_]):
					print 'Error: plotmulti parameter lists must be of the same length.'
					raise CardError('plotmulti parameters error.')
	else:
		# In that case, make these parameters lists of 1 element.
		newdict['general_plotmulti_ext']       = [newdict['general_plotmulti_ext']]
		newdict['general_plotmulti_x']         = [newdict['general_plotmulti_x']]
		newdict['general_plotmulti_y']         = [newdict['general_plotmulti_y']]
		newdict['general_plotmulti_rebinx']    = [newdict['general_plotmulti_rebinx']]
		newdict['general_plutmulti_rebiny']    = [newdict['general_plutmulti_rebiny']]
		newdict['general_plotmulti_prefix']    = [newdict['general_plotmulti_prefix']]
		newdict['general_plotmulti_grdev']     = [newdict['general_plotmulti_grdev']]
		newdict['general_plotmulti_titlesnr']  = [newdict['general_plotmulti_titlesnr']]
		newdict['general_plotmulti_titlefreq'] = [newdict['general_plotmulti_titlefreq']]
		newdict['general_plotmulti_titlemjd']  = [newdict['general_plotmulti_titlemjd']]
		newdict['general_plotmulti_titletobs'] = [newdict['general_plotmulti_titletobs']]
		newdict['general_plotmulti_titlepsr']  = [newdict['general_plotmulti_titlepsr']]
	
	# At this stage we must have lists of plotmulti parameters
	if not type(newdict['general_plotmulti_ext']) is list:
		print 'Error: problem converting plotmulti parameters into lists.'
		raise CardError('plotmulti parameters error.')
		
	#
	
	multiplot_list = [newdict['general_multiplot_ext'],newdict['general_multiplot_x'],newdict['general_multiplot_y'],newdict['general_multiplot_rebinx'],newdict['general_multiplot_rebiny'],newdict['general_multiplot_suffix'],newdict['general_multiplot_titlesnr'],newdict['general_multiplot_titlefreq'],newdict['general_multiplot_titlemjd'],newdict['general_multiplot_titletobs'],newdict['general_multiplot_titlepsr']]
	if any(type(e) is list for e in multiplot_list):
		if not all(type(e) is list for e in multiplot_list):
			print 'Error: multiplot parameters must either all be non-lists, or all lists.'
			raise CardError('multiplot parameters error.')
			
		for i_ in range(len(multiplot_list)):
			for j_ in range(i_+1,len(multiplot_list)):
				if len(multiplot_list[i_]) != len(multiplot_list[j_]):
					print 'Error: multiplot parameter lists must be of the same length.'
					raise CardError('multiplot parameters error.')
	else:
		# In that case, make these parameters lists of 1 element.
		newdict['general_multiplot_ext']       = [newdict['general_multiplot_ext']]
		newdict['general_multiplot_x']         = [newdict['general_multiplot_x']]
		newdict['general_multiplot_y']         = [newdict['general_multiplot_y']]
		newdict['general_multiplot_rebinx']    = [newdict['general_multiplot_rebinx']]
		newdict['general_plutmulti_rebiny']    = [newdict['general_plutmulti_rebiny']]
		newdict['general_multiplot_suffix']    = [newdict['general_multiplot_suffix']]
		newdict['general_multiplot_titlesnr']  = [newdict['general_multiplot_titlesnr']]
		newdict['general_multiplot_titlefreq'] = [newdict['general_multiplot_titlefreq']]
		newdict['general_multiplot_titlemjd']  = [newdict['general_multiplot_titlemjd']]
		newdict['general_multiplot_titletobs'] = [newdict['general_multiplot_titletobs']]
		newdict['general_multiplot_titlepsr']  = [newdict['general_multiplot_titlepsr']]
	
	# At this stage we must have lists of multiplot parameters
	if not type(newdict['general_multiplot_ext']) is list:
		print 'Error: problem converting multiplot parameters into lists.'
		raise CardError('multiplot parameters error.')
	
	#
	
	templates_list = [newdict['general_templates_backend'],newdict['general_templates_ext'],newdict['general_templates_nprof'],newdict['general_templates_freq'],newdict['general_templates_ftol'],newdict['general_templates_bw'],newdict['general_templates_btol'],newdict['general_templates_obsnchan'],newdict['general_templates_forcealign'],newdict['general_templates_shiftmax'],newdict['general_templates_prefix']]
	if any(type(e) is list for e in templates_list):
		if not all(type(e) is list for e in templates_list):
			print 'Error: template parameters must either all be non-lists, or all lists.'
			raise CardError('template parameters error.')
			
		for i_ in range(len(templates_list)):
			for j_ in range(i_+1,len(templates_list)):
				if len(templates_list[i_]) != len(templates_list[j_]):
					print 'Error: template parameter lists must be of the same length.'
					raise CardError('template parameters error.')
	else:
		# In that case, make these parameters lists of 1 element.
		newdict['general_templates_backend']    = [newdict['general_templates_backend']]
		newdict['general_templates_ext']        = [newdict['general_templates_ext']]
		newdict['general_templates_nprof']      = [newdict['general_templates_nprof']]
		newdict['general_templates_freq']       = [newdict['general_templates_freq']]
		newdict['general_templates_ftol']       = [newdict['general_templates_ftol']]
		newdict['general_templates_bw']         = [newdict['general_templates_bw']]
		newdict['general_templates_btol']       = [newdict['general_templates_btol']]
		newdict['general_templates_obsnchan']   = [newdict['general_templates_obsnchan']]
		newdict['general_templates_forcealign'] = [newdict['general_templates_forcealign']]
		newdict['general_templates_shiftmax']   = [newdict['general_templates_shiftmax']]
		newdict['general_templates_prefix']     = [newdict['general_templates_prefix']]
	
	# At this stage we must have lists of template parameters
	if not type(newdict['general_templates_ext']) is list:
		print 'Error: problem converting template parameters into lists.'
		raise CardError('template parameters error.')
	
	#
	
	toas_list = [newdict['general_toas_backend'],newdict['general_toas_ext'],newdict['general_toas_template'],newdict['general_toas_toafile'],newdict['general_toas_freq'],newdict['general_toas_ftol'],newdict['general_toas_bw'],newdict['general_toas_btol'],newdict['general_toas_obsnchan'],newdict['general_toas_algorithm'],newdict['general_toas_plotres']]
	if any(type(e) is list for e in toas_list):
		if not all(type(e) is list for e in toas_list):
			print 'Error: TOA parameters must either all be non-lists, or all lists.'
			raise CardError('TOA parameters error.')
			
		for i_ in range(len(toas_list)):
			for j_ in range(i_+1,len(toas_list)):
				if len(toas_list[i_]) != len(toas_list[j_]):
					print 'Error: TOA parameter lists must be of the same length.'
					raise CardError('TOA parameters error.')
	else:
		# In that case, make these parameters lists of 1 element.
		newdict['general_toas_backend']   = [newdict['general_toas_backend']]
		newdict['general_toas_ext']       = [newdict['general_toas_ext']]
		newdict['general_toas_template']  = [newdict['general_toas_template']]
		newdict['general_toas_toafile']   = [newdict['general_toas_toafile']]
		newdict['general_toas_freq']      = [newdict['general_toas_freq']]
		newdict['general_toas_ftol']      = [newdict['general_toas_ftol']]
		newdict['general_toas_bw']        = [newdict['general_toas_bw']]
		newdict['general_toas_btol']      = [newdict['general_toas_btol']]
		newdict['general_toas_obsnchan']  = [newdict['general_toas_obsnchan']]
		newdict['general_toas_algorithm'] = [newdict['general_toas_algorithm']]
		newdict['general_toas_plotres']   = [newdict['general_toas_plotres']]
	
	# At this stage we must have lists of TOA parameters
	if not type(newdict['general_toas_ext']) is list:
		print 'Error: problem converting TOA parameters into lists.'
		raise CardError('TOA parameters error.')
	
	return newdict


def make_analysis_card(	funcname,\
			other_pars=None ):
	if funcname not in GOOD_FUNCNAMES:
		raise CardError('Invalid function name.')
		
	if funcname == 'setup_directory':  argspec = inspect.getargspec(setupdir)
	elif funcname == 'refold_data':    argspec = inspect.getargspec(refold)
	elif funcname == 'scrunch_data':   argspec = inspect.getargspec(scrunch)
	elif funcname == 'clean':          argspec = inspect.getargspec(clean)
	elif funcname == 'plotone':        argspec = inspect.getargspec(plotone)
	elif funcname == 'plotmulti':      argspec = inspect.getargspec(plotmulti)
	elif funcname == 'multiplot':      argspec = inspect.getargspec(multiplot)
	elif funcname == 'make_stats':     argspec = inspect.getargspec(make_stats)
	elif funcname == 'make_templates': argspec = inspect.getargspec(make_templates)
	elif funcname == 'make_toas':      argspec = inspect.getargspec(make_toas)
	else: raise MiscError('Not implemented yet.')
	
	fargspec = inspect.formatargspec(argspec)	
	argskeys = argspec[0]
	
	if len(argskeys) == len(argspec[3]): argsvals = argspec[3]
	else:
		argsvals = []
		if type(argspec[1]) is list: 
			for elem in argspec[1]: argsvals.append(elem)
		else:   argsvals.append(argspec[1])
		
		for elem in argspec[3]: argsvals.append(elem)
	
	if len(argskeys) != len(argsvals):
		while len(argskeys) != len(argsvals): argsvals = [None] + argsvals
	
	argsdict = {}
	for key, val in zip(argskeys, argsvals): argsdict[key] = val
	
	# Now complete the default card with the user-provided arguments
	if other_pars is not None:
		for key, val in other_pars.items():
			for elem in [funcname,'general']:
				if elem in key: break
				
			keyarg = key.replace(elem + '_','')
			if argsdict.has_key(keyarg): argsdict[keyarg] = val
		
	return argsdict


def driver_script(	card, \
			norefold    = False, \
			noscrunch   = False, \
			noclean     = False, \
			noplots     = False, \
			nostats     = False, \
			notemplates = False, \
			notoas      = False ):
	
	# First read the card file
	card_dict = read_card(card)
	
	##############################################################################################
	# Step 1: setup the directory (if the directory already exists, this will update its contents)
	##############################################################################################
	
	analysis_card = make_analysis_card('setup_directory',card_dict)
	
	# Forced parameter(s)
	analysis_card['destdir'] = card_dict['general_workdir']
	
	print 'Running setup_directory with arguments %s...' % analysis_card
	
	try:
		setupdir(**analysis_card)
		print 
	except:
		raise
	
	# Now save some basic information (paths...) for future usage
	path2links     = os.path.join(analysis_card['destdir'],analysis_card['datadir'],analysis_card['linksdir'])
	path2refold    = os.path.join(analysis_card['destdir'],analysis_card['datadir'],analysis_card['refolddir'])
	path2scrunch   = os.path.join(analysis_card['destdir'],analysis_card['datadir'],analysis_card['scrunchdir'])
	path2plots     = os.path.join(analysis_card['destdir'],analysis_card['plotdir'])
	path2templates = os.path.join(analysis_card['destdir'],analysis_card['templatedir'])
	backends       = analysis_card['backends']
	dataexts       = analysis_card['dataexts']
	
	#######################################################
	# Step 2: refold the data with one or several par files
	#######################################################
	
	if not norefold:
		# Loop over the backends
		for backend in backends:
			analysis_card = make_analysis_card('refold_data',card_dict)
		
			# Forced parameter(s)
			analysis_card['datadir']    = os.path.join(path2links,backend)
			analysis_card['destdir']    = os.path.join(path2refold,backend)
			analysis_card['scrunchdir'] = os.path.join(path2scrunch,backend)
			analysis_card['dataext']    = dataexts[backend]
			if type(analysis_card['site']) is dict: analysis_card['site'] = analysis_card['site'][backend]
			
			if not os.path.isdir(analysis_card['datadir']):
				print 'Directory \"%s\" not found. Continuing...' % analysis_card['datadir']
			
			#
			
			print '[BACKEND %s] Running refold_data with arguments %s...' % (backend,analysis_card)
			
			try:
				refold(**analysis_card)
				print
			except:
				pass
	
	############################################
	# Step 3: scrunch the data in different ways
	############################################
	
	if not noscrunch:
		# Loop over the backends
		for backend in backends:
			# Loop over scrunching strategies
			for i in range(len(card_dict['general_scrunch_ext'])):
				analysis_card = make_analysis_card('scrunch_data',card_dict)
			
				# Forced parameter(s)
				analysis_card['datadir'] = os.path.join(path2refold,backend)
				analysis_card['destdir'] = os.path.join(path2scrunch,backend)
				if type(analysis_card['site']) is dict: analysis_card['site'] = analysis_card['site'][backend]
			
				analysis_card['destext'] = card_dict['general_scrunch_ext'][i]
				
				if card_dict['general_scrunch_dedisp'][i]:   analysis_card['dedisperse'] = True
				
				if card_dict['general_scrunch_pscrunch'][i]: analysis_card['pscrunch'] = True
				
				if card_dict['general_scrunch_bscrunch'][i]: analysis_card['bscrunch'] = True
				
				if card_dict['general_scrunch_tscrunch'][i] == 0:
					analysis_card['tscrunch'] = False
				elif card_dict['general_scrunch_tscrunch'][i] == 1:
					analysis_card['tscrunch'] = True
				elif card_dict['general_scrunch_tscrunch'][i] > 1:
					analysis_card['tscrunch']        = True
					analysis_card['tscrunch_factor'] = card_dict['general_scrunch_tscrunch'][i]
				elif card_dict['general_scrunch_tscrunch'][i] < 0:
					analysis_card['tscrunch']        = True
					analysis_card['tscrunch_nsub']   = -card_dict['general_scrunch_tscrunch'][i]
					
				if card_dict['general_scrunch_fscrunch'][i] == 0:
					analysis_card['fscrunch'] = False
				elif card_dict['general_scrunch_fscrunch'][i] == 1:
					analysis_card['fscrunch'] = True
				elif card_dict['general_scrunch_fscrunch'][i] > 1:
					analysis_card['fscrunch']        = True
					analysis_card['fscrunch_factor'] = card_dict['general_scrunch_fscrunch'][i]
				elif card_dict['general_scrunch_fscrunch'][i] < 0:
					analysis_card['fscrunch']        = True
					analysis_card['fscrunch_nchan']  = -card_dict['general_scrunch_fscrunch'][i]
					
				print '[BACKEND %s] Running scrunch_data with arguments %s...' % (backend,analysis_card)
				
				try:
					scrunch(**analysis_card)
					print
				except:
					pass
			
	##########################################################
	# Step 4: clean up the refolded data (to save disk space!)
	##########################################################
	
	if not noclean:
		# Loop over the backends
		for backend in backends:
			analysis_card = make_analysis_card('clean',card_dict)
			
			# Forced parameter(s)
			analysis_card['datadir'] = os.path.join(path2refold,backend)
			
			print '[BACKEND %s] Running clean with arguments %s...' % (backend,analysis_card)
			
			try:
				clean(**analysis_card)
				print
			except:
				pass
	
	####################
	# Step 5: make plots
	####################
	
	if not noplots:
		# Loop over the backends
		for backend in backends:
			# Loop over the multiplot strategies
			for i in range(len(card_dict['general_multiplot_ext'])):
				analysis_card = make_analysis_card('multiplot',card_dict)
				
				# Forced parameter(s)
				analysis_card['datadir'] = os.path.join(path2scrunch,backend)
				analysis_card['destdir'] = os.path.join(path2plots,backend)
				
				analysis_card['dataext'] = card_dict['general_multiplot_ext'][i]
				analysis_card['x']       = card_dict['general_multiplot_x'][i]
				analysis_card['y']       = card_dict['general_multiplot_y'][i]
				analysis_card['rebinx']  = card_dict['general_multiplot_rebinx'][i]
				analysis_card['rebiny']  = card_dict['general_multiplot_rebiny'][i]
				analysis_card['suffix']  = card_dict['general_multiplot_suffix'][i]
				
				if card_dict['general_multiplot_titlesnr'][i]:  analysis_card['titlesnr']  = True
				else:                                           analysis_card['titlesnr']  = False 
				
				if card_dict['general_multiplot_titlefreq'][i]: analysis_card['titlefreq'] = True
				else:                                           analysis_card['titlefreq'] = False 
				
				if card_dict['general_multiplot_titlemjd'][i]:  analysis_card['titlemjd']  = True
				else:                                           analysis_card['titlemjd']  = False 
				
				if card_dict['general_multiplot_titletobs'][i]: analysis_card['titletobs'] = True
				else:                                           analysis_card['titletobs'] = False 
				
				if card_dict['general_multiplot_titlepsr'][i]:  analysis_card['titlepsr']  = True
				else:                                           analysis_card['titlepsr']  = False 
				
				print '[BACKEND %s] Running multiplot with arguments %s...' % (backend,analysis_card)
				
				try:
					multiplot(**analysis_card)
					print
				except:
					pass
				
	if not noplots:
		# Loop over the backends
		for backend in backends:
			# Loop over the plotmulti strategies
			for i in range(len(card_dict['general_plotmulti_ext'])):
				analysis_card = make_analysis_card('plotmulti',card_dict)
				
				# Forced parameter(s)
				analysis_card['datadir'] = os.path.join(path2scrunch,backend)
				
				analysis_card['dataext'] = card_dict['general_plotmulti_ext'][i]
				analysis_card['x']       = card_dict['general_plotmulti_x'][i]
				analysis_card['y']       = card_dict['general_plotmulti_y'][i]
				analysis_card['rebinx']  = card_dict['general_plotmulti_rebinx'][i]
				analysis_card['rebiny']  = card_dict['general_plotmulti_rebiny'][i]
				if card_dict['general_plotmulti_grdev'][i].startswith('.'): card_dict['general_plotmulti_grdev'][i] = card_dict['general_plotmulti_grdev'][i][1:]
				analysis_card['graph']   = os.path.join(path2plots,backend,card_dict['general_plotmulti_prefix'][i] + '_%s.' % backend + card_dict['general_plotmulti_grdev'][i])
				
				if card_dict['general_plotmulti_titlesnr'][i]:  analysis_card['titlesnr']  = True
				else:                                           analysis_card['titlesnr']  = False 
				
				if card_dict['general_plotmulti_titlefreq'][i]: analysis_card['titlefreq'] = True
				else:                                           analysis_card['titlefreq'] = False 
				
				if card_dict['general_plotmulti_titlemjd'][i]:  analysis_card['titlemjd']  = True
				else:                                           analysis_card['titlemjd']  = False 
				
				if card_dict['general_plotmulti_titletobs'][i]: analysis_card['titletobs'] = True
				else:                                           analysis_card['titletobs'] = False 
				
				if card_dict['general_plotmulti_titlepsr'][i]:  analysis_card['titlepsr']  = True
				else:                                           analysis_card['titlepsr']  = False 
				
				print '[BACKEND %s] Running plotmulti with arguments %s...' % (backend,analysis_card)
				
				try:
					plotmulti(**analysis_card)
					print
				except:
					pass
	
	########################
	# Step 6: get some stats
	########################
	
	if not nostats:
		# Loop over the backends
		for backend in backends:
			analysis_card = make_analysis_card('make_stats',card_dict)
			
			# Forced parameter(s)
			analysis_card['datadir']  = os.path.join(path2scrunch,backend)
			analysis_card['output']   = os.path.join(card_dict['general_workdir'],card_dict['general_pulsar'] + '_%s_stats.dat' % backend)
			analysis_card['obscomb']  = os.path.join(path2plots,backend,'obscomb_%s.png'  % backend)
			analysis_card['freqplot'] = os.path.join(path2plots,backend,'freqplot_%s.png' % backend)
			analysis_card['snrplot']  = os.path.join(path2plots,backend,'snrsplot_%s.png' % backend)
			analysis_card['obschar']  = os.path.join(path2plots,backend,'obschar_%s.png'  % backend)
			analysis_card['zapplot']  = os.path.join(path2plots,backend,'zapplot_%s.png'  % backend)
			
			analysis_card['dataext'] = card_dict['general_stats_ext']
			if card_dict['general_stats_full']:
				analysis_card['origdatadir'] = os.path.join(path2links,backend)
				analysis_card['origdataext'] = dataexts[backend]
				
			print '[BACKEND %s] Running make_stats with arguments %s...' % (backend,analysis_card)
			
			try:
				make_stats(**analysis_card)
				print
			except:
				pass
				
	#################################
	# Step 7: make reference profiles
	#################################
	
	if not notemplates and card_dict['general_templates_update'] is True:
		# Loop over the template strategies
		for i in range(len(card_dict['general_templates_ext'])):
			analysis_card = make_analysis_card('make_templates',card_dict)
			backend       = card_dict['general_templates_backend'][i]
			
			# Forced parameter(s)
			analysis_card['datadir']         = os.path.join(path2scrunch,backend)
			analysis_card['sortsnr']         = True
			analysis_card['maxline']         = True
			if type(analysis_card['clk_corr_file']) is dict: analysis_card['clk_corr_file'] = analysis_card['clk_corr_file'][backend]
			
			analysis_card['backend']         = backend
			analysis_card['dataext']         = card_dict['general_templates_ext'][i]
			analysis_card['nprof']           = card_dict['general_templates_nprof'][i]
			analysis_card['freq']            = card_dict['general_templates_freq'][i]
			analysis_card['ftol']            = card_dict['general_templates_ftol'][i]
			analysis_card['bw']              = card_dict['general_templates_bw'][i]
			analysis_card['btol']            = card_dict['general_templates_btol'][i]
			analysis_card['obsnchan']        = card_dict['general_templates_obsnchan'][i]
			analysis_card['forcealign']      = card_dict['general_templates_forcealign'][i]
			analysis_card['shiftmax']        = card_dict['general_templates_shiftmax'][i]
			analysis_card['addedprof']       = os.path.join(path2templates,card_dict['general_templates_prefix'][i] + '_summed.prof')
			analysis_card['smoothedprof']    = os.path.join(path2templates,card_dict['general_templates_prefix'][i] + '_smoothed.prof')
			analysis_card['output_added']    = os.path.join(path2templates,card_dict['general_templates_prefix'][i] + '_summed.txt')
			analysis_card['output_smoothed'] = os.path.join(path2templates,card_dict['general_templates_prefix'][i] + '_smoothed.txt')
			analysis_card['plot1']           = os.path.join(path2plots,backend,card_dict['general_templates_prefix'][i] + '_template.png')
			analysis_card['plot2']           = os.path.join(path2plots,backend,card_dict['general_templates_prefix'][i] + '_snrplot.png')
			analysis_card['plot3']           = os.path.join(path2plots,backend,card_dict['general_templates_prefix'][i] + '_snrplot2.png')
			
			print '[BACKEND %s] Running make_templates with arguments %s...' % (backend,analysis_card)
			
			try:
				make_templates(**analysis_card)
				print
			except:
				pass
	
	###############################
	# Step 8: make times of arrival
	###############################
	
	if not notoas:
		# Loop over the toa generation strategies
		for i in range(len(card_dict['general_toas_ext'])):
			analysis_card = make_analysis_card('make_toas',card_dict)
			backend       = card_dict['general_toas_backend'][i]
			
			# Forced parameter(s)
			analysis_card['datadir']        = os.path.join(path2scrunch,backend)
			analysis_card['showinstrument'] = True
			analysis_card['showreceiver']   = True
			analysis_card['showtemplate']   = False
			analysis_card['showlength']     = True
			analysis_card['showbw']         = True
			analysis_card['plotdir']        = os.path.join(path2plots,backend)
			
			analysis_card['backend']        = backend
			analysis_card['template']       = os.path.join(path2templates,card_dict['general_toas_template'][i])
			analysis_card['dataext']        = card_dict['general_toas_ext'][i]
			analysis_card['toafile']        = os.path.join(card_dict['general_workdir'],card_dict['general_toas_toafile'][i])
			analysis_card['freq']           = card_dict['general_toas_freq'][i]
			analysis_card['ftol']           = card_dict['general_toas_ftol'][i]
			analysis_card['bw']             = card_dict['general_toas_bw'][i]
			analysis_card['btol']           = card_dict['general_toas_btol'][i]
			analysis_card['obsnchan']       = card_dict['general_toas_obsnchan'][i]
			analysis_card['algorithm']      = card_dict['general_toas_algorithm'][i]
			analysis_card['plotres']        = card_dict['general_toas_plotres'][i]
			
			print '[BACKEND %s] Running make_toas with arguments %s...' % (backend,analysis_card)
			
			try:
				make_toas(**analysis_card)
				print
			except:
				pass
			
	
	return

#

if __name__ == '__main__':
	parser = get_parser()
	args   = parser.parse_args()
	write_history()

	driver_script(	args.card, \
			norefold    = args.norefold, \
			noscrunch   = args.noscrunch, \
			noclean     = args.noclean, \
			noplots     = args.noplots, \
			nostats     = args.nostats, \
			notemplates = args.notemplates, \
			notoas      = args.notoas )
	
	goodbye()
