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
#   -1 cannot find xm or xe, error
#    0 XenServer found
#    1 Xen found
function xen_detect() {
    printf "checking Xen version\t\t\t"
    which xe > /dev/null
    if [ $? -eq 0 ]
    then
        echo "[Xen Server]"
        return 0
    else
        which xm > /dev/null
        if [ $? -eq 0 ]
        then
            echo "[Xen]"
            return 1
        else
            echo "[cannot find]"
            return -1
        fi
    fi
}


