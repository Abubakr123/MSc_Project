#!/bin/bash
#Usage:./my_script.sh > list_ps_files.txt

#Creating a loop for zap files 
for i in *.zap; do
    printf 'psrplot -D "%s_fprof.ps/cps" -p freq+ -j "tscrunch" -j "dedisperse" %s\n' "$i" "$i"	 #plot the bandpass (power vs frequency) and integrated dedispersed pulse
    printf 'pav -g "%s_ds.ps/cps" -j %s\n' "$i" "$i" 		#Display a simple dynamic spectrum image 
done

#looping through the time scrunch files
for i in *.T; do
    #printf 'pav -g "%s_fprof.ps/cps" -Gd %s\n' "$i" "$i" 	#Plot an image of amplitude against frequency & phase 
    printf 'pav -g "%s_off_bp.ps/cps" -J %s\n' "$i" "$i" 	#Plot off-pulse bandpass & channel weights

done

#looping through time scrunch files
for i in *.F; do
    printf 'pav -g "%s_avprof.ps/cps" -DTd %s\n' "$i" "$i"	#plot a single profile(chan 0, poln 0, subint 0)
    printf 'pav -g "%s_stack.ps/cps" -Yd %s\n' "$i" "$i"	#Plot sub-integrations against pulse phase 
done





