#!/bin/bash

# use this script to update the installation after new code is pulled

ZABBIX_BASE_CONFDIR="/etc/zabbix/"
ZABBIX_AGENT_CONF_D_1="zabbix_agentd.conf.d/"
ZABBIX_AGENT_CONF_D_2="zabbix_agentd.d/"
ZABBIX_AGENT_CONF_D_3="zabbix_agent2.d/"
BUILD_BASE="/opt/zabbix_monitoring_scripts/"

# path of conf files inside the "built" distribution
LOCAL_ZABBIX_AGENT_CONF_D="zabbix_agentd.conf.d/"

ZABBIX_AGENT2_CONF_PLUGIN_D="${ZABBIX_AGENT_CONF_D_3}plugins.d/"

NEWLINE=$'\n'

# import functions
. ./bin/functions.sh

errors=""

vm_found=0
disk_found=0

echo

zabbix_agent_version=1
# check directories and files
# imposta la variabile ZABBIX_AGENT_CONF_D alla cartella effettivamente trovata
printf "%-80s" "checking zabbix conf dir"
if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_3} ]
then
	if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_2} ]
	then
        if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_1} ]
        then
    	    errors="Cannot find Zabbix conf dir [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_1}] or ${NEWLINE} [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_2}] or ${NEWLINE}
[${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D_3}]${NEWLINE}"

    	    echo "[fail]"
        else
            ZABBIX_AGENT_CONF_D=${ZABBIX_AGENT_CONF_D_1}
            echo "[OK]"
        fi
	else
		ZABBIX_AGENT_CONF_D=${ZABBIX_AGENT_CONF_D_2}
		echo "[OK]"
	fi
else
	ZABBIX_AGENT_CONF_D=${ZABBIX_AGENT_CONF_D_3}
    echo "[OK (agent2)]"
    zabbix_agent_version=2
    
    # Check directory plugin
    if [ -d "${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT2_CONF_PLUGIN_D}" ]; then
        echo "Directory exists: $ZABBIX_AGENT2_CONF_PLUGIN_D"
    else
        echo "Creating dir ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT2_CONF_PLUGIN_D}"
        mkdir "${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT2_CONF_PLUGIN_D}"
    fi
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

docker_detect -v
docker_found=$?

echo 
if [ "${vm_found:-0}" -eq 2 ]
then
    # Xen checks
    printf "%-80s" "checking PHP"
    which php > /dev/null 2>&1
    if [ $? -ne 0 ]
    then
        errors="${errors}Cannot find PHP executable, please install php-cli"
        echo "[fail]"
    else
        echo "[OK]"
    fi
fi

if [[ "${vm_found:-0}" -eq 1 || "${disk_found:-0}" -eq 1 || "${disk_found:-0}" -eq 2 || "${docker_found:-0}" -eq 1 || "${docker_found:-0}" -eq 2 ]]
then
    # XenServer or Mega Raid checks
    printf "%-80s" "checking Python"
    which python > /dev/null 2>&1
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
	
    if [ "${vm_found:-0}" -ne 0 ]
	then
        install_file topix_vms.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${LOCAL_ZABBIX_AGENT_CONF_D}
	fi
	
    if [ "${disk_found:-0}" -ne 0 ]
	then
        install_file topix_disks.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${LOCAL_ZABBIX_AGENT_CONF_D}
	fi
	
    if [ "${docker_found:-0}" -ne 0 ]
	then
        if [ $zabbix_agent_version -eq 2 ]
        then
            install_file topix_docker_compose.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT2_CONF_PLUGIN_D} ${BUILD_BASE}${ZABBIX_AGENT2_CONF_PLUGIN_D}
        fi
    fi
else
    # errors occourred
    error_exit "${errors}"
fi
echo


