from scipy.integrate import odeint
import numpy as np
import astropy.constants as const
import astropy.units as u
import matplotlib.pyplot as plt

#read the data file
Data = np.loadtxt('dmvals.dat')
MJD = Data[:,0]
DM = Data[:,1]
DM_err = Data[:,2]


Data2 = np.loadtxt('dmvals_trimtim.dat')
MJD2 = Data2[:,0]
DM2 = Data2[:,1]
DM2_err = Data2[:,2]
print np.shape(MJD2), np.shape(DM2), np.shape(DM2_err)

#Data3 = np.loadtxt('dmvals_caterina.dat')
#MJD3 = Data3[:,0]
#DM3 = Data3[:,1]
#DM3_err = Data3[:,2]


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
#plt.subplot(211)
#plt.xlabel('time[MJD]', fontdict=font)
#plt.xlim(58010,58125)
#plt.ylim(0.002 + 1.896e1,0.022 + 1.896e1)
#plt.ylabel('DM[pc\cm^3]', fontdict=font)
#plt.title('dmvals_auto', fontdict=font)
#plt.errorbar(MJD, DM, DM_err, marker='o', ms=7, lolims=lolims, uplims=uplims, ls=ls, color='magenta')



#uplims = np.zeros(MJD2.shape)
#lolims = np.zeros(MJD2.shape)

#plt.subplot(212)
plt.xlabel('time[MJD]', fontdict=font)
#xplt.xlim(56500,57100)
#plt.ylim(0.002 + 1.896e1,0.022 + 1.896e1)
plt.ylabel('DM[pc/cm^3]', fontdict=font)
#plt.title('dmvals_manual', fontdict=font)
plt.errorbar(MJD, DM, DM_err, marker='o', ms=7, ls=ls, color='magenta', label='without_trimtim')
plt.errorbar(MJD2, DM2, DM2_err, marker='o', ms=7,  ls=ls, color='red', label='with_trimtim')
#plt.errorbar(MJD2, DM2, DM2_err, marker='o', ms=7, lolims=lolims, uplims=uplims, ls=ls, color='blue', label='caterina')

#Tweak spacing to prevent clipping of ylabel
plt.legend()
plt.subplots_adjust(left=0.17, hspace = 0.5)
plt.savefig('dmvals_pipeline_vs_trimtim.png')
