#!/bin/sh
result=$1
logdir=$2

suite=$3
testname=$4
testPass=$5
mapping="$6"

masterlog=$( format $masterlog_fmt logdir=$logdir suite=$suite )

if [ "$testPass" = true ]; then
  justify "<" "*" 100 "-->[MASTERLOG [$testname] SUCCESS] "
  checkTestJson                                                                   \
    MASTERLOG_REPORT_TEST                                                         \
    "Ensure masterlog reports test [$testname] success"                           \
    0 $result                                                                     \
    $masterlog                                                                    \
    "['$testname']['success']"                                                    \
    True
  result=$?
else
  justify "<" "*" 100 "-->[MASTERLOG [$testname] FAILURE] "
  checkTestJson                                                                   \
    MASTERLOG_REPORT_TEST                                                         \
    "Ensure masterlog reports test [$testname] failure"                           \
    0 $result                                                                     \
    $masterlog                                                                    \
    "['$testname']['success']"                                                    \
    False
  result=$?
fi

testStdout_loc=$( format $testStdout_fmt logdir=$logdir suite=$suite testname=$testname )
checkTestJson                                                                   \
  MASTERLOG_REPORT_TEST_LASTLINE                                                \
  "Masterlog contains last line from test [$testname] stdout"                   \
  0 $result                                                                     \
  $masterlog                                                                    \
  "['$testname']['line']"                                                       \
  "$( tail -n 1 $testStdout_loc )"
result=$?

steps=$( getKeys "$mapping" )
for step in $steps; do
  stepStdout_loc=$( format $stepStdout_fmt logdir=$logdir suite=$suite testname=$testname step=$step )

  if [ "$( getValuesAtKey "$mapping" $step )" = true ]; then
    checkTestJson                                                                   \
      MASTERLOG_REPORT_STEP                                                         \
      "Ensure masterlog reports step [$step] success"                               \
      0 $result                                                                     \
      $masterlog                                                                    \
      "['$testname']['steps']['$step']['success']"                                  \
      True
    result=$?
  else
    checkTestJson                                                                   \
      MASTERLOG_REPORT_STEP                                                         \
      "Ensure masterlog reports step [$step] failure"                               \
      0 $result                                                                     \
      $masterlog                                                                    \
      "['$testname']['steps']['$step']['success']"                                  \
      False
    result=$?
  fi

  checkTestJson                                                                   \
    MASTERLOG_REPORT_STEP_LASTLINE                                                \
    "Masterlog contains last line from step [$step] stdout"                       \
    0 $result                                                                     \
    $masterlog                                                                    \
    "['$testname']['steps']['$step']['line']"                                     \
    "$( tail -n 1 $stepStdout_loc )"
  result=$?

done

return $result