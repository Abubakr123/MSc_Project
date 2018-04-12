import os
import sys
from misc_tools import *
import difflib

# pulsars.py:  a class for managing the list of observed pulsars
# Author:      Lucas Guillemot
# Last update: 4 Dec 2014
# Version:     1.12



# Some default declarations
DEF_KNOWN             = '/backup/lguillem/pulsar_list/known_pulsars.txt'
DEF_EMPTY_FIELD_CHARS = ['*','x']



class pulsars:
	def __init__(self,psrlist=DEF_KNOWN,empty_field_chars=DEF_EMPTY_FIELD_CHARS):
		if not os.path.exists(psrlist):
			raise ExistError('Error: pulsar list does not exist!')
		
		self.parse_psrlist(psrlist,empty_field_chars)
		return
		
	def parse_psrlist(self,psrlist,empty_field_chars=DEF_EMPTY_FIELD_CHARS):
		self.psrdict = {}
		
		fich = open(psrlist,'r')
		cont = fich.readlines()
		fich.close()
		
		for line in cont:
			if line[0] == '#': continue
			if len(line) < 5:  continue
			data  = line.split()
			nname = data[0]
			
			if len(data) > 1: 
				jname = data[1]
				if jname in empty_field_chars: jname = None
			else:   jname = None
			
			if len(data) > 2: 
				bname = data[2]
				if bname in empty_field_chars: bname = None
			else:   bname = None
			
			if len(data) > 3: other = data[3:]
			else:             other = None
			
			if self.psrdict.has_key(nname):
				raise PulsarError('Error: same nname multiple times in the pulsar list.')
			
			self.psrdict[nname] = {'nname': nname, 'jname': jname, 'bname': bname, 'other': other}
		
		return
	
	def make_tests(self):
		out = 1
		if len(self.psrdict) == 0:
			print 'Empty pulsar list.'
			out = 0
			return out
		
		nnames = []
		jnames = []
		bnames = []
		onames = []
		multn  = []
		multj  = []
		multb  = []
		multo  = []
		
		for key, elem in self.psrdict.items():
			nname, jname, bname, oname = elem['nname'], elem['jname'], elem['bname'], elem['other']
			if nname is not None:
				if nname not in nnames: nnames.append(nname)
				else: multn.append(nname)
			
			if jname is not None:
				if jname not in jnames: jnames.append(jname)
				else: multj.append(jname)
			
			if bname is not None:
				if bname not in bnames: bnames.append(bname)
				else: multb.append(bname)
				
			if oname is not None:
				for name in oname:
					if name not in onames: onames.append(name)
					else: multo.append(oname)
			
		if len(multn) > 0:
			print 'Multiple identical nname entries: %s' % multn
			out = 0
		if len(multj) > 0:
			print 'Multiple identical jname entries: %s' % multj
			out = 0
		if len(multb) > 0:
			print 'Multiple identical bname entries: %s' % multb
			out = 0
		if len(multo) > 0:
			print 'Multiple identical oname entries: %s' % multo
			out = 0
		
		return out
			
	def get_pulsar_dict(self,name,which='nname'):
		if which not in ['nname','jname','bname','other']:
			raise PulsarError('Error: invalid request for get_pulsar.')
			
		empty_dict = {'nname': None, 'jname': None, 'bname': None, 'other': None}
		
		if which == 'nname':
			if self.psrdict.has_key(name): outdict = self.psrdict[name]
			else:
				print 'Unknown pulsar nname: %s.' % name
				return empty_dict
		elif which == 'jname':
			found = 0
			for key, elem in self.psrdict.items():
				if elem['jname'] == None: continue
				if elem['jname'] == name:
					found  += 1
					outdict = elem
			if found == 0:
				print 'Unknown pulsar jname: %s.' % name
				return empty_dict
			elif found > 1: print 'Warning: pulsar jname %s found multiple times in the list!' % name
		elif which == 'bname': 
			found = 0
			for key, elem in self.psrdict.items():
				if elem['bname'] == None: continue
				if elem['bname'] == name:
					found  += 1
					outdict = elem
			if found == 0:
				print 'Unknown pulsar bname: %s.' % name
				return empty_dict
			elif found > 1: print 'Warning: pulsar bname %s found multiple times in the list!' % name
		elif which == 'other':
			found = 0
			for key, elem in self.psrdict.items():
				if elem['other'] == None: continue
				if name in elem['other']:
					found  += 1
					outdict = elem
			if found == 0:
				print 'Unknown alternative name: %s' % name
				return empty_dict
			elif found > 1: print 'Warning pulsar alternative name %s found multiple in the list!' % name
		
		return outdict
		
	def get_pulsar(self,name,which='nname'):
		outdict = self.get_pulsar_dict(name,which)
		return [outdict['nname'], outdict['jname'], outdict['bname'], outdict['other']]
		
	def get_pulsar_by_nname(self,name):
		return self.get_pulsar(name,which='nname')
		
	def get_pulsar_by_jname(self,name):
		return self.get_pulsar(name,which='jname')
		
	def get_pulsar_by_bname(self,name):
		return self.get_pulsar(name,which='bname')
		
	def get_pulsar_by_othername(self,name):
		return self.get_pulsar(name,which='other')
		
	def get_nnames(self):
		nnames = self.psrdict.keys()
		nnames.sort()
		return nnames
		
	def get_jnames(self):
		jnames = []
		for key, elem in self.psrdict.items():
			if elem['jname'] is None: continue
			else: jnames.append(elem['jname'])
		jnames.sort()
		return jnames
		
	def get_bnames(self):
		bnames = []
		for key, elem in self.psrdict.items():
			if elem['bname'] is None: continue
			else: bnames.append(elem['bname'])
		bnames.sort()
		return bnames
		
	def get_othernames(self):
		othernames = []
		for key, elem in self.psrdict.items():
			if elem['other'] is None: continue
			else:
				for othername in elem['other']: othernames.append(othername)
		othernames.sort()
		return othernames
		
	def find_pulsar(self,pulsar,verbose=True):
		nnames     = self.get_nnames()
		othernames = self.get_othernames()
		jnames     = self.get_jnames()
	
		if pulsar in nnames:       return pulsar
		elif pulsar in othernames: return self.get_pulsar_by_othername(pulsar)[0]
		elif pulsar in jnames:     return self.get_pulsar_by_jname(pulsar)[0]
		elif not verbose:          return ""
		else:
			print 'Unknown pulsar: \"%s\".' % pulsar
			print 'Did you mean:', difflib.get_close_matches(pulsar, nnames+othernames+jnames), '?'
			raise

#

if __name__ == '__main__':
	psrs = pulsars()
	print psrs.make_tests()
	
	psr  = psrs.get_pulsar('0030+04')
	print psr
	
	psr  = psrs.get_pulsar('0030+04',which='jname')
	print psr
	
	psr  = psrs.get_pulsar('J0030+0451',which='jname')
	print psr
	
	psr  = psrs.get_pulsar('B1937+21',which='bname')
	print psr
	
