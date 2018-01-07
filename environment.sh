#!/bin/bash
which bork
#0: found 1:not found
available=$?
echo "$available"
#fedora uses pip for python 2+ and pip3 for 3+
#add type for pip3
pip3_type='
### exact copy of bork pip.sh ###
### except with pip3 replacing pip ###
### https://github.com/mattly/bork/blob/master/types/pip.sh ###

# TODO --sudo flag
# TODO versions
# TODO update

action=$1
name=$2
shift 2

case $action in
  desc)
    echo "asserts presence of packages installed via pip"
    echo "> pip pygments"
    ;;
  status)
    needs_exec "pip3" || return $STATUS_FAILED_PRECONDITION
    pkgs=$(bake pip3 list)
    if ! str_matches "$pkgs" "^$name"; then
      return $STATUS_MISSING
    fi
    return 0 ;;
  install)
    bake sudo pip3 install "$name"
    ;;
esac'

#install bork if it is not found
if [[ $available == 1 ]]
    then
    echo bork not found installing 
    wget -P /tmp https://github.com/mattly/bork/archive/master.zip
    #unzipping creates tmp/bork-master
    unzip /tmp/master.zip -d /tmp
    #install per bork install instructions
    sudo cp -r /tmp/bork-master/ /usr/local/src/bork/
    sudo ln -sf /usr/local/src/bork/bin/bork /usr/local/bin/bork
    sudo ln -sf /usr/local/src/bork/bin/bork-compile /usr/local/bin/bork-compile
    #add pip3 type
    echo "$pip3_type" | sudo tee /usr/local/src/bork/types/pip3.sh
fi

#if pip3 type does not exist add
if [ ! -f /usr/local/src/bork/types/pip33.sh ]; then
    echo "$pip3_type" | sudo tee /usr/local/src/bork/types/pip33.sh
fi

if [[ $available == 0 ]]
    then echo bork found...
fi

#ready to start bork scripts
bork satisfy env_meta.bork
