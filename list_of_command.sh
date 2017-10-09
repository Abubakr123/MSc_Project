#!/bin/bash

#Adding the input, output and the name of the pulsar list as arguments and print them
path="$1"
output_dir="$2"
pulsar_list="$3"
software_path="/home/abubakr/MSc_Project/"

echo "The name of the pulsar list is" $pulsar_list
echo "The software path is" $software_path
echo "The input path directory is" $path

#checking and creating a new directory to the outputs

echo "Enter the output Directory Name: " $output_dir

if [[ ! -d "$output_dir" ]]
then
	echo "Directory doesn't exist. Creating now"
	mkdir $output_dir 
	echo "Directory created"
else
	echo "Directory exists"

fi


#Using awk to construct the stem name 
ls -1 $path/*_122_133.ar | awk -F "/|_" '{print $9 $10 "_" $11  }'|

#Create the list of command lines
while read -r; do
  echo "python2.7 "$software_path"reduce_single_station.py --stem "$REPLY" --indir "$path" --outdir "$output_dir" --tscr --fscr --psrsh --clean --verbose">>$pulsar_list

done



