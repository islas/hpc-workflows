#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_stepnames=$5

helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )

justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT] "
checkTest                                                                       \
  TEST_STDOUT_CORRECT_TEST                                                      \
  "Correct test run"                                                            \
  0 $helper_result                                                              \
  $helper_testStdout_loc                                                        \
  "\[test::$helper_testname\][ ]*Preparing working directory"
helper_result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR                                                           \
  "Root dir is set correctly"                                                   \
  0 $helper_result                                                              \
  $helper_testStdout_loc                                                        \
  "Running from root directory $helper_logdir"                                  \
  "\[file::\w+\]"                                                               \
  "Preparing working directory"
helper_result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR_AT_TEST                                                   \
  "Root dir is the same at the test level for test [$helper_testname]"          \
  0 $helper_result                                                              \
  $helper_testStdout_loc                                                        \
  "Running from root directory $helper_logdir"                                  \
  "\[test::$helper_testname\][ ]*Preparing working directory"                   \
  "\[test::$helper_testname\][ ]*Checking if results wait is required"
helper_result=$?

for helper_step in $helper_stepnames; do
  helper_stepStdout_loc=$( format $stepStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname step=$helper_step )
  checkTestBetween                                                                \
    TEST_STDOUT_ROOTDIR_AT_STEP                                                   \
    "Root dir is the same at the step level for step [$helper_step]"              \
    0 $helper_result                                                              \
    $helper_testStdout_loc                                                        \
    "Running from root directory $helper_logdir"                                  \
    "\[step::$helper_step\][ ]*Preparing working directory"                       \
    "\[step::$helper_step\][ ]*Submitting step $helper_step"
  helper_result=$?

  checkTestBetween                                                                \
    TEST_STDOUT_STEP_REDIRECT                                                     \
    "Step stdout is redirected for step [$helper_step]"                           \
    0 $helper_result                                                              \
    $helper_testStdout_loc                                                        \
    "Local step will be redirected to logfile $helper_stepStdout_loc"             \
    "\[step::$helper_step\].*START $helper_step"                                  \
    "\[step::$helper_step\].*STOP $helper_step"
  helper_result=$?
done

return $helper_result