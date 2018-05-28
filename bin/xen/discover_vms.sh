#!/bin/bash

current_dir=$(dirname "$0")
vm_name=$1

. ${current_dir}/../functions.sh


xen_detect
res=$?
if [ $res -eq 0 ]
then
    # error
    exit -1
else
    if [ $res -eq 1 ]
    then
        # XenServer
        ${current_dir}/discover_xenserver_vms.sh $vm_name
    else
        # Xen
        ${current_dir}/discover_xen_vms.sh $vm_name
    fi
fi
