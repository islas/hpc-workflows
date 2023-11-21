#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Check that basic functionality of simplest testing properly passes or fails with correct reports"

# Run various tests from json and do checks
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/00_vs_submitOptions.json -t basic > $redirect 2>&1
result=$?
suite_relfile=00_vs_submitOptions.json
suite_reloffset=""
suiteStdout=$redirect
testStdout=$CURRENT_SOURCE_DIR/basic_stdout.log
stepStdout=$CURRENT_SOURCE_DIR/00_vs_submitOptions.basic.step.log
masterlog=$CURRENT_SOURCE_DIR/00_vs_submitOptions.log
testlog=$CURRENT_SOURCE_DIR/00_vs_submitOptions.basic.log


justify "<" "*" 100 "-->[SUITE RUN OK] "
reportTest                                                                      \
  SUITE_SUCCESS                                                                 \
  "Suite should report success when everything passes"                          \
  0 0 $result

. $CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh $suite_relfile "$suite_reloffset" $result $suiteStdout $testStdout $stepStdout $masterlog $testlog
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh $result $masterlog $testStdout $stepStdout basic step true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $suiteStdout $CURRENT_SOURCE_DIR 1
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout basic true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $testStdout $CURRENT_SOURCE_DIR basic step
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $testStdout basic step true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $stepStdout step "arg0 arg1" true
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log


justify "^" "*" 100 "->[NEGATIVE TESTS]<-"

# Run again, but negative tests cases
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/00_vs_submitOptions.json -t basic-fail > $redirect 2>&1
shouldFail=$?
suite_relfile=00_vs_submitOptions.json
suite_reloffset=""
suiteStdout=$redirect
testStdout=$CURRENT_SOURCE_DIR/basic-fail_stdout.log
stepStdout=$CURRENT_SOURCE_DIR/00_vs_submitOptions.basic-fail.step.log
masterlog=$CURRENT_SOURCE_DIR/00_vs_submitOptions.log
testlog=$CURRENT_SOURCE_DIR/00_vs_submitOptions.basic-fail.log

justify "<" "*" 100 "-->[SUITE FAILS OK] "
reportTest                                                                      \
  SUITE_FAILURE                                                                 \
  "Suite should report failure when step fails in a test"                       \
  1 $result $shouldFail


. $CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh $suite_relfile "$suite_reloffset" $result $suiteStdout $testStdout $stepStdout $masterlog $testlog
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh $result $masterlog $testStdout $stepStdout basic-fail step false false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout basic-fail false false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $testStdout $CURRENT_SOURCE_DIR basic-fail step
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $testStdout basic-fail step false false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $stepStdout step "arg0 arg1" false
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log

exit $result