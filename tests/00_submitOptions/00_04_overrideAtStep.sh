#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/helpers.sh
. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Demonstrate submit options being overridden at the step level"

# Run various tests from json and do checks
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
suite=00_submitOptions
test0=overrideAtStep
test0_step0=stepOverride

$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/$suite.json -t $test0 > $redirect 2>&1
result=$?
suite_relfile=$suite.json
suite_reloffset=""
suiteStdout=$redirect




justify "<" "*" 100 "-->[SUITE RUN OK] "
reportTest                                                                      \
  SUITE_SUCCESS                                                                 \
  "Suite should report success when everything passes"                          \
  0 0 $result

justify "^" "*" 100 "->[CHECK LOGS EXIST]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh \
  $result $CURRENT_SOURCE_DIR $suite                      \
  "$test0=[$test0_step0]"                                 \
  "$suite_relfile"                                        \
  "$suite_reloffset"                                      \
  $suiteStdout
result=$?

justify "^" "*" 100 "->[CHECK PASS TEST]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
  $result $CURRENT_SOURCE_DIR $suite                        \
  $test0 true "$test0_step0=true"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $CURRENT_SOURCE_DIR $suiteStdout 1
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $test0 true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 "$test0_step0=../../tests/scripts/echo_normal.sh"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_working_dir.sh $result $CURRENT_SOURCE_DIR $suite $test0 "$test0_step0=."
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "argset_01=\['arg4','arg5'\]" "argset_01=$test0_step0"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $CURRENT_SOURCE_DIR $suite $test0 true "$test0_step0=true"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "arg4 arg5" true
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log
exit $result