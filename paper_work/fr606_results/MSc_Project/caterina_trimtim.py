#!/usr/bin/env python
#Caterina Tiburzi, 2017

from __future__ import print_function
import numpy as np
import os, argparse, math
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter


import pandas as pd
from itertools import izip
from sklearn import linear_model
from sklearn.linear_model import HuberRegressor
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from statsmodels import robust
import weightedstats as ws

#------------------------------------------------arguments


parser = argparse.ArgumentParser(description="Get DM variations")

parser.add_argument('-o', '--observation', type=str, nargs=1,
                    help="Observation name")

parser.add_argument('-e', '--pulsarephemeris', type=str, nargs=1,
                    help="Current ephemeris")

parser.add_argument('-q', '--equad', type=int, nargs=1,
                    help="EQUAD")

args = parser.parse_args()

obs = args.observation[0]
ephemeris = args.pulsarephemeris[0]


if args.equad:
    equad = args.equad[0]

equad_exists = 'equad' in locals() or 'equad' in globals()

#print("Now cutting the edges of the bandpass")

os.system("cat %s| awk '{if ($2>115 && $2<185 && $4 != 0) print $0}'> %s_tmp"%(obs,obs))
os.system("sed -i '1iFORMAT 1' %s_tmp"%(obs))

#print("Now getting the residuals in output from general2")

#print("tempo2 -output general2 -f %s %s_tmp -s \"tadan {freq} {pre} {err}e-6\n\" | grep 'tadan'| awk \'{print $2,$3,$4}\' > tmp.dat"%(ephemeris,obs))
os.system("tempo2 -output general2 -f %s %s_tmp -s \"tadan {freq} {pre} {err}e-6\n\" | grep 'tadan'| awk \'{print $2,$3,$4}\' > tmp.dat"%(ephemeris,obs))


#print("Now fitting a parabola to the residuals with Huber regressor")

freq, pre, err = np.genfromtxt("./tmp.dat")[:,0], np.genfromtxt("./tmp.dat")[:,1], np.genfromtxt("./tmp.dat")[:,2]
#freq, pre, err = freq.reshape(-1,1), pre.reshape(-1,1), err.reshape(-1,1)
#freq, pre = freq.reshape(-1,1), pre.reshape(-1,1)
freq = freq.reshape(-1,1)

os.system("rm tmp.dat")

model = make_pipeline(PolynomialFeatures(2), HuberRegressor())#ERROR BAR??????? # Fixed, see lines below.
## model.fit(freq,pre,huberregressor__sample_weight=err) This wont work because of the shape (338,1) of the err column. I just flattened it into a 1D array.

model.fit(freq,pre,huberregressor__sample_weight=np.ravel(1/err)) # And this works. :)

#print("Now identifying and rejecting the outliers")

y_pred = model.predict(freq)
residuals = pre - y_pred

##median = ws.weighted_mean(residuals[:,0], weights=1/err)
#median = np.median(residuals[:,0])#ERROR BAR????????
#MAD = robust.mad(residuals[:,0])#ERROR BAR????????
#mask =  (residuals[:,0] > median - 3*MAD) & (residuals[:,0] < median + 3*MAD)

median = np.median(residuals)#ERROR BAR????????
MAD = robust.mad(residuals)#ERROR BAR????????
mask =  (residuals > median - 3*MAD) & (residuals < median + 3*MAD)

freq_in = freq[mask]
pre_in = pre[mask]
err_in = err[mask]


#PLOT
#plt.errorbar(freq,pre,yerr=err,fmt='k.')
#x_plot = np.linspace(freq.min(), freq.max())
#y_plot = model.predict(x_plot[:, np.newaxis])
#plt.plot(x_plot,y_plot,'r-')
#plt.errorbar(freq_in,pre_in,yerr=err_in,fmt='b.')
#plt.show()

#print("Now getting the ToAs newly and putting them in a dataframe")

df = pd.read_csv("%s_tmp"%(obs), skiprows=1, dtype=str, header=None, delim_whitespace=True, names=["name", "freq", "toa", "err", "site", "key1", "frontend", "key2", "backend", "key3", "unknown", "key4", "bandwidth", "key5", "length", "key6", "template", "key7", "gof", "key8", "nbin", "key9", "snr"])



#print("Now applying the boolean mask")

df['inliers'] = mask
df = df[df.inliers != False]
del df['inliers']

#print("Now dumping them to file")

df.to_csv("%s_trimtim"%(obs), sep=' ', header=False, index=False)
#df.to_csv("%s_trimtim"%(obs), sep=' ', header=False, index=False, float_format='%.18f',float_precision='round_trip')
#df.to_csv("%s_trimtim"%(obs), sep=' ', header=False, index=False, float_precision='round_trip')

os.system("rm %s_tmp"%(obs))


os.system("sed -i '1iFORMAT 1' %s_trimtim"%(obs))



if equad_exists == True:
    os.system("sed -i '1iEQUAD %d' %s_trimtim"%(equad,obs))

    


#print("Problems: 1) precision of ToAs is corrupted, 2) Huber with error bars??")
