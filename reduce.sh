#!/bin/bash

files="B0138+59_D20150301T150201 B0138+59_D20150308T133201 B0138+59_D20150315T133201 B0138+59_D20150405T112201 B0138+59_D20150412T112201 B0138+59_D20150419T101701"

for i in $files; do
	echo $i "in the prosessing"
	python2.7 reduceSingleStation_modefy.py --stem $i 

done 
