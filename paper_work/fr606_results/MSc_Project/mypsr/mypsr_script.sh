#!/bin/bash
VERSION=1.0.1
DATUM=13.09.2015
CODENAME=mypsr_script.sh


#Definition of the principal directory, location of the parfiles directory.
#But the code can work without the parfiles directory.

DIR=/data/guestnode3
lucasscripts=/home/artemis/lucasscripts # Directory for lucas scripts
setuptempo2=/data/guestnode3/script/plk_setup_fr606_embrace.dat # setup file for tempo2

PSRNAME=`basename $PWD`
backend=`ls data/links/` #nom du dossier backend
fscrunch=8
tscrunch=10

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
			echo "file created: $PSRNAME.par"
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





function REFOLD1(){
	#on recherche si les .ar existent
	listar=($PWD/data/links/$backend/*.ar)
	if [[ ! -e "$listar" ]]
	then
		echo "No .ar files found: $PWD/data/links/$backend/"
		exit
	fi

	#refold in data/links/$backend/*.ar out data/refolded/$backend/*.refold
	echo "__________REFOLD__________"
	python $lucasscripts/refold_data.py -datadir data/links/$backend/ -dataext ar -destdir data/refolded/$backend/ -parfile $PAR -site $site -overwrite
}



function SCRUNCH_1(){
	echo "__________SCRUNCH_NSUB10_________"
	listrefold=($PWD/data/refolded/$backend/*.refold)
	if [[ ! -e "$listrefold" ]]
	then
		echo "No .refold files found: $PWD/data/refolded/$backend/"
		exit
	fi
	#scrunch_t10    in data/refolded/$backend/*.refold out data/scrunched/$backend/*.scrunchedF8_tsub10
	#le t10 permet de fiter F0 sur une observation uniquement
	#-fscrunch 8 pour fit le DM
	python $lucasscripts/scrunch_data.py -datadir data/refolded/$backend/ -dataext refold -destdir data/scrunched/$backend/ -destext scrunchedF8_tsub10 -pscrunch -fscrunch_nchan $fscrunch -tscrunch_nsub $tscrunch -site $site -overwrite
}



function SCRUNCH_DFTP1(){
	echo "__________SCRUNCH_DFTP_________"
	listrefold=($PWD/data/refolded/$backend/*.refold)
	if [[ ! -e "$listrefold" ]]
	then
		echo "No .refold files found: $PWD/data/refolded/$backend/"
		exit
	fi
	#scrunch_DFTp   in data/scrunched/$backend/*.scrunchedF8_tsub10 out data/scrunched/$backend/*.DFTp
	#ecrase sur t,f,p pour en créer un template
	python $lucasscripts/scrunch_data.py -datadir data/scrunched/$backend/ -dataext scrunchedF8_tsub10 -destdir data/scrunched/$backend/ -destext DFTp -fscrunch -tscrunch -pscrunch -site $site -overwrite -dedisperse
}



function MAKE_TEMPLATES1(){
	echo "__________MAKE_TEMPLATES_________"
	listDFTp=($PWD/data/scrunched/$backend/*.DFTp)
	if [[ ! -e "$listDFTp" ]]
	then
		echo "No .DFTp files found: $PWD/data/scrunched/$backend/"
		exit
	fi

	#make template in data/scrunched/$backend/*DFTp out ./templates.png et ./smoothed.prof
	python $lucasscripts/make_templates.py -datadir data/scrunched/$backend/ -dataext DFTp -sortsnr -overwrite -automax -forcealign -freq 0 -bw 0 -backend $backend -obsnchan 0 -scale 0 -maxsum 0 -noclock

	

	display templates.png &
}



function MAKE_TOAS1(){
	echo "__________MAKE_TOAS_________"
	listretsub10=($PWD/data/scrunched/$backend/*.scrunchedF8_tsub10)
	if [[ ! -e "$listretsub10" ]]
	then
		echo "No .scrunchedF8_tsub10 files found: $PWD/data/scrunched/$backend/"
		exit
	fi
	#make_toas in data/scrunched/$backend/*.scrunchedF8_tsub10  and ./smoothed_F8.prof out TOAs_base_F8.tim
	python $lucasscripts/make_toas.py -datadir data/scrunched/$backend/ -dataext scrunchedF8_tsub10 -plotres -template smoothed_F8.prof -overwrite -toafile TOAs_base_F8.tim

	#last tim file
	TIM=`ls -got | grep \.tim | head -1| awk '{print $7}'`
	echo 'the last .tim file is: '$TIM

	#calcul la mediane et la moyenne dans le tim
	if [[ -e $DIR/python/median.py ]] 
	then
		#creer un fichier pour mettre les valeurs
		>> SAUVE/results.txt
		echo -e "reluts_err_TOAs_micosec_1st"\n >> SAUVE/results.txt
		echo `python $DIR/python/median.py $TIM` >> SAUVE/results.txt
	else
		echo "python script not found: $DIR/python/median.py"
	fi
}




function TEMPO2_1(){
	#tempo2 in .tim and .par out .par
	echo "__________TEMPO2_________"
	tempo2 -gr plk -nspr 1 -nofit -nobs 30000 -f $PAR -setup $setuptempo2 $TIM
	PAR=`ls -got | grep \.par | head -1| awk '{print $7}'`
	#nouvelle iteration si c'est pas bon
	read -p "would you restart tempo2 with the new .par file $PAR y/n:" -n 1 y
	echo -e "\n"
	while [ $y != 'n' ]
	do
	if [ $y = 'y' ]
	then

	echo "__________TEMPO2_________"
	tempo2 -gr plk -nspr 1 -nofit -nobs 30000 -f $PAR -setup $setuptempo2 $TIM
	PAR=`ls -got | grep \.par | head -1| awk '{print $7}'` #nouveau .par
      	  read -p "would you start tempo2 with the new parfile $PAR y/n:" -n 1 y
		echo -e "\n"
	else
      	  read -p "would you start tempo2 with the new parfile $PAR. Careful answer by y or n:" -n 1 y
		echo -e "\n"
	fi
	done
	#recupération des derniers .par et .tim
	PAR=`ls -got | grep \.par | head -1| awk '{print $7}'`
	echo 'the last .par file is: '$PAR
	cp -p $PAR SAUVE
	TIM=`ls -got | grep \.tim | head -1| awk '{print $7}'`
	echo 'the last .tim file is: '$TIM
}



function REFOLD2(){
	echo "__________REFOLD_2nd_________"
	listar=($PWD/data/links/$backend/*.ar)
	if [[ ! -e "$listar" ]]
	then
		#in $PWD/data/links/$backend/*.ar out data/refolded/$backend/*.refold2_F8
		echo "No .ar files found: $PWD/data/links/$backend/"
		exit
	fi
	python $lucasscripts/refold_data.py -datadir data/links/$backend/ -dataext ar -destdir data/refolded/$backend/ -destext refold2_F8 -parfile $PAR -site $site -overwrite -dm_from_parfile
}



function SCRUNCH2(){
	echo "__________SCRUNCH_2nd_________"
	listrefold=($PWD/data/refolded/$backend/*.refold2_F8)
	if [[ ! -e "$listrefold" ]]
	then
		#in $PWD/data/refolded/$backend/*.refold2_F8 out data/scrunched/$backend/*scrunchedF8refold
		echo "No .refold2_F8 files found: $PWD/data/refolded/$backend/"
		exit
	fi
	python $lucasscripts/scrunch_data.py -datadir data/refolded/$backend/ -dataext refold2_F8 -destdir data/scrunched/$backend/ -destext scrunchedF8refold -pscrunch -fscrunch_nchan $fscrunch -tscrunch -site $site -overwrite -parfile $PAR
# -pscrunch -fscrunch_nchan 8 -tscrunch  -site FR606
}



function SCRUNCH_DFTP2(){
	echo "__________SCRUNCH_DFTp_2nd_________"
	listrefold=($PWD/data/refolded/$backend/*.refold2_F8)
	if [[ ! -e "$listrefold" ]]
	then
		echo "No .refold2_F8 files found: $PWD/data/refolded/$backend/"
		exit
	fi
	#in  data/refolded/$backend/*refold2_F8 out data/scrunched/$backend/*DFTprefold
	python $lucasscripts/scrunch_data.py -datadir data/scrunched/$backend/ -dataext scrunchedF8refold -destdir data/scrunched/$backend/ -destext DFTprefold -dedisperse -fscrunch -tscrunch -pscrunch -site $site -overwrite
#-fscrunch -tscrunch -pscrunch  -site FR606
}



function MAKE_TEMPLATES2(){
	echo "__________MAKE_TEMPLATES_2nd_________"
	listDFTprefold=($PWD/data/scrunched/$backend/*.DFTprefold)
	if [[ ! -e "$listDFTprefold" ]]
	then
		echo "No .DFTprefold files found: $PWD/data/scrunched/$backend/"
		exit
	fi
	#in data/scrunched/$backend/*DFTprefold out template.png, summed.prof, smoothed.prof
	python $lucasscripts/make_templates.py -datadir data/scrunched/$backend/ -dataext DFTprefold -sortsnr -overwrite -automax -freq 0 -bw 0 -backend $backend -obsnchan 0 -scale 0 -maxsum 0 -noclock

	display templates.png &
	
}



function MAKE_TOAS2(){
	echo "__________MAKE_TOAS_2nd_________"


	listscrunchedF8refold=($PWD/data/scrunched/$backend/*.scrunchedF8refold)
	if [[ ! -e "$listscrunchedF8refold" ]]
	then
		echo "No .scrunchedF8refold files found: $PWD/data/scrunched/$backend/"
		exit
	fi

	#in data/scrunched/$backend/*scrunchedF8refold out TOAs_F8refold.tim
	python $lucasscripts/make_toas.py -datadir data/scrunched/$backend/ -dataext scrunchedF8refold -plotres -template smoothed_F8refold.prof -overwrite -toafile TOAs_F8refold.tim

	TIM=`ls -got | grep \.tim | head -1| awk '{print $7}'`
	echo 'the last .tim file is: '$TIM

	echo -e "reluts_err_TOAs_micosec_2nd"\n >> SAUVE/results.txt
	echo `python $DIR/python/median.py $TIM` >> SAUVE/results.txt #SAUVE median
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
	#calcul DM variation
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


function plotDMVAL(){
#plot DM variation
rm test.gpl
echo `ls -lhtr *.dat`
read -p "Select a .dat file:" dat
while [ ! -e $dat ]
do
read -p "Select a valide .dat file:" dat
done

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
set title "PSR '$PSRNAME' '$dat'"
set noclip one
set size 1.2,1
set grid xtics ytics
set key outside top Left reverse width -1  box spacing 1.2
f(x)=c+b*(x-56925)
b=20.0
c=1E-6
fit f(x) "$dat" using 1:2:3 via b,c
plot \
"$dat" using ($1):2:3 with errorbars lt 1 pt 6 title "DM",\
f(x) w l title "lin reg"' >> test.gpl
gnuplot test.gpl
mv DMofT$PSRNAME.ps SAUVE/DMofT$PSRNAME-$dat.ps
gv SAUVE/DMofT$PSRNAME-$dat.ps &

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


function STEP(){
	echo "Select a step to start:"
	echo ""
	options=("REFOLD1" "SCRUNCH1" "MAKE_TEMPLATES1" "TOA1" "TEMPO2_1" "REFOLD2" "SCRUNCH2" "SCRUNCH_DFTP2" "MAKE_TEMPLATES2" "TEMPO2_2" "DMVAL" "Return" )
	select opt in "${options[@]}"
	do
		case $opt in
			'REFOLD1') 
			REFOLD1
			SCRUNCH_1
			SCRUNCH_DFTP1
			MAKE_TEMPLATES1
			TEMP1_DELETE
			MAKE_TOAS1
			TEMPO2_1
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'SCRUNCH1') 
			SCRUNCH_1
			SCRUNCH_DFTP1
			MAKE_TEMPLATES1
			TEMP1_DELETE
			MAKE_TOAS1
			TEMPO2_1
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'MAKE_TEMPLATES1')
			PARSELECT
			MAKE_TEMPLATES1
			TEMP1_DELETE
			MAKE_TOAS1
			TEMPO2_1
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'TOA1')
			MAKE_TOAS1
			TEMPO2_1
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'TEMPO2_1')
			PARSELECT
			TIMSELECT
			TEMPO2_1
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'REFOLD2')
			PARSELECT
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'SCRUNCH2')
			PARSELECT
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'SCRUNCH_DFTP2')
			PARSELECT
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'MAKE_TEMPLATES2')
			PARSELECT
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
				;;
			'TEMPO2_2')
			PARSELECT
			TIMSELECT
			TEMPO2_2
			DMVAL
				;;
			'DMVAL')
			PARSELECT
			TIMSELECT
			DMVAL
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

function ONE_STEP(){
	echo "Select a step to start:"
	echo ""
	options=("REFOLD1" "MAKE_TEMPLATES1" "TEMPO2_1" "REFOLD2" "MAKE_TEMPLATES2" "TEMPO2_2" "DMVAL" "Return" )
	select opt in "${options[@]}"
	do
		case $opt in
			'REFOLD1') 
			PARSELECT
			REFOLD1
				;;
			'MAKE_TEMPLATES1')
			PARSELECT
			TIMSELECT
			MAKE_TEMPLATES1
			TEMP1_DELETE
				;;
			'TEMPO2_1')
			PARSELECT
			TIMSELECT
			TEMPO2_1
				;;
			'REFOLD2')
			PARSELECT
			REFOLD2
				;;
			'MAKE_TEMPLATES2')
			PARSELECT
			MAKE_TEMPLATES2
			TEMP2_DELETE
				;;
			'TEMPO2_2')
			PARSELECT
			TIMSELECT
			TEMPO2_2
				;;
			'DMVAL')
			PARSELECT
			TIMSELECT
			DMVAL
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
	options=("plot_DMvar" "subplot_DMvar" "Return" )
	select opt in "${options[@]}"
	do
		case $opt in
			'plot_DMvar')
			plotDMVAL
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
	options=("All the processing" "Start with a particular step" "Only one step" "Plots" "Quit")
	select opt in "${options[@]}"
	do
		case $opt in
			'All the processing') 
			FIRSTPARFILE
			REFOLD1
			SCRUNCH_1
			SCRUNCH_DFTP1
			MAKE_TEMPLATES1
			TEMP1_DELETE
			MAKE_TOAS1
			TEMPO2_1
			REFOLD2
			SCRUNCH2
			SCRUNCH_DFTP2
			MAKE_TEMPLATES2
			TEMP2_DELETE
			MAKE_TOAS2
			TEMPO2_2
			DMVAL
			displayMainMenu
				;;
			'Start with a particular step')
			STEP
				;;
			'Only one step') 
			ONE_STEP
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
