import matplotlib.pyplot as plt
import numpy

#read the data file
Data = numpy.loadtxt('dmvals.dat')


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
plt.show()
plt.savefig('dm_variations_plot.png')




