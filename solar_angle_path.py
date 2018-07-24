import numpy as np
import matplotlib.pyplot as plt
import sys

PSR = sys.argv[1]
name = np.loadtxt('angle.txt')
MJD=name[ :,0]
angle=name[ :,1]
#print angle

plt.figure()
plt.plot(MJD, angle, '.' , label = "Object's path from SUN")
plt.grid(which='both')
plt.xlabel('Days(MJD)')
plt.ylabel('Angle(degrees)')
plt.title("The angle between the Sun and %s" % PSR)
plt.legend(loc='best',fontsize=10,fancybox=True).get_frame().set_alpha(0.5)
plt.savefig("solar_angle_path_%s.png" %PSR)
plt.show()


