import numpy as np
import matplotlib.pyplot as plt
import sys

PSR = sys.argv[1]

# Read the data from dmvals.dat file
name = np.loadtxt('dmvals.dat')
MJD=name[ :,0]
angle=name[ :,1]
dm=name[ :,2]
dm_err=name[ :,3]


fig=plt.figure()

# The first subplot
ax1 = plt.subplot(2, 1, 1)
ax1.plot(MJD, angle,'.' , label = "Object's path from SUN")
plt.ylabel('Solar angle [deg]')
plt.title("The DM and solar angle for %s" % PSR)

# The second subplot
ax2 = plt.subplot(2, 1, 2)
ax2.errorbar(MJD[np.where(angle>20)], dm[np.where(angle>20)], dm_err[np.where(angle>20)], label="angle > 20",ls='dotted', marker='o', ms=3, color='magenta')
ax2.errorbar(MJD[np.where(angle<=20)], dm[np.where(angle<=20)], dm_err[np.where(angle<=20)], label="angle <= 20", ls='dotted', marker='o', ms=3, color='b')
plt.xlabel("Days [MJD]")
plt.ylabel(r"DM [pc cm$^{-3}$]")
plt.grid(which='both')
plt.legend(loc='best',fontsize=10,fancybox=True).get_frame().set_alpha(0.5)

# Shared the x-axis between the two plots
ax1.get_shared_x_axes().join(ax1, ax2)
ax1.set_xticklabels([])
plt.subplots_adjust(hspace=0)


# Save the figure
plt.savefig("solar_angle_path_%s.png" %PSR)
plt.show()


