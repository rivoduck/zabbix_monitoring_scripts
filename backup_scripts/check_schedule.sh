#!/bin/bash

. /opt/zabbix_monitoring_scripts/backup_scripts/config_backupvms
cron_entry=$(grep -v "^#" /etc/cron.d/topix-crons | grep "/opt/zabbix_monitoring_scripts/backup_scripts/backupvms.sh")

echo "[${giorno_di_backup}]: ${cron_entry}"

