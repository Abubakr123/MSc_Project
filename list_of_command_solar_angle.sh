#!/bin/bash

echo -e "Help\n bash ~/MSc_Project/list_of_command_solar_angle.sh\n xjobs -j 3 -t -s observations_list_angle.txt\n ipython2 ~/MSc_Project/solar_angle_path.py PSR"

#Adding the input, output and the name of the pulsar list as arguments and print them
ext="$1"
#output_dir="$2"
#observations_list="$1"
software_path="/home/abubakr/MSc_Project/"



#Using awk to construct the stem name 
ls -1 *.$ext |
#Create the list of command lines
while read -r; do
  echo "python2.7 "$software_path"solar_angle.py "$REPLY" >> angle.txt" >> observations_list_angle.txt
done 
