from scipy.integrate import odeint
import numpy as np
import astropy.constants as const
import astropy.units as u
import matplotlib.pyplot as plt

#read the data file
Data = np.loadtxt('dmvals_with_new_parfile.dat')
MJD = Data[:,0]
DM = Data[:,1]
DM_err = Data[:,2]

a=np.shape(Data)
print("2018", a)

Data2 = np.loadtxt('dmvals_with_final_parfile.dat')
MJD2 = Data2[:,0]
DM2 = Data2[:,1]
DM2_err = Data2[:,2]

a=np.shape(Data2)
print("2015", a)

font = {'family': 'serif',
        'color':  'blue',
        'weight': 'normal',
        'size': 14,
        }

xerr = 0.5
ls = 'dotted'

uplims = np.zeros(MJD.shape)
lolims = np.zeros(MJD.shape)


plt.figure()
plt.subplot(211)
plt.xlabel('time[MJD]', fontdict=font)
#plt.xlim(56852,57083)
#plt.ylim(0.002 + 1.896e1,0.022 + 1.896e1)
plt.ylabel('DM[pc/cm^3]', fontdict=font)
plt.title('dmvals_with_new_parfile', fontdict=font)
plt.errorbar(MJD, DM, DM_err, marker='o', ms=7, lolims=lolims, uplims=uplims, ls=ls, color='magenta')



uplims = np.zeros(MJD2.shape)
lolims = np.zeros(MJD2.shape)

plt.subplot(212)
plt.xlabel('time[MJD]', fontdict=font)
#plt.xlim(56852,57083)
#plt.ylim(0.002 + 1.896e1,0.022 + 1.896e1)
plt.ylabel('DM[pc/cm^3]', fontdict=font)
plt.title('dmvals_with_final_parfile', fontdict=font)
plt.errorbar(MJD2, DM2, DM2_err, marker='o', ms=7, lolims=lolims, uplims=uplims, ls=ls, color='red')

# Tweak spacing to prevent clipping of ylabel
plt.subplots_adjust(left=0.15, hspace = 0.5)
plt.savefig('DM_values_comparison.png')
