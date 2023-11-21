#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_step=$5
helper_expected="$6"
helper_pass=$7

helper_stepStdout_loc=$( format $stepStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname step=$helper_step )



justify "<" "*" 100 "-->[STEP [$helper_step] STDOUT] "
checkTest                                                                       \
  STEP_STDOUT_CORRECT_STEP                                                      \
  "Correct step run"                                                            \
  0 $helper_result                                                              \
  $helper_stepStdout_loc                                                        \
  "$helper_expected"
helper_result=$?

if [ "$helper_pass" = true ]; then
  checkTestLastLine                                                               \
    STEP_STDOUT_PASS_LASTLINE                                                     \
    "Step reports success as last line"                                           \
    0 $helper_result                                                              \
    $helper_stepStdout_loc                                                        \
    "TEST .* PASS"
  helper_result=$?
else
  checkTestLastLine                                                               \
  STEP_STDOUT_FAIL_LASTLINE                                                       \
  "Step does not have last line pass marker"                                      \
  1 $helper_result                                                                \
  $helper_stepStdout_loc                                                          \
  "TEST .* PASS"
  helper_result=$?
fi

return $helper_result