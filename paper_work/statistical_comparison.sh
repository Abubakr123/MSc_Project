#!/bin/bash

DMfile="$1"

DMunc=`bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=4 -median $DMfile`
echo -e "\n"$DMunc "=> median DM uncertainty"

DMchi=`bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=6 -median $DMfile`
echo $DMchi "=> median red. chi^2 of the DM fits"

ToAsfit=`bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=5 -median $DMfile`
echo $ToAsfit "=> median number of ToAs in the DM fits"

echo -e "\n***Calculate the weighted RMS of Delta DMs:"
DMwMean=`bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=3 -ecol=4 -mean $DMfile`
echo $DMwMean "=> weighted mean of the DM fits"
rms=`bash ~/MSc_Project/paper_work/scripts/jd_calc_stats.bash -col=3 -ecol=4 -rms -o=$DMwMean $DMfile`
echo -e "The weighted RMS of Delta DMs\n"$rms


echo -e "\nRemoving the lines of observations where the DM calculation failed"
echo "and comparing the number of lines to check the rejected observations"
grep -v CALCDM $DMfile > DMfile.good
wc -l $DMfile
wc -l DMfile.good
