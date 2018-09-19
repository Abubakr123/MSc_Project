#!/usr/bin/env python

import numpy as np
import os, argparse, math, sys
import matplotlib.pyplot as plt
from sklearn import preprocessing
import numpy.lib.recfunctions as rfn

parser = argparse.ArgumentParser(description="Compute SF")
parser.add_argument('-f', '--dmfile', type=str, nargs=1,
                    help="File containing DM variations")
parser.add_argument('--eb_cut', type=float, nargs='?', default=0.1,
                    help="error bar threshold in the DM plot")
#parser.add_argument('--a_cut', type=float, nargs='?',
#                    help="Window on the Solar angle")
parser.add_argument('-binsize', '--binsize', type=float, nargs=1,
                    help="Length of the bin in the SF")

args = parser.parse_args()

dmfile = args.dmfile[0]
if (args.eb_cut):
    cut = args.eb_cut
#if (args.a_cut):
#    cut = args.a_cut
if (args.binsize):
    binsize = args.binsize[0]

data = np.genfromtxt(dmfile,names='MJD, DM, edm, seq')
#data = data[data['angle']>cut]
data = data[data['edm']<cut]
#print data

tobs = data['MJD'][-1]-data['MJD'][0]



#meandt = np.ediff1d(data['MJD']).mean(axis=0)

nrep = 1000

for h in range(0,nrep):
    
#    print h

    newDM = []
    for z in range(len(data)):
        newDM.append(np.random.normal(data['DM'][z], data['edm'][z], 1))
#    print newDM    

    sfv, tcv, va = [], [], []
        
    for i in range(len(data)):
        for j in range(i+1,len(data)):
            #sfv.append(np.power(data['DM'][i]-data['DM'][j],2))
            sfv.append(np.power(newDM[i]-newDM[j],2))
            tcv.append(np.absolute(data['MJD'][i]-data['MJD'][j]))
            va.append(np.power(data['edm'][i],2)+np.power(data['edm'][j],2))
        
    tcv = np.core.records.fromrecords(tcv, names='tcv',formats='f8')
    sfv = np.core.records.fromrecords(sfv, names='sfv',formats='f8')
    va = np.core.records.fromrecords(va, names='va',formats='f8')
    
        
    pairs = tcv.copy()
    pairs = rfn.append_fields(pairs, ['sfv','va'], [sfv['sfv'],va['va']], usemask = False)
    pairs.sort(order='tcv')
    
    wn = pairs[pairs['tcv']<binsize/2.]
    wn = np.sum(wn['sfv']*1./wn['va'])/np.sum(1./wn['va'])
    
    sca, scaw, lags, npairs = [], [], [], []
    edge=binsize/2.
        
    for k in range(0,int(np.floor(tobs/binsize))):
        if k==0:
            center = 0
            lags.append(center)
            binsf = pairs[pairs['tcv']<edge]
            binsf = binsf[binsf['tcv']>0]
        else:
            center=k*binsize
            lags.append(center)
            binsf = pairs[pairs['tcv']<center+edge]
            binsf = binsf[binsf['tcv']>center-edge]                             
        sca.append(np.mean(binsf['sfv']))
        scaw.append(np.sum(binsf['sfv']/binsf['va'])/np.sum(1./binsf['va']))
        npairs.append(len(binsf))
    
    scawn = sca - wn
    scawwn = scaw - wn
        
    npairs = np.core.records.fromrecords(npairs, names='npairs',formats='f8')
    lags = np.core.records.fromrecords(lags, names='lags',formats='f8')
    sca = np.core.records.fromrecords(sca, names='sca',formats='f8')
    scaw = np.core.records.fromrecords(scaw, names='scaw',formats='f8')
    
    scawn = np.core.records.fromrecords(scawn, names='scawn',formats='f8')
    scawwn = np.core.records.fromrecords(scawwn, names='scawwn',formats='f8')
    
    
    
    #sf = lags.copy()
    #sf = rfn.append_fields(sf, ['scaw','scawwn','sca','scawn','npairs'], [scaw['scaw'],scawwn['scawwn'],sca['sca'],scawn['scawn'],npairs['npairs']], usemask = False)
    
    if h == 0:
        sfmat = lags.copy()
    
    sfmat = rfn.append_fields(sfmat, 'scawwn%s'%(h),scawwn['scawwn'], usemask = False)

fig = plt.figure()

for h in range(0,nrep):
    plt.loglog(sfmat['lags'],sfmat['scawwn%s'%h])

plt.xlabel("Lag [days]")
plt.ylabel(r"SF [DMu$^2$]")
plt.grid(which='both')
#insert Kolmogorov
tau_diff = 1./(60.*24.)#days
lags_kolm = np.arange(tau_diff, 4000.)
f = 150.*10**6 #Hz
K = 2.41*10**(-4)*10**(-12) #Hz^-2 cm^-3 pc s^-1
SF_kolm= (f*K/(2*np.pi))**2 * (lags_kolm/tau_diff)**(5./3.)
plt.loglog(lags_kolm,SF_kolm,color='g',linewidth=2,label='Kolmogorov')
plt.legend(loc='best')
plt.xlim(1,3000)


plt.savefig("SF_all_cut%s.png"%(int(cut)))

plt.close(fig)
#plt.show()



format = str("%.16f'")
for h in range(0,nrep):
    if h !=nrep-1:
        format = format + str(",'%.16f'")
    else:
        format = format + str(",'%.16f")



exec "np.savetxt(\"SF_all_cut%s.dat\", sfmat, fmt =[b'%s'])"%(int(cut),format)

sfmat_all = np.genfromtxt("SF_all_cut%s.dat"%(int(cut)))
lags = sfmat_all[:,0]
sfmat_all = sfmat_all[:,1:]
sfmat_all_m = np.mean(sfmat_all,axis=1)
sfmat_all_s = np.sort(sfmat_all,axis=1)

minussigma =sfmat_all_s[:,int(round(nrep*0.16))]
plussigma =sfmat_all_s[:,int(round(nrep*0.84))]

fig = plt.figure()
plt.xlabel('Lag [days]')
plt.ylabel(r'SF [DMu$^2$]')

plt.loglog(lags,sfmat_all_m,'k-',label='GLOW')
plt.loglog(lags,minussigma,'r-')
plt.loglog(lags,plussigma,'r-')
plt.grid(which='both')

#insert Kolmogorov
tau_diff = 1./(60.*24.)#days
lags_kolm = np.arange(tau_diff, 4000.)
f = 150.*10**6 #Hz
K = 2.41*10**(-4)*10**(-12) #Hz^-2 cm^-3 pc s^-1
SF_kolm= (f*K/(2*np.pi))**2 * (lags_kolm/tau_diff)**(5./3.)  
plt.loglog(lags_kolm,SF_kolm,color='g',label='Kolmogorov')

plt.legend(loc='best')
plt.tight_layout()
plt.xlim(1,3000)
plt.savefig("SF_data_cut%s.eps"%(int(cut)))

plt.close(fig)
#plt.show()

f = open("SF_data_cut%s.dat"%(int(cut)),'w')

for i in range(len(sfmat_all_m)):
    f.write("%.16f %.16f %.16f %.16f %d\n"%(lags[i],minussigma[i],sfmat_all_m[i],plussigma[i],npairs['npairs'][i]))

f.close()

#
#plt.figure()
#plt.loglog(sfcorr['lags'],sfcorr['scawwn'],color='k',linestyle='-',label='weighted-wnsubtracted')
##plt.loglog(sfcorr['lags'],sfcorr['scaw'],color='r',linestyle='-',label='weighted')
#plt.loglog(lags,SF_kolm,color='r',label='Kolmogorov')
#plt.grid(which='both')
#plt.xlabel('Log(Lag)')
#plt.xlabel('Log(SF[DMu^2])')
#plt.legend(loc='best')
#plt.savefig("SF_cut%s.png"%(int(cut)))
#plt.show()
#
#np.savetxt("SF_cut%s.dat"%(int(cut)),sf, fmt=[b'%.16f','%.16f', '%.16f','%.16f','%.16f','%d'])

