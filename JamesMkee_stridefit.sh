#! /bin/bash


par_file=$1
tim_file=$2
fit_window=$3
step_size=$4
option_start_mjd=$5
option_end_mjd=$6
fit_parameter=$7
output_file="output.dat"

tempo2_path=("tempo2")

if [ $7 = "F0" ];
	then
	fit_parameter="F0"
fi	
if [ $7 = "F1" ];
	then
	fit_parameter="F1"
fi

if [ $7 = "DM" ];
	then
	fit_parameter="DM ("
fi	 


cp $par_file temp.par
start_mjd=$option_start_mjd
end_mjd=$((start_mjd+fit_window))

echo "START		" $start_mjd "1" >> temp.par
echo "FINISH		" $end_mjd "1" >> temp.par

if [ "$fit_parameter" = "DM (" ]
	then
	fit_value=$($tempo2_path -f temp.par $tim_file | grep "$fit_parameter" | awk '{print $5 " " $6}')
	echo $start_mjd " " $end_mjd " " $fit_value >> $output_file	
	rm temp.par
fi
if [ "$fit_parameter" != "DM (" ]
	then
	fit_value=$($tempo2_path -f temp.par $tim_file | grep "$fit_parameter" | awk '{print $4 " " $5}')
	echo $start_mjd " " $end_mjd " " $fit_value >> $output_file	
	rm temp.par
fi

while [ $end_mjd -lt $option_end_mjd ]
do 
	cp $par_file temp.par
	start_mjd=$((start_mjd+step_size))
	end_mjd=$((end_mjd+step_size))
	
	echo "START		" $start_mjd "1" >> temp.par
	echo "FINISH		" $end_mjd "1" >> temp.par

	if [ "$fit_parameter" = "DM (" ]
		then
		fit_value=$($tempo2_path -f temp.par $tim_file | grep "$fit_parameter" | awk '{print $5 " " $6}')
		echo $start_mjd " " $end_mjd " " $fit_value >> $output_file	
		rm temp.par
	fi
	if [ "$fit_parameter" != "DM (" ]
		then
		fit_value=$($tempo2_path -f temp.par $tim_file | grep "$fit_parameter" | awk '{print $4 " " $5}')
		echo $start_mjd " " $end_mjd " " $fit_value >> $output_file	
		rm temp.par
	fi
done
