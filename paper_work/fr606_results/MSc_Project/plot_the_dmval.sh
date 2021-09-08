#!/bin/bash

echo "__________GNUPLOT_________"  #Plot DM SAUVE/DMofT$PSRNAME-$TIM.ps
echo -e 'set term postscript color solid\nset output "dmvals_J0613+3731_dmvals-2015-09-07.ps"
set border 15
#set xtics 50
set mxtics 4
#set ytics 0.0005
#set yra [10:45]
set mytics 2
set xlabel "t [MJD]"
set ylabel "DM [pc/cm^3]" offset 2,0
set title "dmvals-J0613+3731-dmvals-2015-09-07-attmp"
set noclip one
set size 1.2,1
set grid xtics ytics
set key outside top Left reverse width -1  box spacing 1.2
f(x)=c+b*(x-56925)
b=20.0
c=1E-6
fit f(x) "dmvals_J0613+3731_3rd_attmp.dat" using 1:2:3 via b,c
plot \
     "dmvals_J0613+3731_3rd_attmp.dat" using 1:2:3 with errorbars lt 1 pt 6 title "DM-J0613+3731",\
     "dmvals-2015-09-07.dat" using 1:2:3 with errorbars lt 3 pt 6 title "DM-2015-09-07",
      f(x) w l title "lin reg"' >> test.gpl
	gnuplot test.gpl
	#mv DMofT.ps SAUVE/DMofT.ps
	#gv SAUVE/DMofT$PSRNAME.ps &
