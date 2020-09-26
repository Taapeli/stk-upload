unset PYTHONPATH
rm -rf ~/"$1.media"
/usr/bin/gramps -i "$2" -a tool -p name=verify
