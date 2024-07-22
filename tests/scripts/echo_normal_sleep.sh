#!/bin/sh

config=$1
dir=$2
cd $dir

shift; shift
echo $*
sleep 1
echo "TEST $(basename $0) PASS"
