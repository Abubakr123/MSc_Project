# Data reduction

# Check the no of channel for the everage time obs
# if nchn =350, in the main and reproccessed data of nancep
# then rename the file to be T.F350
psrstat -c nchan,nsubint *.T

for f in *.T; do mv "$f" "${f/T/T.F350}";done

python2.7 ~/MSc_Project/paper_work/zap_channels.py J0629+2415_*.T --outdir /data1/abubakr/J0629+2415_tcom/J0629+2415/
