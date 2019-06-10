#!/bin/bash

observations="$1"
PSR_name="$2"


python2.7 ~/Desktop/paper-work/zap_channels.py $observations

# Update the observations using the generated parfile for the thesis
# (since I'm using unupdated data i.e. zap or T scrunched)
pam --update_dm -E  ../Second_loop/new_parfile.par *.F350 -T -e T

# Add files, weight, tscrunch, smooth the template
psradd -P -o template.prof *.zap.T

#to caheck for RFI)
pazi template.prof -e prof.pazi

python2.7 ~/MSc_Project/paper_work/set_profile_wt.py --snrsq -R -e pazi.weighted template.prof.pazi

pam -m -D --setnchn 10 -T -p template.prof.pazi.weighted -e weighted.F10

psrsmooth -W template.prof.pazi.weighted.F10

# Generate the ToAs
pat -A FDM:mcmc=1 -P -s template.prof.pazi.weighted.F10.sm -f tempo2 -j "F 10" *.T >> ToAs.tim

# Check and Update the par, tim files. In case there are some outlire ToAs
tempo2 -gr plk -f parfile.par ToAs.tim

# Calculate the DM measurements
bash ~/MSc_Project/paper_work/scripts/jd_calcDMseries.bash -a="-O -U -C=5 -R" -p=new_parfile.par -t=new_timfile.tim>> DMfile.txt

# Plot the DM variations
python2.7 ~/MSc_Project/paper_work/plot_dm.py DMfile.txt $PSR_name


bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=4 -median DMfile.txt

bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=5 -median DMfile.txt

bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=6 -median DMfile.txt

bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=3 -ecol=4 -mean DMfile.txt
bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=3 -ecol=4 -rms -o=3.9902402540e+01 DMfile.txt

