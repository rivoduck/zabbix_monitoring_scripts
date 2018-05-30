#!/bin/bash

# use this script to update the installation after new code is pulled

ZABBIX_BASE_CONFDIR="/etc/zabbix/"
ZABBIX_AGENT_CONF_D_1="zabbix_agentd.conf.d/"
ZABBIX_AGENT_CONF_D_2="zabbix_agentd.d/"
BUILD_BASE="/opt/zabbix_monitoring_scripts/"
LOCAL_ZABBIX_AGENT_CONF_D="zabbix_agentd.conf.d/"

NEWLINE=$'\n'

# import functions
. ./bin/functions.sh

errors=""

vm_found=0
disk_found=0

echo

# check directories and files 
printf "%-80s" "checking zabbix conf dir"
if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_1} ]
then
	if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_2} ]
	then
	    errors="Cannot find Zabbix conf dir [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_1}] or [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_2}]${NEWLINE}"
	    echo "[fail]"
	else
		ZABBIX_AGENT_CONF_D=${ZABBIX_AGENT_CONF_D_2}
		echo "[OK]"
	fi
else
	ZABBIX_AGENT_CONF_D=${ZABBIX_AGENT_CONF_D_1}
    echo "[OK]"
fi

printf "%-80s" "checking distribution dir"
if [ ! -d ${BUILD_BASE} ]
then
    errors="${errors}Cannot find distribution, make sure files are installed in ${BUILD_BASE}${NEWLINE}"
    echo "[fail]"
    # error_exit "Cannot find distribution, make sure files are installed in ${BUILD_BASE}" 
else
    echo "[OK]"
fi

vm_detect -v
vm_found=$?

disk_detect -v
disk_found=$?


echo 
if [ "$vm_found" -eq 2 ]
then
    # Xen checks
    vm_found=$res
    printf "%-80s" "checking PHP"
    which php > /dev/null
    if [ $? -ne 0 ]
    then
        errors="${errors}Cannot find PHP executable, please install php-cli"
        echo "[fail]"
    else
        echo "[OK]"
    fi
fi

if [[ "$vm_found" -eq 1 || "$disk_found" -eq 1 ]]
then
    # XenServer or Mega Raid checks
    vm_found=$res
    printf "%-80s" "checking Python"
    which python > /dev/null
    if [ $? -ne 0 ]
    then
        errors="${errors}Cannot find Python executable, please install python"
        echo "[fail]"
    else
		python -c 'import json' > /dev/null 2>&1
        if [ $? -ne 0 ]
        then
            errors="${errors}Python json module not available"
            echo "[fail]"
        else
            echo "[OK]"
        fi
    fi
fi



if [ "X${errors}" == "X" ]
then
    # install files
    install_file topix_general.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${LOCAL_ZABBIX_AGENT_CONF_D}
	if [ "$vm_found" -ne 0 ]
	then
        install_file topix_vms.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${LOCAL_ZABBIX_AGENT_CONF_D}
	fi
	if [ "$disk_found" -ne 0 ]
	then
        install_file topix_disks.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${LOCAL_ZABBIX_AGENT_CONF_D}
	fi
else
    # errors occourred
    error_exit "${errors}"
fi
echo

