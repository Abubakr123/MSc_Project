from scipy.integrate import odeint
from numpy import *
import astropy.constants as const
import astropy.units as u
import matplotlib.pyplot as plt
import numpy
import sys

psr_name = sys.argv[1]
print psr_name
#read the data file
Data = numpy.loadtxt('dmvals.dat')
#Data = np.loadtxt('dmvals_trimtim.dat')
MJD = Data[:,0]
DM = Data[:,1]
DM_err = Data[:,2]


font = {'family': 'serif',
        'color':  'blue',
        'weight': 'normal',
        'size': 14,
        }

xerr = 0.5
ls = 'dotted'

uplims = numpy.zeros(MJD.shape)
lolims = numpy.zeros(MJD.shape)

axes = plt.gca()
p = numpy.polyfit(MJD, DM, deg=1)
x = MJD
y = p[1] + p[0] * MJD

print "the intercept and the slope of the fit line: ", p

plt.figure()
plt.xlabel('time[MJD]', fontdict=font)
plt.ylabel('DM[pc/cm^3]', fontdict=font)
plt.title(" fitting DM for %s" % psr_name, fontdict=font)
plt.errorbar(MJD, DM, DM_err, label= DM values, marker='o', ms=7, xerr=xerr,
             lolims=lolims, uplims=uplims, ls=ls, color='magenta')
plt.plot(x, y, '--', label="The fitted line")
plt.subplots_adjust(left=0.15 , hspace = 0.5)
plt.legend()
plt.savefig('fitting_dm.png')

