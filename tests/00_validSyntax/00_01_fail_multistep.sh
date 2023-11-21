#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Check that when a multi-step test runs, if one step fails correct reporting is done"

# 
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/00_vs_submitOptions.json -t basic-fail-multistep > $redirect 2>&1
shouldFail=$?
suite_relfile=00_vs_submitOptions.json
suite_reloffset=""
suiteStdout=$redirect
testName=basic-fail-multistep
testStdout=$CURRENT_SOURCE_DIR/${testName}_stdout.log
stepPassStdout=$CURRENT_SOURCE_DIR/00_vs_submitOptions.$testName.step-pass.log
stepFailStdout=$CURRENT_SOURCE_DIR/00_vs_submitOptions.$testName.step-fail.log
masterlog=$CURRENT_SOURCE_DIR/00_vs_submitOptions.log
testlog=$CURRENT_SOURCE_DIR/00_vs_submitOptions.$testName.log

justify "<" "*" 100 "-->[SUITE FAILS OK] "
reportTest                                                                      \
  SUITE_FAILURE                                                                 \
  "Suite should report failure when step fails in a test"                       \
  1 0 $shouldFail
result=$?


. $CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh \
  $suite_relfile                                          \
  "$suite_reloffset"                                      \
  $result                                                 \
  $suiteStdout                                            \
  $testStdout                                             \
  "$stepPassStdout $stepFailStdout"                       \
  $masterlog $testlog
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh $result $masterlog $testStdout $stepPassStdout $testName step-pass false true
result=$?


. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh $result $masterlog $testStdout $stepFailStdout $testName step-fail false false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $suiteStdout $CURRENT_SOURCE_DIR 1
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $testName false false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $testStdout $CURRENT_SOURCE_DIR $testName "step-pass step-fail"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $testStdout $testName step-pass false true
result=$?
. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $testStdout $testName step-fail false false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $stepPassStdout step "arg0 arg1" true
result=$?
. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $stepFailStdout step "arg0 arg1" false
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log

exit $result