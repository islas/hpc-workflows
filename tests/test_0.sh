#!/bin/sh

dir=$1
cd $dir

shift
echo $*
echo "TEST $(basename $0) PASS"