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

#find / -type f -name "psrchive.py"

#### First check the bad observations by execlude all the bad observations
#from the observation using the combined pdf ######
pdfjoin *_header_plots2.pdf --a4paper --no-landscape  -o combined_files_J1932+1059_full.pdf --rotateoversize false

# check the centeral/number of frequency
psrstat -c nchan,nsubint,freq *.T

# Update the observations using the generated parfile for the thesis
# (since I'm using unupdated data i.e. zap or T scrunched)
pam --update_dm -E  ../Second_loop/new_parfile.par *.F350 -T -e T

# Add files, weight, tscrunch, smooth the template
psradd -P -v -o template.prof *.zap.T

# Clean the template
python2.7 ~/MSc_Project/paper_work/iterative_cleaner.py $template

# to caheck for RFI)
pazi template.prof -e prof.pazi


# Center the pulse of the frequency plot
pav -C -G $template

python2.7 ~/MSc_Project/paper_work/set_profile_wt.py --snrsq -R template.prof_cleaned.ar -e ar.weighted 

pam -m -D --setnchn 10 -T -p template.prof_cleaned.ar.weighted -e weighted.F10

psrsmooth -W template.prof_cleaned.ar.weighted.F10

#PLot the profile evolution of the template
python2.7 ~/MSc_Project/paper_work/waterfall.py -T $template -P $PSR_name

#Compare differnt number of frequency channels
bash ~/MSc_Project/paper_work/statistical_comparison.sh $DMfile >> statistical_comparason.txt

# Generate the ToAs
pat -A FDM:mcmc=1 -P -s template.prof.pazi.weighted.F10.sm -f tempo2 -j "F 10" *.F350 >> ToAs.tim

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


'''
packup the result to git and the nancey server as soon as you done

Tempo2 commands
z #to highlite a region/group of toas
o #to select all the toas
ctrl+d #to delet the selected toas
u #to plot all the t2 window




Below I describe the procedure to create a template profile and ToAs:
- First of all, from my experience psrchive works better when the archives 
are _not_ dedispersed, i.e. 'psredit -c dmc <file>' should show 'dmc=0'. You 
can undo the dedispersion with 'pam --DD'.
- To create the template, I run 'psradd -o <template> <files>', where the 
ephemeris in the files should be good to align all observations, i.e. in 
tempo2 there should be no clear structure and the chisq close to 1 - although 
a chisq of 2 or so is probably not a big problem. The files should all have 
the same frequency channels.
- Then I run 'set_profile_wt.py --snrsq -R -e wt <template>'. The script is 
attached to this email. You could also try other weighting schemes. For very 
low S/N pulsars you might want to fscrunch (see below) before weighting (but 
not tscrunch), in case the pulsar is not visible in individual channels.
- Then I tscrunch the template, and also fscrunch to the desired number of 
frequency channels in the timing (e.g. 10). Also, pat wants the template to 
be dedispersed and we don't need polarisation information, so I run: 'pam -D 
--setnchan 10 -T -p -e <ext> <weighted_template>'.
- Now we can smooth the template with 'psrsmooth -W <template>'.
- Now we can do the timing: 'pat -A FDM:mcmc=1 -P -s <template> -f tempo2 -j 
"F 10" <Tp-scrunched (not dedispersed) observations> > ToAs.tim'. '-A' choses 
the algorithm. FDM gives more robust uncertainties than the default PGS. '-P' 
prevents pat from scrunching the template and thus allows to use the 
frequency-resolved template. (Note: pat will always time channel 0 in the 
observation versus channel 0 in the template, channel 1 vs channel 1 and so 
on. So the observation and template *must* have the same frequency channels.) 
'-j "F 10"' tells pat to do a preprocessing job, in this case fscrunching to 
10 frequency channels. You could also fscrunch the observations with pam 
before and remove this option, but I prefer it this way as you don't create 
so many files on the disks. '-f tempo2' sets the format for tempo2 and '-s' 
selects the standard template.

Please let me know if this is understandable and clear and feel free to ask 
if anything is unclear.

Cheers,
Julian
'''
