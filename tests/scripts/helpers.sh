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

justify()
{
  func_justify=$1
  func_fillchar=$2
  func_width=$3
  shift; shift; shift
  func_msg="$*"
  python3 -c "print( '{msg:$func_fillchar$func_justify$func_width}'.format( msg='$func_msg' ) )"
  # https://unix.stackexchange.com/a/267730
  # termwidth="$(tput cols)"
  # padding="$(printf '%0.1s' "$1"{1..64})"
  # printf '%*.*s %s %*.*s\n' 0 "$(((termwidth-2-${#1})/2))" "$padding" "$3" 0 "$(((termwidth-1-${#1})/2))" "$padding"
}

getKeys()
{
  string="$1"
  for substring in $string; do
    echo $substring | awk -F '=' '{print $1}'
  done
}

getValues()
{
  string="$1"
  for substring in $string; do
    echo $substring | awk -F '=' '{print $2}'
  done
}

getValuesAtKey()
{
  string="$1"
  atkey=$2
  for substring in $string; do
    subkey=$( getKeys $substring )
    if [ "$atkey" = "$subkey" ]; then
      echo $substring | awk -F '=' '{print $2}'
      break
    fi
  done
}

getNthValueAtKey()
{
  string="$1"
  atkey=$2
  nth=$3
  for substring in $string; do
    subkey=$( getKeys $substring )
    if [ "$atkey" = "$subkey" ]; then
      values=$( splitValues $( getValues $substring ) )
      val_idx=0
      for subval in $values; do
        if [ $val_idx -eq $nth ]; then
          echo $subval
          break
        fi
        val_idx=$(( $val_idx + 1 ))
      done
    fi
  done
}

splitValues()
{
  string="$1"
  echo $string | tr -d '[' | tr -d ']' | tr ',' '\n'
}

format()
{
  fmt_string="$1"
  shift
  for substring in $*; do
    fmt_pattern=$( echo $substring | awk -F '=' '{print $1}' )
    fmt_value=$( echo $substring | awk -F '=' '{print $2}' )
    fmt_string=$( echo "$fmt_string" | sed "s@%$fmt_pattern%@$fmt_value@" )
  done
  echo $fmt_string
}

# Define formats
masterlog_fmt=%logdir%/%suite%.log
testStdout_fmt=%logdir%/%testname%_stdout.log
testlog_fmt=%logdir%/%suite%.%testname%.log
stepStdout_fmt=%logdir%/%suite%.%testname%.%step%.log
