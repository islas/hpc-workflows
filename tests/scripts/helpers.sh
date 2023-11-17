#!/bin/sh

# Useful string manipulation functions, leaving in for posterity
# https://stackoverflow.com/a/8811800
# contains(string, substring)
#
# Returns 0 if the specified string contains the specified substring,
# otherwise returns 1.
contains()
{
  string="$1"
  substring="$2"
  
  if [ "${string#*"$substring"}" != "$string" ]; then
    echo 0    # $substring is in $string
  else
    echo 1    # $substring is not in $string
  fi
}

setenvStr()
{
  # Changing IFS produces the most consistent results
  tmpIFS=$IFS
  IFS=","
  string="$1"
  for s in $string; do
    if [ ! -z $s ]; then 
      eval "echo export \"$s\""
      eval "export \"$s\""
    fi
  done
  IFS=$tmpIFS
}

fqdn()
{
  echo $( python3 -c "import socket; print( socket.getfqdn() )" )
}

# https://unix.stackexchange.com/a/267730
center()
{
  termwidth="$(tput cols)"
  padding="$(printf '%0.1s' "$1"{1..500})"
  printf '%*.*s %s %*.*s\n' 0 "$(((termwidth-2-${#1})/2))" "$padding" "$2" 0 "$(((termwidth-1-${#1})/2))" "$padding"
}