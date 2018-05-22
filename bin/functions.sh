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
            cp "${2}${1}" "${2}${1}-$timestamp"
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
        printf "%-70s" "checking Xen version"
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


