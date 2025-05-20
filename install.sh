#!/bin/bash

# use this script to update the installation after new code is pulled

ZABBIX_BASE_CONFDIR="/etc/zabbix/"
ZABBIX_AGENT_CONF_D_1="zabbix_agentd.conf.d/"
ZABBIX_AGENT_CONF_D_2="zabbix_agentd.d/"
BUILD_BASE="/opt/zabbix_monitoring_scripts/"
LOCAL_ZABBIX_AGENT_CONF_D="zabbix_agentd.conf.d/"

ZABBIX_AGENT2_CONF_PATH="/usr/local/etc/zabbix_agent2.conf"
ZABBIX_AGENT2_CONF_PLUGIN_D="zabbix_agent2.d/plugins.d"
SOURCE_PLUGIN_FILE="zabbix_agent2.d/plugins.d/topix_docker_compose.conf"

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

if [[ "${vm_found:-0}" -eq 1 || "${disk_found:-0}" -eq 1 || "${disk_found:-0}" -eq 2 ]]
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
else
    # errors occourred
    error_exit "${errors}"
fi
echo

errors=""

# Check Docker
if command -v docker &> /dev/null; then
    echo "Docker installed."
else
        errors="${errors}Docker is not installed"
        echo "[fail]"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose standalone installed."
elif docker compose version &> /dev/null; then
    echo "Docker Compose (plugin) installed."
else
        errors="${errors}Docker is not installed"
        echo "[fail]"
fi

# Check zabbix_agent2.conf
if [ -f "$ZABBIX_AGENT2_CONF_PATH" ]; then
    echo "File $ZABBIX_AGENT2_CONF_PATH exists."
else
    errors="${errors}File $ZABBIX_AGENT2_CONF_PATH doesn't exist."
fi

# Check directory plugin
if [ -d "${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT2_CONF_PLUGIN_D}" ]; then
    echo "Directory exists: $ZABBIX_AGENT2_CONF_PLUGIN_D"
else
    errors="${errors}Directory $ZABBIX_AGENT2_CONF_PLUGIN_D doesn't exits."
fi

if [ "X${errors}" == "X" ]
then
  install_file $SOURCE_PLUGIN_FILE ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT2_CONF_PLUGIN_D} ${BUILD_BASE}${ZABBIX_AGENT2_CONF_PLUGIN_D}
else
  error_exit "${errors}"
fi



echo

