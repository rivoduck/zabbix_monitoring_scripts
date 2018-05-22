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

xen_detect
if [ $? -eq -1 ]
then
    error_exit "cannot find xm or xe"
fi


# install files
install_file userparameter_topix.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${ZABBIX_AGENT_CONF_D}


