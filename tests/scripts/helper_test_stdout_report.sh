#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_testPass=$5
helper_mapping="$6"

helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )


if [ "$helper_testPass" = true ]; then
  justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT SUCCESS] "
  checkTestLastLine                                                               \
    TEST_STDOUT_PASS_LASTLINE                                                     \
    "Test reports success as last line"                                           \
    0 $helper_result                                                              \
    $helper_testStdout_loc                                                        \
    "\[test::$helper_testname\][ ]*\[SUCCESS\] : Test $helper_testname completed successfully"
  helper_result=$?
else
  justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT FAILURE] "
  checkTestLastLine                                                               \
    TEST_STDOUT_FAIL_LASTLINE                                                     \
    "Test reports failure as last line"                                           \
    0 $helper_result                                                              \
    $helper_testStdout_loc                                                        \
    "\[test::$helper_testname\][ ]*\[FAILURE\] : Steps \[ .* \] failed"
  helper_result=$?
fi


helper_steps=$( getKeys "$helper_mapping" )
for helper_step in $helper_steps; do

  if [ "$( getValuesAtKey "$helper_mapping" $helper_step )" = true ]; then
    checkTestBetween                                                                \
      TEST_STDOUT_STEP_REPORTS_SUCCESS                                              \
      "Step [$helper_step] reports success at correct time"                         \
      0 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "\[step::$helper_step\][ ]*\[SUCCESS\]"                                       \
      "\[step::$helper_step\][ ]*Results for $helper_step"                          \
      "\[test::$helper_testname\][ ]*Writing relevant logfiles"
    helper_result=$?
  else

    checkTestBetween                                                                \
      TEST_STDOUT_STEP_REPORTS_FAILURE                                              \
      "Step [$helper_step] reports failure at correct time"                         \
      0 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "\[step::$helper_step\][ ]*\[FAILURE\]"                                       \
      "\[step::$helper_step\][ ]*Results for $helper_step"                          \
      "\[test::$helper_testname\][ ]*Writing relevant logfiles"
    helper_result=$?

    checkTestBetween                                                                \
      TEST_STDOUT_STEP_REPORTS_LASTLINE                                             \
      "Step [$helper_step] reports lastline reason for failure"                     \
      0 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "\[step::$helper_step\][ ]*Line: \".*\""                                      \
      "\[step::$helper_step\][ ]*\[FAILURE\] : Missing key"                         \
      "\[step::$helper_step\][ ]*.*ERROR ERROR ERROR"
    helper_result=$?

  fi
done

return $helper_result