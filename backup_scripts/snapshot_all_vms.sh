#!/bin/bash


DATE=`date +%Y-%m-%d-%H:%M`
VMUUIDS=''
VMUUIDS=$(xe vm-list is-control-domain=false is-a-snapshot=false | grep uuid | cut -d":" -f2| sed 's/^ *//g')
for VMUUID in $VMUUIDS

	do
	    	VMNAME=`xe vm-list uuid=$VMUUID | grep name-label | cut -d":" -f2 | sed 's/^ *//g'`
		xe vm-snapshot uuid=$VMUUID new-name-label="SNAPSHOT-$VMNAME-$DATE"

		count=0
		SNAPUUIDS=$(xe snapshot-list | awk '{if ( $0 ~ /uuid/) {uuid=$5} if ($0 ~ /name-label/) {$1=$2=$3="";vmname=$0; printf "%s - %s\n", vmname, uuid}}' |grep $VMNAME | sort -r |awk '{print $3}')
		for SNAPUUID in $SNAPUUIDS
			do
				if [ $count -gt 1 ]
					then
					xe snapshot-uninstall uuid=$SNAPUUID force=true
					echo "yes"
					echo -ne '\n'
				fi
			((count++))
		done
done
