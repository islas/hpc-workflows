#!/bin/sh

dir=$1
cd $dir

shift
echo $*
sleep 1
echo "TEST $(basename $0) PASS"