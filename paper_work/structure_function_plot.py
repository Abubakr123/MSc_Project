import matplotlib.pyplot as plt
import numpy as np
import sys
from matplotlib.ticker import ScalarFormatter

sf_file = sys.argv[1]
psr_name = sys.argv[2]

#read the data file
Data = np.loadtxt(sf_file)
tau = Data[:,0]
DDM = Data[:,1]
DDM_err = Data[:,2]
n_pairs = Data[:,3]

#cut the first values and add log scale
tau=tau[10:]
DDM=DDM[10:]
DDM_err=DDM_err[10:]

log_tau = np.log10(tau)
log_DDM = np.log10(DDM)

slope, intercept = np.polyfit(log_tau, log_DDM, deg=1)
p = np.polyfit(log_tau, log_DDM, deg=1)
y = 10**intercept*tau**slope
print("slope = ", slope)

#calculate the offset
a=5./3.
b=[]
for i in range(len(DDM)):
    b_i = log_DDM[i] - a*log_tau[i]
    b.append(b_i)

y_intercept = np.mean(b)

#Kolmogorov
kolm= 10**y_intercept*tau**(5./3.)


fig=plt.figure()
ax = plt.axes()
ax.set_xscale('log', nonposy="clip")
ax.set_yscale('log', nonposy="clip")

for axis in [ax.xaxis]:
    axis.set_major_formatter(ScalarFormatter())

plt.errorbar(tau, DDM, yerr=DDM_err, fmt='.k', elinewidth=2,  mfc='k')
plt.plot(tau, kolm, color='g', linestyle='dashed', linewidth=2, label='Kolmogorov Spectrum')
plt.xlabel("Time Lag [days]")
plt.ylabel(r"Log$_{10}$ [D$_{DM}(\tau)}$]")
plt.xlim(10, 3000)
plt.ylim(np.min(DDM)*-2, np.max(DDM)*2)
plt.title("PSR %s"% psr_name)
plt.legend(loc='lower right')
plt.grid(which='both')
plt.savefig('SF_Kolm_%s.png' % psr_name)
plt.show()
