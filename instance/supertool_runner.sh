#
# This is run in the upload folder, i.e. uploads/<user>/<batchid>
#
unset PYTHONPATH
LANGUAGE="$1"             # language, en, fi etc
INPUTFILE="$2"            # input file, e.g. family.gramps
SCRIPTFILE="$3"           # SuperTool script file to run, full path, e.g. app/scripts/example.script
OUTPUTFILE="$4"           # output csv file, e.g. output.csv
BASEDIR="$5"
#rm -rf ~/"$INPUTFILE.media"
rm -f "$OUTPUTFILE"
cmd=LANGUAGE="$LANGUAGE" /usr/bin/gramps -q -i "$INPUTFILE" -a tool -p name=SuperTool,script=$SCRIPTFILE,output=$OUTPUTFILE,args=$BASEDIR
