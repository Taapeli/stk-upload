unset PYTHONPATH
PYTHON=""
GRAMPS=/usr/bin/gramps

export PYTHONPATH=.
export GRAMPS_RESOURCES=resources

# gramps_run(gramps_runner, "isotammi-idt", lang, current_user.username, batch_id, batch.xmlname, newfile)
#    {gramps_runner} '{tool}' '{lang}' '{xmlfile}' '{pathname}' '{export_file}'

TOOL=$1
LANGUAGE="$2"
XMLNAME="$3"
INPUTFILE="$4"
EXPORTFILE="$5"

export LANGUAGE

rm -rf ~/"$XMLNAME.media"
rm -f "$EXPORTFILE"

CMD="$GRAMPS -q -i '$INPUTFILE' -a tool -p name=$TOOL -e '$EXPORTFILE'"
echo CMD="$CMD"
sh <<EOF
$CMD
EOF

#echo LANGUAGE="$1" /usr/bin/gramps -i "$3" -a tool -p name=isotammi-verify
#LANGUAGE="$1" /usr/bin/gramps -q -i "$3" -a tool -p name=isotammi-verify -e "$4"
