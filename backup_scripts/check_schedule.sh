#!/bin/bash

. /opt/zabbix_monitoring_scripts/backup_scripts/config_backupvms
echo "${giorno_di_backup} \c"
grep -v ^# /etc/cron.d/topix-crons | grep /opt/zabbix_monitoring_scripts/backup_scripts/backupvms.sh\""


