function fix_path { # file_path
    if test -n "$1"
    then
        # get full path, will fail when trying to write to other user's home
        local result=${1#\~/}
        [[ "$1" != "$result" ]] && result="$HOME/$result"
        [[ "$result" =~ ^/ ]] || result="$PWD/$1"
        echo "$result"
    fi
}

function require_script { # script_path
    ! test -f $1 && echo "ERROR: Cannot find required script $1!" && exit 1
}