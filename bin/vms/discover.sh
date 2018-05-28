#!/bin/bash

current_dir=$(dirname "$0")
vm_name=$1

. ${current_dir}/../functions.sh


vm_detect
res=$?
if [ $res -eq 0 ]
then
    # error
    exit -1
else
    if [ $res -eq 1 ]
    then
        # XenServer
        python ${current_dir}/parse_vm_list_xenserver.py $vm_name
    else
        # Xen
        php ${current_dir}/parse_vm_list_xen.php $vm_name
    fi
fi
