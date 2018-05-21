#!/bin/bash

# use this script to update the installation after new code is pulled

ZABBIX_BASE_CONFDIR="/etc/zabbix/"
ZABBIX_AGENT_CONF_D="zabbix_agentd.conf.d/"
BUILD_BASE="/opt/zabbix_monitoring_scripts/"


function error_exit {
    echo >&2
    echo "ERROR: $1" >&2   ## Send message to stderr. Exclude >&2 if you don't want it that way.
    echo >&2
    exit "${2:-1}"  ## Return a code specified by $2 or 1 by default.
}

# arguments:
#   file name
#   install location
#   location in build
function install_file {
    timestamp=`date +%Y-%m-%d-%H:%M`
    printf "installing %s in [%s]\t\t" $1 $2
    if [ -f ${2}${1} ]
    then
        diff ${2}${1} ${3}$1 > /dev/null
        if [ $? -ne 0 ]
        then
            cp "${2}${1}" "${2}${1}-$timestamp"
            cp ${3}$1 ${2}${1}
            echo " [file copied]"
        else
            echo " [no change]"
        fi
    fi
}


if [ ! -d ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ]
then
	error_exit "cannot find Zabbix conf dir [${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D}]" 
fi



install_file userparameter_topix.conf ${ZABBIX_BASE_CONFDIR}${ZABBIX_AGENT_CONF_D} ${BUILD_BASE}${ZABBIX_AGENT_CONF_D}


