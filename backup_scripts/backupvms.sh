#!/bin/bash
#
# Written By: Gabriele Rocca
# Created date: 03-11-2015
# Version: 1.0
#

# Variabili da definire

CONFIG='/opt/zabbix_monitoring_scripts/backup_scripts/config_backupvms'

. $CONFIG

TIPO='oggi niente backup'

if [ -z $local_mountpoint ]
then
	echo "impossible leggere il file di configurazione ${CONFIG}, verificare che il pacchetto sia installato sotto /opt/"
	exit -1
fi

if [ "X${1}" == 'Xsettimanale' ] || [ "X${1}" == 'Xmensile' ]
then
	# forza backup indipendentemente dal file di configurazione
	TIPO=$1
else
	if [ "$(date '+%a')" == $giorno_di_backup ]
	then
		if [ "$(date '+%d')" -ge 1 ] && [ "$(date '+%d')" -le 7 ]
		then
			# primo giorno di backup del mese, eseguire un backup mensile
			TIPO='mensile'
		else
			TIPO='settimanale'
		fi
	fi
fi


if [ "$TIPO" == "mensile" ]
then
	numerobackup=$numerobackup_mensile
else
	if [ "$TIPO" == "settimanale" ]
	then
		numerobackup=$numerobackup_settimanale
	else
	    echo "[$(date +"%a %Y-%m-%d %H:%M:%S")] oggi non e' giorno di backup (vedi ${CONFIG})"
	    echo "usare $0 settimanale o $0 mensile per forzare il backup adesso"
		exit 0
	fi
fi



DATA=`date +%Y-%m-%d-%H:%M`
SERVER=`echo $HOSTNAME`
mkdir -p $local_mountpoint
MAIL=/tmp/mail-$DATA.txt

echo "To: $destinatari" > $MAIL
echo "From: $SERVER@top-ix.org" >> $MAIL
echo "Subject: Backup $TIPO" >> $MAIL

# settings for logging (syslog)
loggerTag="xen-backup-$TIPO" # the tag for our log statements
loggerFacility="cron" # the syslog facility to log to

  
# setup logging subsystem. using syslog via logger
logCritical="logger -t ${loggerTag} -s -p ${loggerFacility}.crit"
logWarning="logger -t ${loggerTag} -s -p ${loggerFacility}.warning"
logDebug="logger -t ${loggerTag} -s -p ${loggerFacility}.debug"


# verifica che la cartella dello storage sia montata, scrivibile e abbia lo spazio sufficiente per i backup

foldermounttype=$(stat -f -L -c %T $local_mountpoint)

if [[ "$foldermounttype" != "nfs" ]]
then
        #umount $local_mountpoint
        mount -F $SHARE $local_mountpoint -o nfsvers=3 
fi
  
foldermounttype=$(stat -f -L -c %T $local_mountpoint)
                
if [[ "$foldermounttype" != "nfs" ]]
then
        ${logCritical} "[$(date +"%a %Y-%m-%d %H:%M:%S")] Impossibile montare la cartella per i backup";
	echo -e "Backup Fallito!\nImpossibile montare la cartella per i backup!" >> $MAIL
	/usr/sbin/ssmtp $destinatari < $MAIL
        exit 1;
fi
  
spaziolibero=$(df -P $local_mountpoint|grep $local_mountpoint| awk '{print $4}')
                        
test -w $local_mountpoint/fileprovamount-scrittura || { ${logCritical} "[$(date +"%a %Y-%m-%d %H:%M:%S")] Cartella dei backup non montata correttamente"; exit 1; }

if [  $spaziolibero -lt $spaziominimoStorage ]
then
        ${logCritical} "[$(date +"%a %Y-%m-%d %H:%M:%S")] La cartella dei backup non ha spazio sufficiente per effettuare i backup";
        echo -e "Backup Fallito!\nLa cartella dei backup non ha spazio sufficiente per effettuare i backup!" >> $MAIL
        /usr/sbin/ssmtp $destinatari < $MAIL
        exit 1;
fi


### Mounting remote nfs share backup drive


BACKUPPATH=$local_mountpoint/$TIPO
mkdir -p $BACKUPPATH
[ ! -d $BACKUPPATH ]  && { ${logCritical} "Cartella dei backup non montata correttamente"; echo -e "Backup Fallito!\nCartella dei backup non montata correttamente!" >> $MAIL ; /usr/sbin/ssmtp $destinatari < $MAIL ; exit 1; }

VMUUIDS=''
# Fetching list UUIDs of all VMs running on XenServer
VMUUIDS=$(xe vm-list is-control-domain=false is-a-snapshot=false power-state=running | grep uuid | cut -d":" -f2| sed 's/^ *//g')
INIZIOORE=`date +%k:%M`
INIZIODATA=`date +%d-%m-%Y`
echo -e "\n\n\n***** $INIZIODATA $INIZIOORE: Inizio backup $TIPO macchine di $SERVER\n";
echo -e "Inizio backup $TIPO macchine di $SERVER alle ore $INIZIOORE del $INIZIODATA \n" >> $MAIL

if [ -z "${VMUUIDS}" ]
then
${logDebug} "[$(date +"%a %Y-%m-%d %H:%M:%S")] Nessuna VM da salvare"; echo -e "Nessuna VM da salvare" >> $MAIL ; /usr/sbin/ssmtp $destinatari < $MAIL; exit 1;
fi  


for VMUUID in ${VMUUIDS}
do
    VMNAME=`xe vm-list uuid=$VMUUID | grep name-label | cut -d":" -f2 | sed 's/^ *//g'`

    ${logDebug} "Inizio backup di $VMNAME"	
    SNAPUUID=`xe vm-snapshot uuid=$VMUUID new-name-label="SNAPSHOT-$VMUUID-$DATE"`
    echo "$?"
    xe template-param-set is-a-template=false ha-always-run=false uuid=$SNAPUUID
    echo "$?"
	# lancia l'export dello snapshot usando nice e ionice per dare bassa priorita' al processo sia per la CPU che per l'IO
    #nice -n 19 ionice -c2 -n7 -t xe vm-export vm=$SNAPUUID filename="$BACKUPPATH/$VMNAME-$TIPO-$DATA.xva"
    nice -n 19 ionice -c2 -n7 -t xe vm-export vm=$SNAPUUID filename="$BACKUPPATH/$VMNAME-$TIPO-$SERVER-$DATA.xva"
    chmod 644 "$BACKUPPATH/$VMNAME-$TIPO-$SERVER-$DATA.xva"
    
    echo "$?"
    xe vm-uninstall uuid=$SNAPUUID force=true
    echo "$?"	
    if test $? -ne 0
    then
	${logCritical} "[$(date +"%a %Y-%m-%d %H:%M:%S")] ERRORE nel backup della VM $VMNAME"
	echo -e "ERRORE! Backup di $VMNAME!" >> $MAIL
    else
	${logDebug} "[$(date +"%a %Y-%m-%d %H:%M:%S")] OK. Backup della VM $VMNAME effettuato correttamente"
	echo -e "OK. Backup di $VMNAME" >> $MAIL
    fi

    # VMORDERS=`ls -t $BACKUPPATH/$VMNAME-$TIPO*`  ERRORE se il nome della VM contiene spazi. Racchiudere tra apici
    VMORDERS=`ls -t $BACKUPPATH/"$VMNAME"-$TIPO*`

    contatore=1
    for VMORDER in ${VMORDERS}
    do 
	if [ $contatore -gt $numerobackup ]
	then
		rm $VMORDER
                ${logDebug} "[$(date +"%a %Y-%m-%d %H:%M:%S")] Rimozione vecchio backup $TIPO $VMORDER di $contatore volte prima"  
	fi
	contatore=$((contatore+1))
    done	
	
done

FINEORE=`date +%k:%M`
FINEDATA=`date +%d-%m-%Y`

echo " " >> $MAIL
echo "Fine backup $TIPO macchine di $SERVER alle ore $FINEORE del $FINEDATA" >> $MAIL

/usr/sbin/ssmtp $destinatari < $MAIL

rm /tmp/mail-$DATA.txt

#umount $local_mountpoint


if [ ! -z $TRAP_ZABBIX_HOST ] && [ ! -z $TRAP_HOST ]
then
	# TRAP_KEY='trapmontly'
	if [ $TIPO == "settimanale" ]
	then
		# manda trap settimanale
		# TRAP_KEY='trapweekly'
		/usr/bin/zabbix_sender -z $TRAP_ZABBIX_HOST -p 10051 -s "$TRAP_HOST" -k trapweekly -o 1
	else
		# manda trap mensile e settimanale
		/usr/bin/zabbix_sender -z $TRAP_ZABBIX_HOST -p 10051 -s "$TRAP_HOST" -k trapmontly -o 1
		/usr/bin/zabbix_sender -z $TRAP_ZABBIX_HOST -p 10051 -s "$TRAP_HOST" -k trapweekly -o 1
	fi
	# /usr/bin/zabbix_sender -z $TRAP_ZABBIX_HOST -p 10051 -s "$TRAP_HOST" -k $TRAP_KEY -o 1
fi

echo "***** $FINEDATA $FINEORE: Fine backup $TIPO macchine di $SERVER\n\n";

