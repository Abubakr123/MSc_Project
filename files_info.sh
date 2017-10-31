#!/usr/bin/env bash



#pass the directory of the  main latex sript (header_plots.tex)
path="/home/abubakr/MSc_Project"

#prepare a list of the files
file_list="*.ar.pscr.zap.F"

#prepare and check the stem name (e.g B1122+25_D20140125T124533)
stem_name=`ls -1 *$file_list | awk -F '.'  '{print $1}'`
echo $stem_name

#creat a loop through the files with different exctensions
for f in $stem_name ; do
	echo "Start processing the table informations"
	sed  "s/xstem/$f/g" $path/header_plots.tex >> "${f}"_header_plots2.tex
	sed -i 's/_/\\_/g' "${f}"_header_plots2.tex
	name=`psredit -Q -q -c name $f.ar.pscr.zap.F`
	sed -i "s/xname/$name/g" "${f}"_header_plots2.tex
	sed -i 's/+/\$+$/g' "${f}"_header_plots2.tex
	nbin=`psredit -Q -q -c nbin $f.ar.pscr.zap.F`
	sed -i "s/xnbin/$nbin/g" "${f}"_header_plots2.tex
	npol=`psredit -Q -q -c npol $f.ar.pscr.zap.F`
	sed -i "s/xnpol/$npol/g" "${f}"_header_plots2.tex
	nchan=`psredit -Q -q -c nchan $f.ar.pscr.zap.T`
	sed -i "s/xnchan/$nchan/g" "${f}"_header_plots2.tex
	nsubint=`psredit -Q -q -c nsubint $f.ar.pscr.zap.F`
	sed -i "s/xnsubint/$nsubint/g" "${f}"_header_plots2.tex
	type=`psredit -Q -q -c type $f.ar.pscr.zap.F`
	sed -i "s/xtype/$type/g" "${f}"_header_plots2.tex
	length=`psredit -Q -q -c length $f.ar.pscr.zap.F`
	sed -i "s/xlength/$length/g" "${f}"_header_plots2.tex
	site=`psredit -Q -q -c site $f.ar.pscr.zap.F`
	sed -i "s/xsite/$site/g" "${f}"_header_plots2.tex
	rm=`psredit -Q -q -c rm $f.ar.pscr.zap.F`
	sed -i "s/xrm/$rm/g" "${f}"_header_plots2.tex
	dm=`psredit -Q -q -c dm $f.ar.pscr.zap.F`
	sed -i "s/xdm/$dm/g" "${f}"_header_plots2.tex
	freq=`psredit -Q -q -c freq $f.ar.pscr.zap.F` 
	sed -i "s/xfreq/$freq/g" "${f}"_header_plots2.tex
	bw=`psredit -Q -q -c bw $f.ar.pscr.zap.F`
	sed -i "s/xbw/$bw/g" "${f}"_header_plots2.tex
	coord=`psredit -Q -q -c coord $f.ar.pscr.zap.F`
	sed -i "s/xcoord/$coord/g" "${f}"_header_plots2.tex
	snr=`psrstat -Q -q -j tscrunch -c snr $f.ar.pscr.zap.F`
	sed -i "s/xsnr/$snr/g" "${f}"_header_plots2.tex 
	rfi_sum=`sed '1,4d' $f.psh | wc -l`
	RFI_percent=$(echo "($rfi_sum/($nsubint * $nchan)) * 100" | bc -l) 
	sed -i "s/xRFI/$RFI_percent/g" "${f}"_header_plots2.tex

	echo "Table infomation updated. Start producing the plots and convert them to pdf files."

	fprof_plot=`psrplot -D "${f}_fprof.ps/cps" -p freq+ -j 'tscrunch' -j 'dedisperse' $f.ar.pscr.zap`
	ps2pdf ${f}_fprof.ps ${f}_fprof.pdf
	rm ${f}_fprof.ps
	sed -i "s/xfprof/${f}_fprof.pdf/g" "${f}"_header_plots2.tex

	ds_plot=`pav -g "${f}_ds.ps/cps" -j $f.ar.pscr.zap` 
	ps2pdf ${f}_ds.ps ${f}_ds.pdf
	rm ${f}_ds.ps
	sed -i "s/xds/${f}_ds.pdf/g" "${f}"_header_plots2.tex

	bp_plot=`pav -g "${f}_bp.ps/cps" -J $f.ar.pscr.zap.T`
	ps2pdf ${f}_bp.ps ${f}_bp.pdf
	rm ${f}_bp.ps
	sed -i "s/xbp/${f}_bp.pdf/g" "${f}"_header_plots2.tex

	avprof_plot=`pav -g "${f}_avprof.ps/cps" -DTd $f.ar.pscr.zap.F`
	ps2pdf ${f}_avprof.ps ${f}_avprof.pdf
	rm ${f}_avprof.ps 
	sed -i "s/xavprof/${f}_avprof.pdf/g"  "${f}"_header_plots2.tex

	stack_plot=`pav -g "${f}_stack.ps/cps" -Yd $f.ar.pscr.zap.F`
	ps2pdf ${f}_stack.ps ${f}_stack.pdf
	rm ${f}_stack.ps
	sed -i "s/xstack/${f}_stack.pdf/g" "${f}"_header_plots2.tex

	echo "Run pdflatex to get pdf version of the the latex template."
	pdflatex ${f}_header_plots2.tex

done

echo "Latex template done. Producing final combined pdf file."
pdfjoin *_header_plots2.pdf --a4paper --no-landscape  -o combined_files.pdf --rotateoversize false

echo "End of Processing"
