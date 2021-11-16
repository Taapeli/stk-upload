unset PYTHONPATH
rm -rf ~/"$2.media"
rm -f "$4"
echo LANGUAGE="$1" /usr/bin/gramps -i "$3" -a tool -p name=isotammi-verify
LANGUAGE="$1" /usr/bin/gramps -q -i "$3" -a tool -p name=isotammi-verify -e "$4"
