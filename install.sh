#!/bin/bash

# use this script to update the installation after new code is pulled

ZABBIX_BASE_CONFDIR="/etc/zabbix/"
ZABBIX_AGENT_CONF_D="zabbix_agentd.conf.d/"
BUILD_BASE="/opt/zabbix_monitoring_scripts/"


# import functions
. ./bin/functions.sh

# check directories and files 
if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ]
then
	error_exit "cannot find Zabbix conf dir [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D}]" 
fi

if [ ! -d ${BUILD_BASE} ]
then
	error_exit "Cannot find distribution, make sure files are installed in ${BUILD_BASE}" 
fi


printf "checking Xen version\t\t\t"
which xe
if [ $? -eq 0 ]
then
    echo "[Xen Server]"
else
    which xm
    if [ $? -eq 0 ]
    then
        echo "[Xen]"
    else
        echo "[cannot find]"
        error_exit "Cannot find Xen/XenServer installation, make sure xm or xe are in the path"
    fi
fi




# install files
install_file userparameter_topix.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${ZABBIX_AGENT_CONF_D}


