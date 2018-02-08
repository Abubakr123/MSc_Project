#!/bin/bash
VERSION=1.0.1
DATUM=13.09.2015
CODENAME=mypsr_split.sh

#

#definition of the principal directory, location of the parfiles directory
#but the code can work without the parfiles directory

DIR=/data/guestnode3
lucasscripts=/home/artemis/lucasscripts # directory for lucas scripts
setuptempo2=/data/guestnode3/script/plk_setup_fr606_embrace.dat

PSRNAME=`basename $PWD`
backend=`ls data/links/` #nom du dossier backend

file=`ls data/links/$backend/* | head -1`
file=`basename $file`
site=`psredit -c site data/links/$backend/$file | cut -d "=" -f2` 

echo '---------------------------------------------

        \  |		#	SCRIPT 	'$CODENAME'
         \ |		#	V: '$VERSION'
          \|		#	DATUM: '$DATUM'
           O		#	Autor: Louis Bondonneau
           |\		#
           | \		#
           |  \		#

'
echo "site=$site"

#création du dossier SAUVE
if [[ ! -e "SAUVE" ]]
then
	mkdir SAUVE
fi



function FIRSTPARFILE(){
	echo -e ":\n\n\n	Le mode automatique utilise une recherche dans $DIR/parfiles/new/, le dossier courant ou utilise vap -E sur les données."
	echo -e "\n\n\nHow would you want select your parameter file ?"
	echo ""
	options=("Manually" "chose in current directory" "Automatic" "Return" )
	select opt in "${options[@]}"
	do
		case $opt in



			'Manually')

	read -p "way to your parameter file:" PAR
	if  [[ ! -f $PAR ]]
	then
		while [[ ! -e $PAR ]]
		do
			echo "$PAR are not found"
			read -p "way to your valide parameter file:" PAR
		done
	fi
	echo $PAR
	break
				;;
			'chose in current directory')

	PARSELECT
	echo $PAR
	break
				;;




			'Automatic')

	filelist=($DIR/parfiles/new/$PSRNAME*.par) #liste des fichiers .par dans $DIR/parfiles/new
	filelist2=(./$PSNAME*.par) #liste des fichiers .par dans le dossier courant

	#par le plus récent dans le dossier $DIR/parfiles/new/ 
	#Sinon dans le dossier courant
	#ou alors on le récupère avec un vap -E
	if [[ -f "$filelist" ]] 
	then
		echo "$filelist found"	
		PAR=`ls $DIR/parfiles/new/$PSRNAME*.par -got | head -1 | awk '{print $7}'`
	else
		if [[ -f "$filelist2" ]]
		then
		echo "par found in current dir"
		PAR=`ls -got | grep \.par | head -1| awk '{print $7}'`
		else
			echo "no .par file found vap -E file will be used"
			#psrcat -e $PSRNAME >$DIR/parfiles/orig/$PSRNAME.par
			firstfile=`ls data/links/LuMP/ | head -1`
			#vap -E data/links/$backend/$firstfile | tail -n +2 >$DIR/parfiles/orig/$PSRNAME.par
			#PAR=$DIR/parfiles/orig/$PSRNAME.par
			vap -E data/links/$backend/$firstfile | tail -n +2 >$PSRNAME.par
			PAR=$PSRNAME.par
			echo "file found: $PSRNAME.par"
		fi
	fi
	echo $PAR
	break
				;;




			'Return')
			displayMainMenu
				;;
			*)
		 		echo "Invalid option, enter a number"
		 		;;
		esac
	done
	echo $PAR
	
	#tempo1 tempo2 transformation
	parvers=`less $PAR | grep EPHVER | grep -o '[0-9]'`
	if [[ $parvers == '2' ]]
	then
		echo "parfile version is update for tempo2"
		tempo2 -gr transform $PAR $PAR
	fi
}



function TEMPO2_2(){
echo "__________TEMPO2_2nd_________"
	
	tempo2 -gr plk -nspr 1 -nofit -nobs 30000 -f $PAR -setup $setuptempo2 $TIM

	PAR=`ls -got | grep \.par | head -1| awk '{print $7}'`
	echo 'the last .par file is: '$PAR
	TIM=`ls -got | grep \.tim | head -1| awk '{print $7}'`
	echo 'the last .tim file is: '$TIM
}



function DMVAL(){
	#plot DM variation
	rm test.gpl
	rm dmvals.dat
	rm strides.dat
	tail -n +2 $TIM | grep -v "C "| cut -d " " -f4 | cut -d "." -f1 | awk '{print ($1)" "($1)+1" a a"}' > strides.dat #creat the stride file
	echo "__________TEMPO2_last_________"
	tempo2 -gr dm -t strides.dat -nspr 1 -nobs 30000 -f $PAR $TIM

	rm dmvals_$TIM.dat
	mv dmvals.dat dmvals_$TIM.dat
	
	echo -e "results_err_DMvals_$TIM"\n >> SAUVE/results.txt #SAUVE error on DM
	python $DIR/python/median_dmvals.py dmvals_$TIM.dat >> SAUVE/results.txt
	
	cp -p $PAR SAUVE # SAUVE du fichier par
	#cp -p $PAR ../parfiles/new/$PAR


	echo "__________GNUPLOT_________"  #Plot DM SAUVE/DMofT$PSRNAME-$TIM.ps
	echo -e 'set term postscript color solid\nset output "DMofT'$PSRNAME'.ps"
set border 15
#set xtics 50
set mxtics 4
#set ytics 0.0005
#set yra [10:45]
set mytics 2
set xlabel "t [MJD]"
set ylabel "DM [pc/cm^3]" offset 2,0
set title "PSR '$PSRNAME' '$TIM'"
set noclip one
set size 1.2,1
set grid xtics ytics
set key outside top Left reverse width -1  box spacing 1.2
f(x)=c+b*(x-56925)
b=20.0
c=1E-6
fit f(x) "dmvals_'$TIM'.dat" using 1:2:3 via b,c
plot \
     "dmvals_'$TIM'.dat" using ($1):2:3 with errorbars lt 1 pt 6 title "DM",\
      f(x) w l title "lin reg"' >> test.gpl
	gnuplot test.gpl
	mv DMofT$PSRNAME.ps SAUVE/DMofT$PSRNAME-$TIM.ps
	#gv SAUVE/DMofT$PSRNAME.ps &

}




function Superpose_DMVAL(){
	#Superpose two DM variation to compare
	echo `ls -lhtr *.dat`
	read -p "Select a 1st .dat file:" dat1
	while [ ! -e $dat1 ]
	do
		read -p "Select a valide 1st .dat file:" dat1
	done
	echo `ls -lhtr *.dat`
	read -p "Select a 2nd .dat file:" dat2
	while [ ! -e $dat & $dat1 == $dat2  ]
	do
		read -p "Select a valide 2nd .dat file:" dat2
	done

	echo "__________GNUPLOT_________"
	echo -e 'set term postscript color solid\nset output "DMofT'$PSRNAME'.ps"
set border 15
#set xtics 50
set mxtics 4
#set ytics 0.0005
set mytics 2
set xlabel "t [MJD]"
set ylabel "DM [pc/cm^3]" offset 2,0
set title "PSR '$PSRNAME'"
set noclip one
set size 1.2,1
set grid xtics ytics
set key outside top Left reverse width -1  box spacing 1.2
plot \
     "'$dat1'" using ($1):2:3 with errorbars lt 1 pt 6 title "'$dat1'",\
     "'$dat2'" using ($1):2:3 with errorbars lt 3 pt 6 title "'$dat2'"' >> test.gpl
	gnuplot test.gpl
	mv DMofT$PSRNAME.ps SAUVE/DMofT$PSRNAME-"$dat1"_"$dat2".ps
	gv SAUVE/DMofT$PSRNAME-"$dat1"_"$dat2".ps &

}



function SPLIT_psrsplit(){
#SPLIT of refold2 files for separate channels
#the desired number of channels must be a multiple of the number of initial channels.

#calcul of the bw
nchan=`psredit -c nchan data/refolded/$backend/* | cut -d "=" -f2 | tail -n 1`
let "chan = $nchan/($nb+1)"

rm -r data/refolded/SPLIT
rm data/refolded/$backend/*_0000.refold2_F8

echo "_____________psrsplit__"$nb"F_with0_________"
if [[ ! -e "data/refolded/SPLIT" ]]
then
	mkdir data/refolded/SPLIT
fi
for l in data/refolded/$backend/*.refold2_F8
do
	#split each refold2_F8
	echo $chan
	#IN data/refolded/$backend/*.refold2_F8 out data/refolded/$backend/*_0000.refold2_F8
	psrsplit -c $chan $l
done
mv data/refolded/$backend/*_0000.refold2_F8 data/refolded/SPLIT/
}

function SPLIT_scrunchTOAs(){
rm -r data/scrunched/SPLIT
echo "_____________scrunch_TOAs__"$nb"F_with0________"
#scrunch each bw on frequency and time
	if [[ ! -e "data/scrunched/SPLIT" ]]
	then
		mkdir data/scrunched/SPLIT
	fi
	#in data/refolded/SPLIT/*refold2_F8 out data/scrunched/SPLIT/*toasscrunched
	python $lucasscripts/scrunch_data.py -datadir data/refolded/SPLIT/ -dataext refold2_F8 -destdir data/scrunched/SPLIT/ -destext toasscrunched -pscrunch -fscrunch -tscrunch -site $site -overwrite -parfile $PAR -dm_from_parfile
} #-pscrunch -fscrunch -tscrunch but non dedisperse to make toa

function SPLIT_scrunchDFTp(){
echo "_____________scrunch_DFTp_templates__"$nb"F_with0________"
#scrunch dedisperse for templates 
	listrefold=(data/scrunched/SPLIT/*toasscrunched)
	if [[ ! -e "$listrefold" ]]
	then
		echo "No .toasscrunched files found: data/scrunched/SPLIT/"
		exit
	fi
	#in data/scrunched/SPLIT/*toasscrunched out data/scrunched/SPLIT/*splitscrunch
	python $lucasscripts/scrunch_data.py -datadir data/scrunched/SPLIT/ -dataext toasscrunched -destdir data/scrunched/SPLIT/ -destext splitscrunch -pscrunch -fscrunch -tscrunch -site $site -overwrite -dedisperse -parfile $PAR -dm_from_parfile	
} #-pscrunch -fscrunch -tscrunch -dedisperse

function SPLIT_MAKE_TEMPL(){
rm *.png
rm OUTPUT*
rm *.prof
#rm TOAs_freq0.tim
echo -e "FORMAT 1" >> TOAs_freq0.tim
for n in `seq 0 $nb` # make template on each bw
do
echo "__________MAKE_TEMPLATES____"$n"/"$nb"_______"
if [[ ${#n} == 1 ]]
then
	n2=0$n #if the number of bw is smaller than 10 --> 09
	elif [[ ${#n} == 2 ]] #if the number of bw is bigger than 9 --> 10

	then
 	n2=$n
fi
	#in data/scrunched/SPLIT/*00"$n2"_0000.splitscrunch out OUTPUT_SMOOTHED_$n OUTPUT_ADDED_$n summed.prof smoothed.prof
	python $lucasscripts/make_templates.py -datadir data/scrunched/SPLIT -dataext 00"$n2"_0000.splitscrunch -sortsnr -overwrite -automax -freq 0 -bw 0 -backend $backend  -obsnchan 0 -scale 0 -maxsum 0 -noclock -output_smoothed OUTPUT_SMOOTHED_$n -smoothedprof smoothed00$n2.prof  -output_added OUTPUT_ADDED_$n

# -forcealign -nprof 0 
mv templates.png templates00"$n2".png #rename template.png
display templates00"$n2".png &
	#delete corrupt files
	read -p "would you want delete a corrupt profile ? y/n:" y
	echo -e \n
while [[ $y = 'y' ]]
	do

	psredit -c int[0]:mjd data/scrunched/SPLIT/*00"$n2"_0000.splitscrunch
	read -p "select the profile .00"$n2"_0000.splitscrunch to be deleted in the list" prof
	rm $prof
	read -p "would you want delete an other corrupt profile ? y:" y
	echo -e \n
	while [[ $y = 'y' ]]
		do
		read -p "select the profile to be deleted" prof
		echo -e \n
		rm $prof
		read -p "would you want delete an other corrupt profile ? y:" y
		echo -e \n
	done
	#remake the template
	#in data/scrunched/SPLIT/*00"$n2"_0000.splitscrunch out OUTPUT_SMOOTHED_$n OUTPUT_ADDED_$n summed.prof smoothed.prof
	python $lucasscripts/make_templates.py -datadir data/scrunched/SPLIT -dataext 00"$n2"_0000.splitscrunch -sortsnr -overwrite -automax -freq 0 -bw 0 -backend $backend  -obsnchan 0 -scale 0 -maxsum 0 -noclock -output_smoothed OUTPUT_SMOOTHED_$n -smoothedprof smoothed00$n2.prof
	mv templates.png templates00"$n2".png
	display templates00"$n2".png &
      	read -p "would you want delete an other corrupt profile ? y/n:" y
	echo -e "\n"
done
done
}




function SPLIT_TOAs(){
rm TOAs_freq0.tim
echo -e "FORMAT 1" >> TOAs_freq0.tim


if [[ ${#nb} == 1 ]]
then
	nb2=0$nb
	elif [[ ${#n} == 2 ]]

	then
 	nb2=$nb
fi

rm SAUVE/phase.txt
for n in `seq $nb -1 0` # `seq $nb -1 0` to compare with the highest template
do
if [[ ${#n} == 1 ]]
then
	n2=0$n
	elif [[ ${#n} == 2 ]]

	then
 	n2=$n
fi
	#phase is the variation in phase with the highest template
	phase[$nb-$n]=`pat -R -s smoothed00$nb2.prof smoothed00$n2.prof | cut -d " " -f4`
	#err it's the error on this phase
	err[$nb-$n]=`pat -R -s smoothed00$nb2.prof smoothed00$n2.prof | cut -d " " -f5`
	echo "${phase[$nb-$n]}	${err[$nb-$n]}	`psredit -c freq data/scrunched/SPLIT/*"$n2"_0000* | cut -d "=" -f2 | awk 'NR>1{v+=$1;count++}END{print v/count}'`" >> SAUVE/phase.txt #SAUVE this phase variation in the SAUVE/phase.txt file
done


for n in `seq 0 $nb` # `seq 0 $nb` to make toas
do

if [[ ${#n} == 1 ]]
then
	n2=0$n
	elif [[ ${#n} == 2 ]]
	then
 	n2=$n
fi

echo "__________MAKE_TOAs_______"$n"/"$nb"_______"
#in data/scrunched/SPLIT/00"$n2"_0000.toasscrunched out smoothed00$n2.prof TOAs_freq_temp.tim
python $lucasscripts/make_toas.py -datadir data/scrunched/SPLIT/ -dataext 00"$n2"_0000.toasscrunched -template smoothed00$n2.prof -overwrite -toafile TOAs_freq_temp.tim

#add the phase jump of the template in the time file
python $DIR/python/jump.py TOAs_freq_temp.tim ${phase[$nb-$n]}

#delete the first line "FORMAT 1" and add in TOAs_freq0.tim
sed -n -e '2,$p' TOAs_freq_temp_padd.tim >> TOAs_freq0.tim

rm TOAs_freq_temp.tim
rm TOAs_freq_temp_padd.tim # clear .tim file

done

tempo2 -gr plk -nspr 1 -nofit -nobs 30000 -f $PAR -setup $setuptempo2 TOAs_freq0.tim
}


function TEMP1_DELETE(){
	#delete corupt templtes in the first pass
	read -p "would you want delete a corrupt profile ? y/n:" -n 1 y
	echo -e "\n"
while [ $y = 'y' ]
do
	psredit -c int[0]:mjd data/scrunched/$backend/*.DFTp
	read -p "select the profile to be deleted" prof
	rm $prof
	read -p "would you want delete an other corrupt profile ? y:" y
	echo -e \n
	while [ $y = 'y' ]
	do
		psredit -c int[0]:mjd data/scrunched/$backend/*.DFTp
		read -p "select the profile .DFTp to be deleted in the list" prof
		rm $prof
     		read -p "would you want delete an other corrupt profile ? y/n:" y
		echo -e \n
	done
	MAKE_TEMPLATES2
      	read -p "would you want delete an other corrupt profile ? y/n:" y
	echo -e \n

done
mv templates.png SAUVE/templates_"$PSRNAME"_1st.png
mv smoothed.prof smoothed_F8.prof
}


function TEMP2_DELETE(){
	#delete corupt templtes in the seconde pass
	read -p "would you want delete a corrupt profile ? y/n:" -n 1 y
	echo -e "\n"
while [ $y = 'y' ]
do
	psredit -c int[0]:mjd data/scrunched/$backend/*.DFTprefold
	read -p "select the profile to be deleted" prof
	rm $prof
	read -p "would you want delete an other corrupt profile ? y:" y
	echo -e \n
	while [ $y = 'y' ]
	do
		psredit -c int[0]:mjd data/scrunched/$backend/*.DFTprefold
		read -p "select the profile .DFTprefold to be deleted in the list" prof
		rm $prof
     		read -p "would you want delete an other corrupt profile ? y/n:" y
		echo -e \n
	done
	MAKE_TEMPLATES2
      	read -p "would you want delete an other corrupt profile ? y/n:" y
	echo -e \n

done
mv templates.png SAUVE/templates_"$PSRNAME"_2nd.png
mv smoothed.prof smoothed_F8refold.prof
}


function PSST(){
#Plot Smoothed Splitted Templates
rm freq_smoothedprof.gpl
rm freq_smoothedprof.ps
nb=`ls OUTPUT_SMOOTHED* |wc -l`
let "nb = $nb-1"
for n in `seq 0 $nb`
do
	if [[ ${#n} == 1 ]]
	then
		n2=0$n
	elif [[ ${#n} == 2 ]]
	then
 		n2=$n
	fi
	#pdv -t -n $n $PSRNAME.combine >prof_$n.txt
	#psrtxt -c $n $PSRNAME.combine >prof_$n.txt
	freq[$n]=`psredit -c freq data/scrunched/SPLIT/*00"$n2"_0000* | cut -d "=" -f2 | awk 'NR>1{v+=$1;count++}END{print v/count}'`
done
echo -e 'set term postscript color solid\nset output "freq_smoothedprof.ps"
#set border 15
#set xtics 50
#set xra [600:800]
#set mxtics 4
#set ytics 0.0005
#set mytics 2
set xlabel "Pulse Phase"
set ylabel "Intensity (a.u.)" offset 2,0
set title "frequency smoothed Profils '$PSRNAME'"
#set noclip one
#set size 1.2,1
#set grid xtics ytics
#set key outside top Left reverse width -1  box spacing 1.2

plot \' >> freq_smoothedprof.gpl

for i in `seq 0 $nb`;
do
let "nbi = $nb-$i"
echo '	"OUTPUT_SMOOTHED_'$nbi'" using 3:($4+'`echo "$nbi*$decal" |bc`') with lines title "'${freq[$nbi]}'MHz",\' >> freq_smoothedprof.gpl
done

sed '$ s/..$//' freq_smoothedprof.gpl > freq_smoothedprof2.gpl
mv freq_smoothedprof2.gpl freq_smoothedprof.gpl
gnuplot freq_smoothedprof.gpl
#rm prof_?.txt
#cp -p SAUVE/"$PSRNAME"_smoothedfreq_prof.ps $DIR/Plot_OUTPUTSMOOTHED/"$PSRNAME"_smoothedfreq_prof.ps

}


function PAddST(){
#Plot Add Splitted Templates
rm freq_smoothedprof.gpl
rm freq_smoothedprof.ps
nb=`ls OUTPUT_ADDED* |wc -l`
let "nb = $nb-1"
for n in `seq 0 $nb`
do
	#pdv -t -n $n $PSRNAME.combine >prof_$n.txt
	#psrtxt -c $n $PSRNAME.combine >prof_$n.txt
	freq[$n]=`psredit -c freq data/scrunched/SPLIT/*000"$n"_0000* | cut -d "=" -f2 | awk 'NR>1{v+=$1;count++}END{print v/count}'`
done
#make a gnuplot script
echo -e 'set term postscript color solid\nset output "freq_smoothedprof.ps"
#set border 15
#set xtics 50
#set mxtics 4
#set ytics 0.0005
#set mytics 2
set xlabel "Pulse Phase"
set ylabel "Intensity (a.u.)" offset 2,0
set title "frequency smoothed Profils '$PSRNAME'"
#set noclip one
#set size 1.2,1
#set grid xtics ytics
#set key outside top Left reverse width -1  box spacing 1.2

plot \' >> freq_smoothedprof.gpl

for i in `seq 0 $nb`;
do
let "nbi = $nb-$i"
echo '	"OUTPUT_ADDED_'$nbi'" using 3:($4+'`echo "$nbi*$decal" |bc`') with lines title "'${freq[$nbi]}'MHz",\' >> freq_smoothedprof.gpl
done

sed '$ s/..$//' freq_smoothedprof.gpl > freq_smoothedprof2.gpl
mv freq_smoothedprof2.gpl freq_smoothedprof.gpl
gnuplot freq_smoothedprof.gpl

#cp -p SAUVE/"$PSRNAME"_smoothedfreq_prof.ps $DIR/Plot_OUTPUTSMOOTHED/"$PSRNAME"_smoothedfreq_prof.ps

}


function PARSELECT(){ #par selection in current directory
ls -lhtr *.par
read -p "Select a .par file:" PAR
while [ ! -e $PAR ]
do
	read -p "Select a valid .par file:" PAR
done
#tempo1 tempo2 transformation
parvers=`less $PAR | grep EPHVER | grep -o '[0-9]'`
if [[ $parvers == '2' ]]
then
	echo "parfile version is update for tempo2"
	tempo2 -gr transform $PAR $PAR
fi
}

function TIMSELECT(){ #tim selection in current directory
ls -lhtr *.tim
read -p "Select a .tim file:" TIM
while [ ! -e $TIM ]
do
	read -p "Select a valid .tim file:" TIM
done
}


function SPLIT(){
	echo "Select a process:"
	options=("All_split_processing" "start_on_scrunchTOAs" "start_on_scrunchDFTp" "Only_split_scrunchtoa_scrunchDFTp" "start_on_Templates_and_TOAs" "start_on_TOAs" "Return" )
	select opt in "${options[@]}"
	do
		case $opt in
			'All_split_processing') 
			PARSELECT
			read -p "how many split would you like ? :" nb
			#nb-1 avec zero
			let "nb = $nb-1"
			SPLIT_psrsplit
			SPLIT_scrunchTOAs
			SPLIT_scrunchDFTp
			SPLIT_MAKE_TEMPL
			SPLIT_TOAs
				;;
			'start_on_scrunchTOAs') 
			PARSELECT
			read -p "how many split ? :" nb
			#nb-1 avec zero
			let "nb = $nb-1"
			SPLIT_scrunchTOAs
			SPLIT_scrunchDFTp
			SPLIT_MAKE_TEMPL
			SPLIT_TOAs
				;;
			'start_on_scrunchDFTp') 
			PARSELECT
			read -p "how many split ? :" nb
			#nb-1 avec zero
			let "nb = $nb-1"
			SPLIT_scrunchDFTp
			SPLIT_MAKE_TEMPL
			SPLIT_TOAs
				;;
			'Only_split_scrunchtoa_scrunchDFTp') 
			PARSELECT
			read -p "how many split ? :" nb
			#nb-1 avec zero
			let "nb = $nb-1"
			SPLIT_psrsplit
			SPLIT_scrunchTOAs
			SPLIT_scrunchDFTp
				;;
			'start_on_Templates_and_TOAs') 
			PARSELECT
			read -p "how many split ? :" nb
			#nb-1 avec zero
			let "nb = $nb-1"
			SPLIT_MAKE_TEMPL
			SPLIT_TOAs
				;;
			'start_on_TOAs') 
			PARSELECT
			read -p "how many split ? :" nb
			#nb-1 avec zero
			let "nb = $nb-1"
			SPLIT_TOAs
				;;

			'Return')
			displayMainMenu
				;;
			*)
		 		echo "Invalid option, enter a number"
		 		;;
		esac
	done
}

function PLOTs(){
	echo "Select a step to start:"
	echo ""
	options=("plot_smoothed_split_templates" "plot_smoothed_split_templates_superpose" "plot_Add_split_templates" "plot_Add_split_templates_superpose" "tempo2" "plot_DMvar" "subplot_DMvar" "Return" )
	select opt in "${options[@]}"
	do
		case $opt in
			'plot_smoothed_split_templates') 
			decal=0.05
			PSST
			mv freq_smoothedprof.ps SAUVE/"$PSRNAME"_smoothedfreq_prof.ps
			gv SAUVE/"$PSRNAME"_smoothedfreq_prof.ps &
				;;
			'plot_smoothed_split_templates_superpose') 
			decal=0
			PSST
			mv freq_smoothedprof.ps SAUVE/"$PSRNAME"_smoothedfreq_superpose.ps
			gv SAUVE/"$PSRNAME"_smoothedfreq_superpose.ps &
				;;
			'plot_Add_split_templates') 
			decal=0.05
			PAddST
			mv freq_smoothedprof.ps SAUVE/"$PSRNAME"_Addfreq_prof.ps
			gv SAUVE/"$PSRNAME"_Addfreq_prof.ps &
				;;
			'plot_Add_split_templates_superpose') 
			decal=0
			PAddST
			mv freq_smoothedprof.ps SAUVE/"$PSRNAME"_Addfreq_superpose.ps
			gv SAUVE/"$PSRNAME"_Addfreq_superpose.ps &
				;;
			'tempo2') 
			PARSELECT
			TIMSELECT
			TEMPO2_2
				;;
			'plot_DMvar') 
			PARSELECT
			TIMSELECT
			DMVAL
				;;
			'subplot_DMvar') 
			Superpose_DMVAL
				;;
			'Return')
			displayMainMenu
				;;
			*)
		 		echo "Invalid option, enter a number"
		 		;;
		esac
	done
}
function displayMainMenu(){
	echo "Select an option:"
	echo ""
	options=("SPLIT & step" "Plots" "Quit")
	select opt in "${options[@]}"
	do
		case $opt in
			'SPLIT & step')
			SPLIT
				;;
			'Plots') 
			PLOTs
				;;
			'Quit')
				exit;;
			*)
		 		echo "Invalid option, enter a number"
		 		;;
		esac
	done
}

echo "---------------------------------------------"
displayMainMenu
