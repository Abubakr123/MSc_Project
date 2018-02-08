import os, sys
import numpy as np
import argparse

TOA = sys.argv[1]
phase = sys.argv[2]
TOAs = open(TOA, "r")
TOAsadd = open(TOA[:-4]+"_padd.tim", "w")
b=TOAs.readlines()
for l in b:
	if l.split()[0] != 'FORMAT' and l.split()[0] != '#':
		TOAsadd.write(l[:-2]+" -padd "+str(phase)+"\n")
	else:
		TOAsadd.write(l)

