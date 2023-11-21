#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/helpers.sh
. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Check that when a multi-test suite runs, if one test fails correct reporting is done"

# 
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/00_vs_submitOptions.json -t basic basic-fail-multistep > $redirect 2>&1
shouldFail=$?
suite=00_vs_submitOptions
suite_relfile=$suite.json
suite_reloffset=""
suiteStdout=$redirect

test0=basic-fail-multistep
test0_step0=step-pass
test0_step1=step-fail

test1=basic
test1_step0=step


justify "<" "*" 100 "-->[SUITE FAILS OK] "
reportTest                                                                      \
  SUITE_FAILURE                                                                 \
  "Suite should report failure when step fails in a test"                       \
  1 0 $shouldFail
result=$?


. $CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh \
  $result                                                 \
  $CURRENT_SOURCE_DIR                                     \
  $suite                                                  \
  "$test0=[$test0_step0,$test0_step1] $test1=[$test1_step0]" \
  "$suite_relfile"                                        \
  "$suite_reloffset"                                      \
  $suiteStdout                                            \
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
  $result                                                   \
  $CURRENT_SOURCE_DIR                                       \
  $suite                                                    \
  $test0                                                    \
  false                                                     \
  "$test0_step0=true $test0_step1=false"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $CURRENT_SOURCE_DIR $suiteStdout 2
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh \
  $result              \
  $suiteStdout         \
  $test0               \
  false false
result=$?

justify "^" "*" 100 "->[CHECK FAILED TEST]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh \
  $result             \
  $CURRENT_SOURCE_DIR \
  $test0              \
  "$test0_step0 $test0_step1"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh \
  $result             \
  $CURRENT_SOURCE_DIR \
  $suite              \
  $test0              \
  false               \
  "$test0_step0=true $test0_step1=false"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh \
  $result $CURRENT_SOURCE_DIR $suite $test0 \
  $test0_step0   \
  "arg0 arg1" \
  true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh \
  $result $CURRENT_SOURCE_DIR $suite $test0 \
  $test0_step1   \
  "arg0 arg1" \
  false
result=$?


# justify "^" "*" 100 "->[CHECK PASSED TEST]<-"
# . $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
#   $result                                                   \
#   $masterlog                                                \
#   $( format $testStdout_fmt testname=basic )                \
#   $( format $stepStdout_fmt testname=basic step=step )      \
#   basic                                                     \
#   step                                                      \
#   true true
# result=$?

# . $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh \
#   $result              \
#   $suiteStdout         \
#   basic                \
#   false true
# result=$?

# . $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh \
#   $result             \
#   $( format $testStdout_fmt testname=basic ) \
#   $CURRENT_SOURCE_DIR \
#   $testName           \
#   "step"
# result=$?
# . $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $( format $testStdout_fmt testname=basic ) basic step true true
# result=$?
# . $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $stepPassStdout step "arg0 arg1" true
# result=$?
# . $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $stepFailStdout step "arg0 arg1" false
# result=$?


# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log

exit $result