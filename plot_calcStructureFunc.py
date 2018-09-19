import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd
from pandas import Series
#read the data from dmvals.dat file
name = np.loadtxt('structure_function.dat')
tau = np.array(name[ :,0])
dDM = np.array(name[ :,1])
dDM_err = np.array(name[ :,2])


np_clean = [x for x in dDM if str(x) != 'nan']
print"SF", np_clean 


dDM=np_clean#[np_clean]
dDM_err=dDM_err[ :-3]#[np_clean]
tau=tau[ :-3]#[np_clean]

print"SF_uncer", dDM_err
print"tau0, tau"
logA = np.log(tau) #no need for list comprehension since all z values >= 1
logB = np.log(dDM)
print np.shape(logA)
print np.shape(logB)


m, c = np.polyfit(logA, logB, 1) # fit log(y) = m*log(x) + c
y_fit = np.exp(m*logA + c) # calculate the fitted values of y




#plots
fig=plt.figure()
ax=plt.gca()
plt.errorbar(tau, dDM, yerr = dDM_err, marker='o', ms=5, ls='dotted', color ='b', label='SF')
plt.plot(tau, y_fit, ':', color='r', label="Fitting")
ax.set_xscale('log')
ax.set_yscale('log')
plt.xlabel("Lag [days]")
plt.ylabel(r"SF [DMu$^2$]")
plt.legend(loc='best')
plt.grid(which='both')
ax.set_title('The Structure Function')
plt.savefig("calcStructureFunction.png")
plt.show()


slope, intercept = np.polyfit(logA, logB, 1)
print "the slope , intercept: ", slope, intercept




