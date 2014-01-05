#!/bin/bash
. /etc/profile

DATE=$(date)

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

command=( $(udevadm info -q all --name $DEVICENAME) ) 

for i in $(seq 0 ${#command[@]})
do
    word=${command[$i]}
    echo $word | grep -q "="
    if [ $? -ne 0 ] 
    then 
        unset command[$i]
    else
        declare ${command[$i]}
    fi
done

 
MODEL=$ID_MODEL
SERIAL=$ID_SERIAL_SHORT
DEVBASENAME=$(basename $DEVICENAME)
LABEL="CLOUDDISK_"${DEVBASENAME}
VENDOR=$ID_VENDOR

extra=( $(udevadm info -q all --name $DEVICENAME --attribute-walk | awk -F "==" '/speed|size/{gsub("\"","",$2);if($0 ~ /size/){size=$2/2}else{speed=$2}}END{print size;print speed}') ) 
SIZE=${extra[0]}
SPEED=${extra[1]}

#Call newUSBDevice command from jshell!
log_file=/opt/qbase5/var/log/usb.log

if [ ! -f $log_file ] 
then 
     touch $log_file
fi

echo "Add USB: $DATE - q.cmdtools.disktools.usb._add('$MODEL', '$SERIAL', '$DEVICENAME', '$LABEL', '$SIZE', '$SPEED', '$VENDOR')" >> $log_file 

/opt/qbase5/jshell -c "q.cmdtools.disktools.usb._add(model='$MODEL', serial='$SERIAL', devicename='$DEVICENAME', label='$LABEL', size='$SIZE', speed='$SPEED', vendor='$VENDOR')" >> $log_file 2>&1

if [ -f $log_file ] 
then
    size=(`du -m $log_file`)
    size=${size[0]}
    if [ $size -gt 10 ]
    then 
        rm $log_file
        echo "Removed log file since this was more than 10 MB in size"
    fi
fi