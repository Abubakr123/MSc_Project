#!/usr/bin/env python

import psrchive
import subprocess
import numpy as np
import sys

obs = sys.argv[1]
print obs

archive = psrchive.Archive_load(obs)
print archive

cmd = ['psredit',  obs[0]]
ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
output = ps.communicate()[0]
print output
