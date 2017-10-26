#!/usr/bin/env bash
for f in *.zap.T ; do
	ls -1 $f
	stem=`psredit -c file $f`
	name=`psredit -c name $f`
	nbin=`psredit -c nbin $f`
	npol=`psredit -c npol $f`
	nchan=`psredit -c nchan $f`
	nsubint=`psredit -c nsubint $f`
	type=`psredit -c type $f`
	length=`psredit -c length $f`
	site=`psredit -c site $f`
	rm=`psredit -c rm $f`
	dm=`psredit -c dm $f`
	freq=`psredit -c freq $f` 
	bw=`psredit -c bw $f`
	#sed  "s/bw/$bw/g" header_plots.tex
	coord=`psredit -c coord $f`
	snr=`psrstat -j fscrunch -c snr $f`
	#rfi_sum=`wc -l $f` | sed '1,4d'  
	#\%RFI=$(echo `($rfi_sum/($nsubint*$nchan))*100.0` | bc )
	#$echo $rfi_sum
	echo $bw
	echo $snr
	echo $nchan
	echo $nsubint
done
