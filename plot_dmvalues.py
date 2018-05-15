from scipy.integrate import odeint
from numpy import *
import astropy.constants as const
import astropy.units as u
import matplotlib.pyplot as plt
import numpy
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


plt.figure()
plt.xlabel('time[MJD]', fontdict=font)
plt.ylabel('DM[pc/cm^3]', fontdict=font)
plt.title('DM values', fontdict=font)
plt.errorbar(MJD, DM, DM_err, marker='o', ms=7, xerr=xerr,
             lolims=lolims, uplims=uplims, ls=ls, color='magenta')
plt.subplots_adjust(left=0.15 , hspace = 0.5)
plt.savefig('dm_variations_plot.png')



#====================================================================================
'''
Data = sp.loadtxt('dmvals-2015-09-07.dat')
MJD2 = Data[:,0]
DM2 = Data[:,1]
DM2_err = Data[:,2]


uplims = np.zeros(MJD2.shape)
lolims = np.zeros(MJD2.shape)

plt.subplot(212)
plt.xlabel('time[MJD]', fontdict=font)
plt.ylabel('DM[pc\cm^3]', fontdict=font)
plt.title('DM values J0613+3731 2015-09-07', fontdict=font)
plt.errorbar(MJD2, DM2, DM2_err+0.001, label="DM-val", marker='o', ms=7, xerr=xerr,
             lolims=lolims, uplims=uplims, ls=ls, color='red')

# Tweak spacing to prevent clipping of ylabel
plt.subplots_adjust(left=0.1, hspace = 0.5)
plt.legend()
plt.savefig('DM values J0613+3731_comp.png')



plt.subplot(211)
plt.plot(range(12))
plt.subplot(212, fac

left  = 0.125  # the left side of the subplots of the figure
right = 0.9    # the right side of the subplots of the figure
bottom = 0.1   # the bottom of the subplots of the figure
top = 0.9      # the top of the subplots of the figure
wspace = 0.2   # the amount of width reserved for blank space between subplots,
               # expressed as a fraction of the average axis width
hspace = 0.2   # the amount of height reserved for white space between subplots,
               # expressed as a fraction of the average axis heigh

plt.errorbar(MJD, DM, DM_err,
linestyle='dashed', color='cyan', linewidth=1.0, 
marker='o', markeredgecolor='red', markeredgewidth=2,
markerfacecolor='white', markersize=10,
ecolor='black', elinewidth=2.0, capsize=10) 
'''
