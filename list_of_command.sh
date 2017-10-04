#!/bin/bash

#Adding the input, output and the name of the pulsar list as arguments and print them
path="$1"
output_dir="$2"
pulsar_list="$3"
software_path="/home/abubakr/MSc_Project/"

echo "The name of the pulsar list is" $pulsar_list
echo "The software path is" $software_path
echo "The input path directory is" $path

#Using awk to construct the stem name 
ls -1 $path/*_122_133.ar | awk -F "/|_" '{print $6 $7 "_" $8  }'|

#Create the list of command lines
while read -r; do
  echo "python2.7 "$software_path"reduce_single_station.py --stem "$REPLY" --indir "$path" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$pulsar_list

done



