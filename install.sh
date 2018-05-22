#!/bin/bash

# use this script to update the installation after new code is pulled

ZABBIX_BASE_CONFDIR="/etc/zabbix/"
ZABBIX_AGENT_CONF_D="zabbix_agentd.conf.d/"
BUILD_BASE="/opt/zabbix_monitoring_scripts/"

NEWLINE=$'\n'

# import functions
. ./bin/functions.sh

errors=""

echo

# check directories and files 
printf "%-80s" "checking zabbix conf dir"
if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ]
then
    errors="Cannot find Zabbix conf dir [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D}]${NEWLINE}"
    echo "[fail]"
    # error_exit "Cannot find Zabbix conf dir [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D}]" 
else
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

xen_detect -v
res=$?
if [ $res -eq 0 ]
then
    errors="${errors}cannot find xm or xe${NEWLINE}"
    # error_exit "cannot find xm or xe"
else
    if [ $res -eq 2 ]
    then
        # Xen checks
        printf "%-80s" "checking PHP"
        which php > /dev/null
        if [ $? -ne 0 ]
        then
            errors="${errors}Cannot find PHP executable, plese install php-cli"
            echo "[fail]"
        else
            echo "[OK]"
        fi
    fi
fi

if [ "X${errors}" == "X" ]
then
    # install files
    install_file userparameter_topix.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${ZABBIX_AGENT_CONF_D}
else
    # errors occourred
    error_exit "${errors}"
fi

