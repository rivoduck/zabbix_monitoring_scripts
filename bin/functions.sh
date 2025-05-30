function error_exit() {
    echo >&2
    echo "ERRORS:" >&2
    echo "$1" >&2
    echo >&2
    exit "-1"
}

# copy file into place
# arguments:
#   file name
#   install location
#   location in build
function install_file() {
    timestamp=`date +%Y-%m-%d-%H:%M`
    message=$(printf "installing %s in [%s]" "$1" "$2")
    printf "%-80s" "$message"
    if [ -f ${2}${1} ]
    then
        diff ${2}${1} ${3}$1 > /dev/null
        if [ $? -ne 0 ]
        then
			# backup and copy
			mkdir -p /opt/zabbix_monitoring_scripts/backup/
            mv "${2}${1}" "/opt/zabbix_monitoring_scripts/backup/${1}-$timestamp"
            cp ${3}$1 ${2}${1}
            if [ $? -eq 0 ]
            then
                echo "[file copied]"
            else
                echo "[fail]"
            fi
        else
            echo "[no change]"
        fi
	else
		# copy no backup
        cp ${3}$1 ${2}${1}
        if [ $? -eq 0 ]
        then
            echo "[file copied]"
        else
            echo "[fail]"
		fi
    fi
}


# detect Xen or XenServer
# return values:
#    0 no known virtualizer detected, cannot find xm or xe, error
#    1 XenServer found
#    2 Xen found
function vm_detect() {
    if [ "X$1" == "X-v" ]
    then
        printf "%-80s" "checking Virtualizer type"
    fi
    which xe > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
        if [ "X$1" == "X-v" ]
        then
            echo "[Xen Server]"
        fi
        return 1
    else
        which xm > /dev/null 2>&1
        if [ $? -eq 0 ]
        then
            if [ "X$1" == "X-v" ]
            then
                echo "[Xen]"
            fi
            return 2
        else
            if [ "X$1" == "X-v" ]
            then
                echo "[cannot find]"
            fi
            return 0
        fi
    fi
}


# detect RAID management tool
# return values:
#    0 no sw found
#    1 MegaRAID storCLI found
#    2 MegaRAID percCLI found
function disk_detect() {
    if [ "X$1" == "X-v" ]
    then
        printf "%-80s" "checking Raid array type"
    fi
    which storcli > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
        if [ "X$1" == "X-v" ]
        then
            echo "[Mega (stocli)]"
        fi
        return 1
    fi
    which perccli > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
        if [ "X$1" == "X-v" ]
        then
            echo "[Mega (perccli)]"
        fi
        return 2
    fi
    which megacli > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
        if [ "X$1" == "X-v" ]
        then
            echo "[Mega (megacli)]"
        fi
        return 3
    fi

    # no RAID tool found
    if [ "X$1" == "X-v" ]
    then
        echo "[cannot find, looking for commands storcli, perccli, megacli]"
    fi
    return 0
}




# detect docker and docker compose
# return values:
#    0 no docker found
#    1 docker found, no docker compose found
#    2 docker compose found
function docker_detect() {
    if [ "X$1" == "X-v" ]
    then
        printf "%-80s" "checking Docker compose"
    fi
    # Check Docker
    if command -v docker &> /dev/null; then
        # Check Docker Compose
        if command -v docker-compose &> /dev/null; then
            if [ "X$1" == "X-v" ]
            then
                echo "[Docker Compose standalone]"
            fi
            return 2
        elif docker compose version &> /dev/null; then
            if [ "X$1" == "X-v" ]
            then
                echo "[Docker Compose plugin]"
            fi
            return 2
        fi
    else
        if [ "X$1" == "X-v" ]
        then
            echo "[Docker]"
        fi
        return 1
    fi
    if [ "X$1" == "X-v" ]
    then
        echo "[no Docker]"
    fi
    return 0
}
