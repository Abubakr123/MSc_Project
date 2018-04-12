import os
import sys
import numpy
import psrchive as p
import commands
import datetime
import time
import pytz
import logging
import scipy.stats.mstats as m
from math import factorial as fact

# Default declarations
NON_TEMPO_KEYS = [	'S400','S1400','W10','W50','itoa_code']

COMP_KEYS      = [	'RAJ','DECJ','PMRA','PMDEC','F0','F1','PEPOCH','DM','DM1',
			'PB','A1','T0','TASC','E','ECC','EPHEM','CLK' ]

EPOCH_KEYS     = [	'EPOCH', 'PEPOCH', 'POSEPOCH', 'DMEPOCH', 'TZRMJD', 'T0', 'TASC' ]

FREQ_COLORS    = {	1:	[0., 1200.,    'r', 'f < 1.2 GHz'], \
			2:      [1200., 1500., 'b', '1.2 < f < 1.5 GHz'], \
			3:      [1500., 1800., 'g', '1.5 < f < 1.8 GHz'], \
			4:      [1800., 2200., 'c', '1.8 < f < 2.2 GHz'], \
			5:      [2200., 2800., 'm', '2.2 < f < 2.8 GHz'], \
			6:      [2800., 9999., 'k', 'f > 2.8 GHz'] }

CALEN_REF      = datetime.datetime(1995, 10, 10)
CALEN_MJD_REF  = 50000.
DAY2SEC        = 86400.

# Misc functions
def write_history(history_file='commands.hist'):
	argv = sys.argv
	hist = open(history_file,'a+')
	hist.write("python")
	for elem in argv: hist.write(" " + elem)
	hist.write("\n")
	hist.close()
	return

def goodbye():
	if os.path.exists('ErRoR.LoG'): os.unlink('ErRoR.LoG')
	if os.path.exists('pred.tim'): os.unlink('pred.tim')

	print 'Finished! Goodbye...'
	sys.exit()

def progress_bar(progress,barLength=10):
	status = ""
	if isinstance(progress, int): progress = float(progress)
	if not isinstance(progress, float): 
		progress = 0
		status   = "error: progress var must be float\r\n"
	if progress < 0:
		progress = 0
		status   = "Halt...\r\n"
	if progress >= 1:
		progress = 1
		status   = "Done...\r\n"
	block = int(round(barLength*progress))
	text = "\rPercentage done: [%s] %.1f%%" % ("#"*block + "-"*(barLength-block), progress*100.)
	sys.stdout.write(text)
	sys.stdout.flush()
	return

def initialize_logging(name=__file__,logfile='log.txt'):
	logger = logging.getLogger(name)
	
	if not logger.handlers:
		logger.setLevel(logging.DEBUG)
		
		# create a file handler
		handler = logging.FileHandler(logfile)
		handler.setLevel(logging.DEBUG)
	
		# create a logging format
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(formatter)
	
		# add the handlers to the logger
		logger.addHandler(handler)
	
	return logger

def terminate_logging():
	logging.shutdown()
	return

def get_clk_corr_range(clk_corr_file):
	data = numpy.genfromtxt(clk_corr_file,unpack=True)
	return data[0].min(), data[0].max()
	
def get_freq_color(freq):
	f    = float(freq)
	keys = FREQ_COLORS.keys()
	keys.sort()
	for key in keys:
		val = FREQ_COLORS[key]
		if f >= val[0] and f < val[1]: break
	return val[2], val[3]

class ParFiles:
	def __init__(self):
		self.parfiles = []
		self.tmins    = []
		self.tmaxs    = []
		return
		
	def add_parfile(self,parfile,tmin=0.,tmax=99999.):
		# First test that the parfile exists
		if not os.path.exists(parfile):
			print 'Error: par file does not exist! Exiting...'
			raise ExistError('Par file does not exist! Exiting...')
			
		try:
			tmin = float(tmin)
		except:
			print 'Error: failed to convert tmin into a float.'
			raise MiscError('Failed to convert tmin into a float.')
			
		try:
			tmax = float(tmax)
		except:
			print 'Error: failed to convert tmax into a float.'
			raise MiscError('Failed to convert tmax into a float.')
		
		if tmin >= tmax:
			print 'Error: tmin greater than or equal to tmax!'
			raise MiscError('tmin greater than or equal to tmax!')
		
		self.parfiles.append(parfile)
		self.tmins.append(tmin)
		self.tmaxs.append(tmax)
		return
		
	def get_parfile_for_epoch(self,epoch):
		# Test that parfiles have been loaded
		if len(self.parfiles) == 0:
			print 'Error: no par files loaded!'
			return None
		
		try:
			epoch = float(epoch)
		except:
			print 'Failed to convert epoch into a float.'
			raise MiscError('Failed to convert epoch into a float.')
			
		# Now search for the best par file to return
		outpar = []
		for par, tmin, tmax in zip(self.parfiles, self.tmins, self.tmaxs):
			if epoch >= tmin and epoch < tmax: outpar.append(par)
		
		if len(outpar) == 0:
			print 'Error: no par file found for epoch %.1f!' % epoch
			raise MiscError('Could not find a par file for this epoch.')
		elif len(outpar) > 1: 
			print 'Warning: found multiple par files for epoch %.1f! Will return the first one provided.' % epoch
		
		return outpar[0]


# Exceptions
class Error(Exception):
	"""Base class for exceptions in this module."""
	pass

class ExistError(Error):
	def __init__(self, msg):
		self.msg  = msg
	def __str__(self):
		return self.msg

class AlreadyExistError(Error):
	def __init__(self, msg):
		self.msg  = msg
	def __str__(self):
		return self.msg

class NoFilesError(Error):
	def __init__(self, msg):
		self.msg  = msg
	def __str__(self):
		return self.msg

class PulsarError(Error):
	def __init__(self, msg):
		self.msg  = msg
	def __str__(self):
		return self.msg

class CardError(Error):
	def __init__(self, msg):
		self.msg  = msg
	def __str__(self):
		return self.msg

class MiscError(Error):
	def __init__(self, msg):
		self.msg  = msg
	def __str__(self):
		return self.msg

class PsrchiveError(Error):
	def __init__(self, msg, cmd):
		self.msg = msg
		self.cmd = cmd
	def __str__(self):
		return self.msg, self.cmd



# psrchive-related functions
def load_archive(archive):
	"""
	arch = p.Archive_load(archive)
	return arch
	"""

	### THIS VERSION SEEMS TO SEGFAULT!
	"""
	# Flush and save old file descriptors
	sys.stderr.flush()
	old_stderr_fd = os.dup(sys.stderr.fileno())
	old_stderr    = sys.stderr
	
	errf          = 'ErRoR.LoG'
	err_log       = file(errf,'a+',0)
	os.dup2(err_log.fileno(),sys.stderr.fileno())

	arch = p.Archive_load(archive)
	
	# Now restore original stderr
	sys.stderr    = old_stderr
	os.dup2(old_stderr_fd,sys.stderr.fileno())
	#os.unlink(errf)
	
	return arch
	"""
	
	#"""
	### WHILE THIS ONE DOES NOT (UNTIL NOW!)
	# Flush and save old file descriptors
	errf          = 'ErRoR.LoG'
	err_log       = file(errf,'a+',0)
	os.dup2(err_log.fileno(),sys.stderr.fileno())
	arch = p.Archive_load(archive)
	#os.unlink(errf)
	
	return arch
	#"""
	

def get_source(archive):
	arch = load_archive(archive)
	return get_source_open(arch)

def get_source_open(arch):
	return arch.get_source()

def get_snr(archive):
	arch = load_archive(archive)
	return get_snr_open(arch)

def get_snr_open(arch):
	# Careful: this one scrunches nsubint, nchan and npol information!
	if arch.get_nsubint() != 1: arch.tscrunch()
	if arch.get_nchan() != 1:   arch.fscrunch()
	if arch.get_npol() != 1:    arch.pscrunch()
	
	prof = arch.get_Profile(0,0,0)
	return prof.snr()

def get_nbin(archive):
	arch = load_archive(archive)
	return get_nbin_open(arch)
	
def get_nbin_open(arch):
	return arch.get_nbin()

def get_npol(archive):
	arch = load_archive(archive)
	return get_npol_open(arch)
	
def get_npol_open(arch):
	return arch.get_npol()
	
def get_nsubint(archive):
	arch = load_archive(archive)
	return get_nsubint_open(arch)
	
def get_nsubint_open(arch):
	return arch.get_nsubint()
	
def get_nchan(archive):
	arch = load_archive(archive)
	return get_nchan_open(arch)
	
def get_nchan_open(arch):
	return arch.get_nchan()
	
def get_ns(archive):
	arch = load_archive(archive)
	return get_ns_open(arch)

def get_ns_open(arch):
	nbin = get_nbin_open(arch)
	npol = get_npol_open(arch)
	nsub = get_nsubint_open(arch)
	nch  = get_nchan_open(arch)
	return nbin, npol, nsub, nch

def get_epoch(archive):
	arch = load_archive(archive)
	return get_epoch_open(arch)

def get_epoch_open(arch):
	epoch = arch.get_Integration(0).get_start_time()
	if isinstance(epoch,p.MJD): return epoch.in_days()
	else: return epoch

def get_length(archive):
	arch = load_archive(archive)
	return get_length_open(arch)

def get_length_open(arch):
	return arch.integration_length()

def get_first_profile(archive):
	arch = load_archive(archive)
	return get_first_profile_open(arch)
	
def get_first_profile_open(arch):
	prof = arch.get_Profile(0,0,0)
	return prof.get_amps()

def get_first_subint_duration(archive):
	arch = load_archive(archive)
	return get_first_subint_duration_open(arch)

def get_first_subint_duration_open(arch):
	return arch.get_first_Integration().get_duration()

def get_subint_lengths(archive):
	arch = load_archive(archive)
	return get_subint_lengths_open(arch)
	
def get_subint_lengths_open(arch):
	return [arch.get_Integration(i).get_duration() for i in xrange(arch.get_nsubint())]

def get_equ_coords(archive,sexa=False):
	arch = load_archive(archive)
	return get_equ_coords_open(arch,sexa)
	
def get_equ_coords_open(arch,sexa=False):
	coord = arch.get_coordinates()
	radec = coord.getRaDec()
	if sexa: out = radec.getHMSDMS()
	else:    out = radec.getDegrees()
	out = out.lstrip('(').rstrip(')').replace(' ','').split(',')
	for i_ in range(len(out)): out[i_] = float(out[i_])
	return out
	
	
def get_gal_coords(archive,sexa=False):
	arch = load_archive(archive)
	return get_gal_coords_open(arch,sexa)
	
def get_gal_coords_open(arch,sexa=False):
	coord = arch.get_coordinates()
	gal   = coord.getGalactic()
	if sexa: out = gal.getHMSDMS()
	else:    out = gal.getDegrees()
	out = out.lstrip('(').rstrip(')').replace(' ','').split(',')
	for i_ in range(len(out)): out[i_] = float(out[i_])
	return out

def get_frequency(archive):
	arch = load_archive(archive)
	return get_frequency_open(arch)
	
def get_frequency_open(arch):
	return arch.get_centre_frequency()

def get_bandwidth(archive):
	arch = load_archive(archive)
	return get_bandwidth_open(arch)

def get_bandwidth_open(arch):
	return arch.get_bandwidth()

def get_frequency_info(archive):
	arch = load_archive(archive)
	return get_frequency_info_open(arch)

def get_frequency_info_open(arch):
	freq = get_frequency_open(arch)
	bw   = get_bandwidth_open(arch)
	return freq, bw

def get_site(archive):
	arch = load_archive(archive)
	return get_site_open(arch)

def get_site_open(arch):
	return arch.get_telescope()

def get_backend(archive):
	cmd  = 'vap -c backend -n %s' % archive
	out  = commands.getoutput(cmd)
	return out.split()[-1]

def get_scale(archive):
	arch = load_archive(archive)
	return get_scale_open(arch)

def get_scale_open(arch):
	return arch.get_scale()

def get_dm(archive):
	arch = load_archive(archive)
	return get_dm_open(arch)

def get_dm_open(arch):
	return arch.get_dispersion_measure()

def get_sum_weights(archive):
	arch = load_archive(archive)
	return get_sum_weights_open(arch)
	
def get_sum_weights_open(arch):
	return arch.get_weights().sum()

def get_nsubx_nchanx(archive):
	arch = load_archive(archive)
	return get_nsubx_nchanx_open(arch)
	
def get_nsubx_nchanx_open(arch):
	# Stuff below is adapted from PulsePortraiture
	nsub         = get_nsubint_open(arch)
	nchan        = get_nchan_open(arch)
	weights      = arch.get_weights()
	weights_norm = numpy.where(weights == 0.0, numpy.zeros(weights.shape),numpy.ones(weights.shape))
	ok_isubs     = numpy.compress(weights_norm.mean(axis=1), xrange(nsub))
	ok_ichans    = [numpy.compress(weights_norm[isub], xrange(nchan)) for isub in xrange(nsub)]
	nsubx        = len(ok_isubs)
	nchanx       = numpy.array(map(len, ok_ichans)).mean()
	return nsubx, nchanx

def get_zapped_subints(archive):
	arch = load_archive(archive)
	return get_zapped_subints_open(arch)

def get_zapped_subints_open(arch):
	nsub         = get_nsubint_open(arch)
	weights      = arch.get_weights()
	weights_norm = numpy.where(weights == 0.0, numpy.zeros(weights.shape),numpy.ones(weights.shape))
	zapped_isubs = numpy.compress(weights_norm.mean(axis=1) == 0.0, xrange(nsub))
	return zapped_isubs
	
def get_zapped_chans(archive):
	arch = load_archive(archive)
	return get_zapped_chans_open(arch)
	
def get_zapped_chans_open(arch):
	nsub          = get_nsubint_open(arch)
	nchan         = get_nchan_open(arch)
	weights       = arch.get_weights()
	weights_norm  = numpy.where(weights == 0.0, numpy.zeros(weights.shape),numpy.ones(weights.shape))
	zapped_ichans = [numpy.compress(weights_norm[isub] == 0.0, xrange(nchan)) for isub in xrange(nsub)]
	return zapped_ichans
	
def get_2D_mask(zapped_ichans,epoch,length,freq,bw,nsub,nchan):
	# Take the output of the above function to form a 2D array suitable for imshow
	mask = numpy.zeros((nsub,nchan))
	
	for idx in xrange(nsub):
		row = zapped_ichans[idx]
		if len(row) == 0: continue
		mask[idx,row] = 1
	
	mask   = numpy.transpose(mask)
	extent = [epoch,epoch+length/86400.,freq-0.5*bw,freq+0.5*bw]
	return mask, extent

def get_obsnchan(archive):
	cmd  = 'psrstat -Q -c ext:obsnchan %s' % archive
	out  = commands.getoutput(cmd)
	return float(out.split()[-1])

def get_sum_bins(archive):
	cmd  = 'psrstat -Q -c all:sum %s' % archive
	out  = commands.getoutput(cmd)
	return float(out.split()[-1])

def get_dedispersed(archive):
	arch = load_archive(archive)
	return arch.get_dedispersed()

def get_max_shift(archive):
	arch   = load_archive(archive)
	data   = arch.get_data()
	prof   = data[0][0][0]
	binmax = numpy.argmax(prof)
	return -float(binmax) / float(len(prof))

def rotate_profile(archive,shift):
	sh      = -float(shift)
	cmd     = 'pam %s -r %f -e TmP' % (archive,sh)
	
	try:
		out = commands.getoutput(cmd)
	except:
		print 'Something went wrong while running \"%s\"...' % cmd
		raise PsrchiveError('Error while rotating profile!', cmd)
	
	fileext = os.path.splitext(archive)[1]
	tmpfile = archive.replace(fileext,'.TmP')
	
	try:
		os.rename(tmpfile,archive)
	except:
		print 'Something went wrong with file \"%s\"!' % archive
		if os.path.exists(tmpfile): os.unlink(tmpfile)
	
	return
	
def rotate_max(archive):
	shift = get_max_shift(archive)
	rotate_profile(archive,shift)
	return

def output_profile(archive,outfile,flags='FTp'):
	cmd = 'pdv -%s -t -K %s > %s' % (flags,archive,outfile)
	
	try:
		out = commands.getoutput(cmd)
	except:
		print 'Something went wrong while running \"%s\"...' % cmd
		raise PsrchiveError('Error while extracting the profile!', cmd)
	
	return

def fold_file(infile,outfile,DM=None,parfile=None,site=None):
	cmd  = 'pam -e TmP'
	if parfile is not None: cmd += ' -E %s' % parfile
	if DM is not None:      cmd += ' -d %s' % DM
	if site is not None:    cmd += ' --site %s' % site
	cmd += ' %s' % infile
	
	out = commands.getoutput(cmd)
	for outl in out.split('\n'):
		if 'error' in outl.lower():
			print 'Something went wrong while running \"%s\"...' % cmd
			raise PsrchiveError('Error while folding the profile!', cmd)
	
	fileext = os.path.splitext(infile)[1]
	tmpfile = infile.replace(fileext,'.TmP')
	
	try:
		os.rename(tmpfile,outfile)
	except:
		print 'Something went wrong with file \"%s\"!' % infile
		if os.path.exists(tmpfile): os.unlink(tmpfile)
	
	return

def scrunch_file(infile,outfile,flags=None):
	cmd  = 'pam -e TmP'
	if flags is not None: cmd += flags
	cmd += ' %s' % infile
	
	out = commands.getoutput(cmd)
	for outl in out.split('\n'):
		if 'error' in outl.lower():
			print 'Something went wrong while running command \"%s\"...' % cmd
			raise PsrchiveError('Error while scrunching the file!', cmd)

	fileext = os.path.splitext(infile)[1]
	tmpfile = infile.replace(fileext,'.TmP')
	
	try:
		os.rename(tmpfile,outfile)
	except:
		print 'Something went wrong with file \"%s\"!' % infile
		if os.path.exists(tmpfile): os.unlink(tmpfile)
	
	return

def add_files(infiles,outfile,flags=None):
	tmpfile = 'TmP.TmP'
	cmd     = 'psradd -o %s' % tmpfile
	if flags is not None:  cmd += flags
	for infile in infiles: cmd += ' %s' % infile
	
	out  = commands.getoutput(cmd)
	for outl in out.split('\n'):
		if 'error' in outl.lower():
			print 'Something went wrong while running command \"%s\"...' % cmd
			raise PsrchiveError('Error while adding the files!', cmd)
			
	try:
		os.rename(tmpfile,outfile)
	except:
		print 'Something went wrong with file \"%s\"!' % infile
		if os.path.exists(tmpfile): os.unlink(tmpfile)
		
	return

def smooth_file(infile,outfile,flags=None):
	cmd  = 'psrsmooth -e TmP'
	if flags is not None: cmd += flags
	cmd += ' %s' % infile
	
	out  = commands.getoutput(cmd)
	for outl in out.split('\n'):
		if 'error' in outl.lower():
			print 'Something went wrong while running command \"%s\"...' % cmd
			raise PsrchiveError('Error while smoothing the file!', cmd)
			
	tmpfile = infile + '.TmP'
	
	try:
		os.rename(tmpfile,outfile)
	except:
		print 'Something went wrong with file \"%s\"!' % infile
		if os.path.exists(tmpfile): os.unlink(tmpfile)
	
	return


# par file related functions
def extract_parfile(archive):
	cmd   = 'vap -E %s' % archive
	
	try:
		out   = commands.getoutput(cmd)
		out   = out.split('\n')
	except:
		print 'Something went wrong while running command \"%s\"...' % cmd
		raise PsrchiveError('Error while extracting par file!', cmd)
	
	par   = {}
	for line in out:
		if len(line) < 5:  continue
		if line[0] == '#': continue
		dat = line.split()
		if len(dat) < 2:   continue
		key, val = dat[0], dat[1]
		par[key] = val
	return par

def fix_parfile(par):
	if type(par) == str: pardict = extract_parfile(par)
	else: pardict = par
	
	# Eliminate non-tempo2 keys
	new_dict = {}
	change   = False
	for key, val in pardict.items():
		if key in NON_TEMPO_KEYS:
			if key != 'itoa_code': change = True
			continue
		else:
			new_dict[key] = val
	
	# detect pure tempo1 parameters ephemerides
	if 	not new_dict.has_key('EPHVER') and \
		((new_dict.has_key('P1') and 'D-' in new_dict['P1']) or \
		(new_dict.has_key('F1') and 'D-' in new_dict['F1']) or \
		(new_dict.has_key('P1') and (not any(e in new_dict['P1'] for e in ['D','E','d','e']))) or \
		(new_dict.has_key('F1') and (not any(e in new_dict['F1'] for e in ['D','E','d','e']))) or \
		new_dict.has_key('E')):
			new_dict['UNITS']               = 'TDB'
			new_dict['TIMEEPH']             = 'FB90'
			new_dict['DILATEFREQ']          = 'N'
			new_dict['PLANET_SHAPIRO']      = 'N'
			new_dict['T2CMETHOD']           = 'TEMPO'
			new_dict['CORRECT_TROPOSPHERE'] = 'N'
			change = True
	
	# use F0, F1, F2 instead of P0, P1, P2 (F2 should be enough)
	if new_dict.has_key('P0'):
		P0 = new_dict['P0'].replace('D','E')
		P0 = float(P0)
		F0 = 1. / P0
		new_dict['F0'] = F0
		new_dict.pop('P0', None)
		change = True
		
	if new_dict.has_key('P1'):
		P1 = new_dict['P1'].replace('D','E')
		P1 = float(P1)
		if not any(e in new_dict['P1'] for e in ['D','E','d','e']): P1 *= 1.e-15
		F0 = float(new_dict['F0'])
		F1 = - P1 * F0 * F0
		new_dict['F1'] = F1
		new_dict.pop('P1', None)
		change = True
		
	if new_dict.has_key('P2'):
		P2 = new_dict['P2'].replace('D','E')
		P2 = float(new_dict['P2'])
		if not any(e in new_dict['P1'] for e in ['D','E','d','e']): P2 *= 1.e-30
		F0 = float(new_dict['F0'])
		F1 = float(new_dict['F1'])
		F2 = 2. * F1**2. / F0 - P2 * F0**2.
		new_dict['F2'] = F2
		new_dict.pop('P2', None)
		change = True
	
	# Fix aberrant epoch values
	for key, val in new_dict.items():
		if key in EPOCH_KEYS:
			val = float(val)
			if val < 10000. or val > 80000.: val = 56000.
			new_dict[key] = val
	
	return new_dict, change

def write_parfile(pardict, outpar):
	outf = open(outpar,'w+')
	for key, val in pardict.items(): outf.write('%s %s\n' % (key, val))
	outf.close()

def read_parfile(parfile):
	fich = open(parfile)
	cont = fich.readlines()
	fich.close()

	par  = {}
	for line in cont:
		if len(line) < 5:  continue
		if line[0] == '#': continue
		dat = line.split()
		if len(dat) < 2:   continue
		key, val = dat[0], dat[1]
		par[key] = val
	return par

def get_dm_from_parfile(parfile,epoch=None):
	pardict = read_parfile(parfile)
	dm      = float(pardict['DM'])
	if epoch is not None:
		if pardict.has_key('DMEPOCH'): dt = (float(epoch) - float(pardict['DMEPOCH'])) / 365.25
		else:                          dt = (float(epoch) - float(pardict['PEPOCH']))  / 365.25

		for i_ in range(10):
			if pardict.has_key('DM%d' % i_): dm += numpy.power(dt, i_) * float(pardict['DM%d' % i_])
	return dm

def same_ephemeris(archive,parfile):
	pardict1 = extract_parfile(archive)
	
	if type(parfile) == str: pardict2 = read_parfile(parfile)
	else:                    pardict2 = parfile
	
	diff     = 0
	for key in COMP_KEYS:
		if not pardict1.has_key(key) or not pardict2.has_key(key): continue

		val1 = pardict1[key]
		val2 = pardict2[key]

		if (not val1 == val2) or (not val1 in val2) or (not val2 in val1):
			diff += 1
	
	if diff > 0: return False
	else: return True

def same_dm(archive,DM,tol=1.e-5):
	dm1 = get_dm(archive)
	if numpy.abs(float(dm1)-float(DM)) < tol: return True
	else: return False

def get_freq_from_parfile(parfile,epoch=None):
	pardict = read_parfile(parfile)
	f       = float(pardict['F0'])
	pepoch  = float(pardict['PEPOCH'])
	if epoch is not None:
		dt = (float(epoch) - pepoch) * 86400.
		
		for i_ in range(1,10):
			if pardict.has_key('F%d' % i_): f += numpy.power(dt, i_) * float(pardict['F%d' % i_]) / float(fact(i_))
	
	return f
	
def get_number_free_parameters(parfile):
	fich = open(parfile)
	cont = fich.readlines()
	fich.close()

	nf   = 0
	for line in cont:
		if len(line) < 5:  continue
		if line[0] == '#': continue
		dat = line.split()
		if len(dat) < 3:   continue
		if dat[2] == '1':  nf += 1

	return nf
	
# Data related functions
def clean2D(data, zmax = 3.):
	stds  = []
	idxs  = []
	shape = data.shape
	
	for i in range(shape[0]):
		mini = data[i].min()
		maxi = data[i].max()
		if mini == 0. and maxi == 0.: continue
		std  = data[i].std()
		stds.append(std)
		idxs.append(i)
		
	stds    = numpy.array(stds)
	zscores = m.zscore(stds)
		
	for i in range(len(stds)):
		idx = idxs[i]
		z   = zscores[i]
		if z > zmax:
			for j in range(shape[1]): data[idx][j] = 0.
	
	return data

def norm1D(data, zero_value = 0.5):
	if data.min() == data.max():
		for i in range(len(data)): data[i] = zero_value
	else:
		data -= data.min()
		data /= data.max()
		
	return data

def norm2D(data, zero_value = 0.5):
	shape = data.shape
	
	for i in range(shape[0]):
		if data[i].min() == 0. and data[i].max() == 0.:
			for j in range(shape[1]): data[i][j] = zero_value
		else:
			mini = data[i].min()
			data[i] -= mini
			maxi = data[i].max()
			if maxi == 0.:
				for j in range(shape[1]): data[i][j] = zero_value
			else:
				data[i] /= maxi
		
	return data

def diff_profiles(prof1, prof2):
	nbins    = len(prof2)
	scale    = (float(nbins) * (prof1*prof2).sum() - prof2.sum() * prof1.sum())
	scale   /= (float(nbins) * (prof1*prof1).sum() - prof1.sum() * prof1.sum())
	offset   = (scale * prof1.sum() - prof2.sum()) / float(nbins)

	prof3    = prof1.copy()
	prof3   -= offset
	prof3   *= scale
	diff     = prof2 - prof3
	return diff

def read_TOA_data(timfile,keep_commented=False):
	fich    = open(timfile,'r')
	cont    = fich.readlines()
	fich.close()
	
	TOAdata = []
	for line in cont:
		if len(line) < 5: continue
		data = line.split()
		if data[0].upper() in ['C','#'] and not keep_commented: continue
		
		if data[0].upper() == 'INCLUDE':
			TOAdata2 = read_TOA_data(data[1],keep_commented=keep_commented)
			if len(TOAdata2) == 0: 
				continue
			elif len(TOAdata2) == 1: 
				TOAdata.append(TOAdata2[0])
			else:
				for elem in TOAdata2: TOAdata.append(elem)
		else:
			if len(data) < 4: continue
			TOAdata.append(line)
			
	return TOAdata
	
def get_number_toas(timfile):
	TOAdata = read_TOA_data(timfile,keep_commented=False)
	ntoas   = len(TOAdata)
	return ntoas

def periodogram(time,flux,err,frequencies):
	t_     = numpy.array(time)
	fl_    = numpy.array(flux)
	err_   = numpy.array(err)
	fr_    = numpy.array(frequencies)
	
	# Stuff below is adapted from pyPeriod's gls.py
	tmin_  = t_.min()
	th     = t_ - tmin_
	omegas = 2.*numpy.pi*fr_
	err2   = err_*err_
	w_     = (1. / numpy.sum(1./err2)) / err2
	Y_     = numpy.sum(w_*fl_)
	yh     = fl_ - Y_
	YY_    = numpy.sum(w_*(yh**2.))
	
	upow_  = numpy.zeros(len(omegas))
	a_     = numpy.zeros(len(omegas))
	b_     = numpy.zeros(len(omegas))
	off_   = numpy.zeros(len(omegas))
	
	for i_, omega in enumerate(omegas):
		x_        = omega*th
		cosx      = numpy.cos(x_)
		sinx      = numpy.sin(x_)
		wcosx     = w_*cosx
		wsinx     = w_*sinx
		
		C         = numpy.sum(wcosx)         # Eq. (8)
		S         = numpy.sum(wsinx)         # Eq. (9)
		
		YC        = numpy.sum(yh*wcosx)      # Eq. (11)
		YS        = numpy.sum(yh*wsinx)      # Eq. (12)
		CCh       = numpy.sum(wcosx*cosx)    # Eq. (13)
		CSh       = numpy.sum(wcosx*sinx)    # Eq. (15)
		SSh       = 1.-CCh
		CC        = CCh-C*C	             # Eq. (13)
		SS        = SSh-S*S	             # Eq. (14)
		CS        = CSh-C*S	             # Eq. (15)
		D         = CC*SS-CS*CS              # Eq. (6)
		
		a_[i_]    = (YC*SS-YS*CS) / D
		b_[i_]    = (YS*CC-YC*CS) / D
		off_[i_]  = -a_[i_]*C - b_[i_]*S
		upow_[i_] = (SS*YC*YC + CC*YS*YS - 2.*CS*YC*YS) / (YY_*D)
		
	N_     = float(len(fl_))
	
	# Horne Baliunas normalization
	pow_   = (N_-1.)/2.*upow_
	return pow_
      

def get_subint_range(nsubint, zapped_subints):
	nzapped = len(zapped_subints)
	
	if nzapped == 0:
		return [0, nsubint-1]
	elif nzapped == nsubint:
		return -1
	else:
		imin = 0
		imax = nsubint-1
		for i in range(nzapped):
			if zapped_subints[i] != i:
				imin = i
				break
		
		for i in range(nzapped-1,-1,-1):
			if zapped_subints[i] == imax:
				imax -= 1
			else:
				break
		
		return [imin, imax]
	
	

# Clock accidents functions
def load_clock_accidents(accfile):
	fich = open(accfile,'r')
	cont = fich.readlines()
	fich.close()

	intervals = []

	for line in cont:
		if len(line) < 5:  continue
		if line[0] == '#': continue
		data = line.split()
		if len(data) < 2:  continue

		tmin = float(data[0])
		tmax = float(data[1])
		intervals.append([tmin,tmax])

	return intervals

def in_clock_accident(epoch, accidents):
	for interval in accidents:
		tmin = interval[0]
		tmax = interval[1]
		if epoch >= tmin and epoch < tmax: return True
	
	return False

# Time-related functions
def calendar_to_mjd(date):
	if type(date) is datetime.datetime:
		delta = date - CALEN_REF
	else:
		date_  = datetime.datetime.fromtimestamp(time.mktime(time.strptime(date, "%Y-%m-%d %H:%M:%S")))
		delta  = date_ - CALEN_REF

	mjd    = CALEN_MJD_REF
	mjd   += delta.days
	mjd   += delta.seconds / DAY2SEC
	mjd   += delta.microseconds / (1.e6 * DAY2SEC)
	return mjd

def mjd_to_calendar(mjd):
	diff   = mjd - CALEN_MJD_REF
	delta  = datetime.timedelta(days=diff)
	return CALEN_REF + delta

def mjd_to_calendar_str(mjd):
	diff   = mjd - CALEN_MJD_REF
	delta  = datetime.timedelta(days=diff)
	calen  = CALEN_REF + delta
	return calen.strftime("%d %b %Y")
	
def calendar_to_year(calen):
	newyear_day = datetime.datetime(calen.year, 1, 1, 0, 0, 0)
	diffdate = calen - newyear_day
	
	year = float(calen.year)
	year += (diffdate.days + (diffdate.seconds + diffdate.microseconds / 1000000.) / 86400.) / 365.
	
	return year

def mjd_to_year(mjd):
	return calendar_to_year(mjd_to_calendar(mjd))

def mjd_to_doy(mjd):
	calen = mjd_to_calendar(mjd)
	return calen.timetuple().tm_yday

def lmst_func(mjd,olong=-2.2):
	# adapted from tempo2's lmst in get_obsCoord.C
	a = 24110.54841
	b = 8640184.812866
	c = 0.093104
	d = -6.2e-6
	fmjdu1, nmjdu1 = numpy.modf(mjd)
	seconds_per_jc = 86400.0*36525.0

	tu0   = ((nmjdu1-51545)+0.5)/3.6525e4
	dtu   = fmjdu1/3.6525e4
	tu    = tu0+dtu
	gmst0 = (a + tu0*(b+tu0*(c+tu0*d)))/86400.0
	gst  = gmst0 + dtu*(seconds_per_jc + b + c*(tu+tu0) + d*(tu*tu+tu*tu0+tu0*tu0))/86400
	xlst = gst - olong/360.0
	return xlst

def get_lmst(mjd,olong=-2.2):
	# same as above, but return xlst%24
	xlst = lmst_func(mjd,olong)
	xlst = numpy.remainder(xlst,1.)
	return xlst

def get_local_time(utcmjd):
	diff   = utcmjd - CALEN_MJD_REF
	delta  = datetime.timedelta(days=diff)
	calen  = datetime.datetime(1995, 10, 10, 0, 0, 0, tzinfo=pytz.utc) + delta
	zone   = pytz.timezone('Europe/Paris')
	return calen.astimezone(zone)

def get_month_mjds(year,month):
        date   = datetime.datetime(year,month,1)
        mjd1   = calendar_to_mjd(date)

	year2  = year
	month2 = month+1
	
	if month2 == 13:
		month2 = 1
		year2 += 1
		
	date2  = datetime.datetime(year2,month2,1)
	mjd2   = calendar_to_mjd(date2) - 1.
	return mjd1, mjd2

def get_month_year(mjd):
	calen = mjd_to_calendar(mjd)
	return calen.year, calen.month

def get_mjd_now():
	calen = datetime.datetime.now()
	return calendar_to_mjd(calen)
