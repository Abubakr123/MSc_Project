import os
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
		err[k]=l.split()[3]
		k=k+1
err=err[0:k-1]
z=np.median(err)
w=np.mean(err)
print "err_median=",z,"\nerr_moyenne=", w
