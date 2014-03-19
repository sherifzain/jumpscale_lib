#!/bin/sh
. /etc/profile

DATE=`date`

while getopts "d:" OPTION
do
    case $OPTION in 
        "d")
            DEVICENAME=$OPTARG
            ;;
        ?)
            echo "Wrong arguments passed. Cannot continue."
            exit 1
    esac
done

log_file=/opt/qbase5/var/log/usb.log

LABEL="CLOUDDISK_"`basename $DEVICENAME`
#Call removeUSBDevice command from jshell!
echo "Remove USB: $DATE - q.cmdtools.disktools.usb._remove('$LABEL')" >> $log_file

/opt/qbase5/jshell -c "q.cmdtools.disktools.usb._remove('$LABEL')" >> $log_file 2>&1
