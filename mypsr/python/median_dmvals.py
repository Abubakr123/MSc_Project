import os, sys
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("echo")
args = parser.parse_args()
TOA = args.echo


TOAs = open(TOA, "r")
k=0
b=TOAs.readlines()
err=np.zeros((len(b)))

for l in b:
	if l.split()[0] != 'C' and l.split()[0] != 'FORMAT' and l.split()[0] != '#':
		#print l.split()[3]
		#print k
		err[k]=l.split()[2]
		k=k+1
err=err[0:k-1]
z=np.median(err)
w=np.mean(err)
print "err_median=",z,"\nerr_moyenne=", w


#DEF_TOA_FILE       = 'TOAs.tim'
#def get_parser():
#	parser = argparse.ArgumentParser(description='A script for producing times of arrival from Nancay pulsar timing data.')
#	parser.add_argument('-toafile',type=str,default=DEF_TOA_FILE,help='Name of output TOA file (default: \"%s\").' % DEF_TOA_FILE)
#	return parser
#toafile=DEF_TOA_FILE
#print toafile
