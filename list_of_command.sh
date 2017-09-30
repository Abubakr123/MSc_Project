#!/bin/bash

path="$1"

#creat a list of command lines 
echo "The path directory " $path
ls -1 $path/*_122_133.ar | awk -F "/|_" '{print $9 $10 $11 }'|

while read -r; do
  echo "python2.7 /home/abubakr/MSc_Project/reduce_single_station.py --stem "$REPLY" --indir /data0/abubakr/B0138+59/raw --outdir /data0/abubakr/B0138+59/result --tscr --fscr --psrsh --clean --verbose">>list_of_command.txt

done



