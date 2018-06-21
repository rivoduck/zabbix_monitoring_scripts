#!/bin/bash

current_dir=$(dirname "$0")
disk_name=$1
command=$2

. ${current_dir}/../functions.sh


disk_detect
res=$?
if [ $res -eq 0 ]
then
    # error
    exit -1
else
    if [ $res -eq 1 ]
    then
        # storCLI
        python ${current_dir}/MEGA/parse_disk_array_storcli.py "$disk_name" $command
    fi
fi
