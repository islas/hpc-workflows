#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/helpers.sh
. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Check that when a multi-step test runs, if no dependencies are set all steps will maximize usage of threadpool"

# 
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
suite=02_multiAction
suite_relfile=$suite.json
suite_reloffset=""
suiteStdout=$redirect
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/$suite.json -t basicParallel -tp 4 > $redirect 2>&1
result=$?


test0=basicParallel
test0_step0=stepA
test0_step1=stepB
test0_step2=stepC
test0_step3=stepD

justify "<" "*" 100 "-->[SUITE RUNS OK] "
reportTest                                                                      \
  SUITE_SUCCESS                                                                 \
  "Suite should report success when everything passes"                       \
  0 0 $result
result=$?


justify "^" "*" 100 "->[CHECK LOGS EXIST]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh \
  $result                                                 \
  $CURRENT_SOURCE_DIR                                     \
  $suite                                                  \
  "$test0=[$test0_step0,$test0_step1,$test0_step2,$test0_step3]" \
  "$suite_relfile"                                        \
  "$suite_reloffset"                                      \
  $suiteStdout
result=$?

justify "^" "*" 100 "->[CHECK PASSED TEST]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
  $result $CURRENT_SOURCE_DIR $suite                        \
  $test0 true                                              \
  "$test0_step0=true $test0_step1=true $test0_step2=true $test0_step3=true"
result=$?


$CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $CURRENT_SOURCE_DIR $suiteStdout 1
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $test0 true true
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh \
  $result $CURRENT_SOURCE_DIR $suite $test0 \
  "$test0_step0=./tests/scripts/echo_normal_sleep.sh \
   $test0_step1=./tests/scripts/echo_normal_sleep.sh \
   $test0_step2=./tests/scripts/echo_normal_sleep.sh \
   $test0_step3=./tests/scripts/echo_normal_sleep.sh"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_working_dir.sh \
  $result $CURRENT_SOURCE_DIR $suite $test0 \
  "$test0_step0=../../ \
   $test0_step1=../../ \
   $test0_step2=../../ \
   $test0_step3=../../"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "argset_01=\['arg0','arg1'\]" "argset_01=$suite"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 "argset_01=\['arg0','arg1'\]" "argset_01=$suite"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step2 "argset_01=\['arg0','arg1'\]" "argset_01=$suite"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 "argset_01=\['arg0','arg1'\]" "argset_01=$suite"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh \
  $result $CURRENT_SOURCE_DIR $suite \
  $test0 true "$test0_step0=true $test0_step1=true $test0_step2=true $test0_step3=true"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_step_dep_order.sh \
  $result $CURRENT_SOURCE_DIR $suite \
  $test0 "$test0_step0=[] $test0_step1=[] $test0_step2=[] $test0_step3=[]"
result=$?

# we know steps are submitted in appearing order from the test config so this will work
# when using the test script that sleeps to enforce coherency
$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_step_parallel.sh \
  $result $CURRENT_SOURCE_DIR $suite \
  $test0 "$test0_step0=[$test0_step1,$test0_step2,$test0_step3] \
          $test0_step1=[$test0_step2,$test0_step3] \
          $test0_step2=[$test0_step3]"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "arg0 arg1" true
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 "arg0 arg1" true
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step2 "arg0 arg1" true
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 "arg0 arg1" true
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log

exit $result