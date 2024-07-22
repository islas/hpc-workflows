#!/bin/sh

config=$1
dir=$2
cd $dir

shift; shift
echo $*
echo "TEST $(basename $0) PASS"
