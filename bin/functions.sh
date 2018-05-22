function error_exit() {
    echo >&2
    echo "ERROR: $1" >&2   ## Send message to stderr. Exclude >&2 if you don't want it that way.
    echo >&2
    exit "${2:-1}"  ## Return a code specified by $2 or 1 by default.
}

# copy file into place
# arguments:
#   file name
#   install location
#   location in build
function install_file() {
    timestamp=`date +%Y-%m-%d-%H:%M`
    printf "installing %s in [%s]\t\t" $1 $2
    if [ -f ${2}${1} ]
    then
        diff ${2}${1} ${3}$1 > /dev/null
        if [ $? -ne 0 ]
        then
            cp "${2}${1}" "${2}${1}-$timestamp"
            cp ${3}$1 ${2}${1}
            echo "[file copied]"
        else
            echo "[no change]"
        fi
    fi
}


# detect Xen or XenServer
# return values:
#    0 cannot find xm or xe, error
#    1 XenServer found
#    2 Xen found
function xen_detect() {
    if [ "X$1" == "X-v" ]
    then
        printf "checking Xen version\t\t\t\t\t\t\t\t\t"
    fi
    which xe > /dev/null
    if [ $? -eq 0 ]
    then
        if [ "X$1" == "X-v" ]
        then
            echo "[Xen Server]"
        fi
        return 1
    else
        which xm > /dev/null
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


