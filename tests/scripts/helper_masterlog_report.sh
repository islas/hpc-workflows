#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_testPass=$5
helper_mapping="$6"

helper_masterlog=$( format $masterlog_fmt logdir=$helper_logdir suite=$helper_suite )

if [ "$helper_testPass" = true ]; then
  justify "<" "*" 100 "-->[MASTERLOG [$helper_testname] SUCCESS] "
  checkTestJson                                                                   \
    MASTERLOG_REPORT_TEST                                                         \
    "Ensure masterlog reports test [$helper_testname] success"                    \
    0 $helper_result                                                              \
    $helper_masterlog                                                             \
    "['$helper_testname']['success']"                                             \
    True
  helper_result=$?
else
  justify "<" "*" 100 "-->[MASTERLOG [$helper_testname] FAILURE] "
  checkTestJson                                                                   \
    MASTERLOG_REPORT_TEST                                                         \
    "Ensure masterlog reports test [$helper_testname] failure"                    \
    0 $helper_result                                                              \
    $helper_masterlog                                                             \
    "['$helper_testname']['success']"                                             \
    False
  helper_result=$?
fi

helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )
checkTestJson                                                                   \
  MASTERLOG_REPORT_TEST_LASTLINE                                                \
  "Masterlog contains last line from test [$helper_testname] stdout"            \
  0 $helper_result                                                              \
  $helper_masterlog                                                             \
  "['$helper_testname']['line']"                                                \
  "$( tail -n 1 $helper_testStdout_loc )"
helper_result=$?

helper_steps=$( getKeys "$helper_mapping" )
for helper_step in $helper_steps; do
  helper_stepStdout_loc=$( format $stepStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname step=$helper_step )

  if [ "$( getValuesAtKey "$helper_mapping" $helper_step )" = true ]; then
    checkTestJson                                                                   \
      MASTERLOG_REPORT_STEP                                                         \
      "Ensure masterlog reports step [$helper_step] success"                        \
      0 $helper_result                                                              \
      $helper_masterlog                                                             \
      "['$helper_testname']['steps']['$helper_step']['success']"                    \
      True
    helper_result=$?
  else
    checkTestJson                                                                   \
      MASTERLOG_REPORT_STEP                                                         \
      "Ensure masterlog reports step [$helper_step] failure"                        \
      0 $helper_result                                                              \
      $helper_masterlog                                                             \
      "['$helper_testname']['steps']['$helper_step']['success']"                    \
      False
    helper_result=$?
  fi

  checkTestJson                                                                   \
    MASTERLOG_REPORT_STEP_LASTLINE                                                \
    "Masterlog contains last line from step [$helper_step] stdout"                \
    0 $helper_result                                                              \
    $helper_masterlog                                                             \
    "['$helper_testname']['steps']['$helper_step']['line']"                       \
    "$( tail -n 1 $helper_stepStdout_loc )"
  helper_result=$?

done

return $helper_result