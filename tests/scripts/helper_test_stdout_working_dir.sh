#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_mapping=$5

SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )
. $SOURCE_DIR/helpers.sh
. $SOURCE_DIR/checkers.sh

helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )

justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT WORKING DIRECTORY] "

helper_steps=$( getKeys "$helper_mapping" )
for helper_step in $helper_steps; do
  helper_stepWorkingDir=$( getValuesAtKey "$helper_mapping" $helper_step )
  checkTestBetween                                                                \
    TEST_STDOUT_WORKDIR_AT_STEP                                                   \
    "Working dir is set for step [$helper_step] to $helper_stepWorkingDir"        \
    0 $helper_result                                                              \
    $helper_testStdout_loc                                                        \
    "Setting working directory to $helper_stepWorkingDir"                         \
    "\[step::$helper_step\][ ]*Preparing working directory"                       \
    "\[step::$helper_step\][ ]*Submitting step $helper_step"
  helper_result=$?

  helper_stepWorkingDirAbs=$( realpath $helper_logdir/$helper_stepWorkingDir )
  checkTestBetween                                                                \
    TEST_STDOUT_WORKDIR_FROM_ROOT                                                 \
    "Absolute path of working dir is applied from root to point to $helper_stepWorkingDirAbs" \
    0 $helper_result                                                              \
    $helper_testStdout_loc                                                        \
    "Current directory : $helper_stepWorkingDirAbs"                               \
    "\[step::$helper_step\][ ]*Preparing working directory"                       \
    "\[step::$helper_step\][ ]*Submitting step $helper_step"
  helper_result=$?
done

exit $helper_result