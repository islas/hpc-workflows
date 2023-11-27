#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/helpers.sh
. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Demonstrate argpack complex feature of allowing regex using submit options logic of override at step"

# Run various tests from json and do checks
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
suite=00_submitOptions
test0=overrideAtStep-regex
test0_step0=step
test1=basic
test1_step0=step

$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/$suite.json -t $test0 $test1 > $redirect 2>&1
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
  "$test0=[$test0_step0] $test1=[$test1_step0]"           \
  "$suite_relfile"                                        \
  "$suite_reloffset"                                      \
  $suiteStdout
result=$?

justify "^" "*" 100 "->[CHECK REGEX TEST]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
  $result $CURRENT_SOURCE_DIR $suite                        \
  $test0 true "$test0_step0=true"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $CURRENT_SOURCE_DIR $suiteStdout 2
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $test0 true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 "$test0_step0=./tests/scripts/echo_normal.sh"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_working_dir.sh $result $CURRENT_SOURCE_DIR $suite $test0 "$test0_step0=../../"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 \
  "argset_01=\['arg0','arg1'\] \.\*regex\.\*::argset_02=\['overrideAtStep'\]" "argset_01=$suite \.\*regex\.\*::argset_02=$test0_step0"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $CURRENT_SOURCE_DIR $suite $test0 true "$test0_step0=true"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "arg0 arg1 overrideAtStep" true
result=$?

justify "^" "*" 100 "->[CHECK NON-REGEX TEST]<-"

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $test1 true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test1 "$test1_step0=./tests/scripts/echo_normal.sh"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_working_dir.sh $result $CURRENT_SOURCE_DIR $suite $test1 "$test1_step0=../../"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test1 $test1_step0 "argset_01=\['arg0','arg1'\]" "argset_01=$suite"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test1 $test1_step0 \
  "\.\*regex\.\*::argset_02=\['dontcare'\]" "\.\*regex\.\*::argset_02=$suite" false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $CURRENT_SOURCE_DIR $suite $test1 true "$test1_step0=true"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test1 $test1_step0 "arg0 arg1" true
result=$?


# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log
exit $result