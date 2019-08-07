#!/bin/bash


if [ "$1" = "-h" ] ; then
  echo "Usage: data_analysis.sh  <archive> <PSR_name> <DMfile> <template>"
  exit 0
fi


observations="$1"
PSR_name="$2"
DMfile="3"
template="4"

python2.7 ~/Desktop/paper-work/zap_channels.py $observations


#### First check the bad observations by execlude all the bad observations
#from the observation using the combined pdf ######


# Update the observations using the generated parfile for the thesis
# (since I'm using unupdated data i.e. zap or T scrunched)
pam --update_dm -E  ../Second_loop/new_parfile.par *.F350 -T -e T

# Add files, weight, tscrunch, smooth the template
psradd -P -o template.prof *.zap.T

# Clean the template
python2.7 ~/MSc_Project/paper_work/iterative_cleaner.py $template

# to caheck for RFI)
pazi template.prof -e prof.pazi


# Center the pulse of the frequency plot
pav -C -G $template

python2.7 ~/MSc_Project/paper_work/set_profile_wt.py --snrsq -R -e pazi.weighted template.prof.pazi

pam -m -D --setnchn 10 -T -p template.prof.pazi.weighted -e weighted.F10

psrsmooth -W template.prof.pazi.weighted.F10

#PLot the profile evolution of the template
python2.7 ~/MSc_Project/paper_work/waterfall.py -T $template -P $PSR_name

#Compare differnt number of frequency channels
bash ~/MSc_Project/paper_work/statistical_comparison.sh $DMfile >> statistical_comparason.txt

# Generate the ToAs
pat -A FDM:mcmc=1 -P -s template.prof.pazi.weighted.F10.sm -f tempo2 -j "F 10" *.T >> ToAs.tim

# Check and Update the par, tim files. In case there are some outlire ToAs
tempo2 -gr plk -f parfile.par ToAs.tim

# Calculate the DM measurements
bash ~/MSc_Project/paper_work/scripts/jd_calcDMseries.bash -a="-O -U -C=5 -R" -p=new_parfile.par -t=new_timfile.tim>> DMfile.txt

# Plot the DM variations
python2.7 ~/MSc_Project/paper_work/plot_dm.py DMfile.txt $PSR_name


# Get the SF values
~/MSc_Project/paper_work/calcStructureFunc -w -i DMfile.txt -col_DM 3 -col_DMerr 4 -v -tau 3 -tau_factor 1.25 -o J0613+3731_sf.dat

# Plot SF
ipython ~/MSc_Project/paper_work/structure_function_plot.py J0613+3731_sf.dat J0613+3731
