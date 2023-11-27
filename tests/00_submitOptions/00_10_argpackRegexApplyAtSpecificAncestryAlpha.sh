#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/helpers.sh
. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Demonstrate alpha order precedence of argpacks, even when regex applied"

# Run various tests from json and do checks
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
suite=00_submitOptions
test0=applyAtSpecificAncestry-alpharegex
test0_step0=step_setA_setB
test0_step1=step_setD_setC
test0_step2=step_setA_setB_setC_setD
test0_step3=step_none_set_a_set_B_settC_dSet


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
  "$test0=[$test0_step0,$test0_step1,$test0_step2,$test0_step3]"           \
  "$suite_relfile"                                        \
  "$suite_reloffset"                                      \
  $suiteStdout
result=$?

justify "^" "*" 100 "->[CHECK REGEX TEST]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
  $result $CURRENT_SOURCE_DIR $suite                        \
  $test0 true "$test0_step0=true"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $CURRENT_SOURCE_DIR $suiteStdout 1
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $test0 true true
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 \
  "$test0_step0=./tests/scripts/echo_normal.sh \
   $test0_step1=./tests/scripts/echo_normal.sh \
   $test0_step2=./tests/scripts/echo_normal.sh \
   $test0_step3=./tests/scripts/echo_normal.sh"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_working_dir.sh $result $CURRENT_SOURCE_DIR $suite $test0 \
  "$test0_step0=../../ \
   $test0_step1=../../ \
   $test0_step2=../../ \
   $test0_step3=../../"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $CURRENT_SOURCE_DIR $suite $test0 true \
  "$test0_step0=true \
   $test0_step1=true \
   $test0_step2=true \
   $test0_step3=true"
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step0] STEP ]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 \
  "argset_01=\['arg0','arg1'\]                   \
   \.\*regex\.\*::argset_02=\[\]                 \
   \.\*setB\.\*::beSecondSet=\['setB'\]             \
   \.\*setA\.\*::shouldBeLast=\['setA'\]" \
  "argset_01=$suite                              \
   \.\*regex\.\*::argset_02=$test0               \
   \.\*setB\.\*::beSecondSet=$test0                 \
   \.\*setA\.\*::shouldBeLast=$test0"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 \
  "\.\*setD\.\*::alwaysFirst=\['setD'\]             \
   \.\*setC\.\*::needsToBeBetween_b_and_s=\['setC'\]" \
  "\.\*setD\.\*::alwaysFirst=$test0                \
   \.\*setC\.\*::needsToBeBetween_b_and_s=$test0" false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "arg0 arg1 setB setA" true
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step1] STEP ]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 \
  "\.\*setD\.\*::alwaysFirst=\['setD'\]               \
  argset_01=\['arg0','arg1'\]                         \
   \.\*regex\.\*::argset_02=\[\]                      \
   \.\*setC\.\*::needsToBeBetween_b_and_s=\['setC'\]" \
  "\.\*setD\.\*::alwaysFirst=$test0                \
   argset_01=$suite                                \
   \.\*regex\.\*::argset_02=$test0
   \.\*setC\.\*::needsToBeBetween_b_and_s=$test0"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 \
  "\.\*setB\.\*::beSecondSet=\['setB'\]             \
   \.\*setA\.\*::shouldBeLast=\['setA'\]" \
  "\.\*setB\.\*::beSecondSet=$test0                \
   \.\*setA\.\*::shouldBeLast=$test0" false
result=$?


. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 "setD arg0 arg1 setC" true
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step2] STEP ]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step2 \
  "\.\*setD\.\*::alwaysFirst=\['setD'\]              \
  argset_01=\['arg0','arg1'\]                        \
   \.\*regex\.\*::argset_02=\[\]                     \
   \.\*setB\.\*::beSecondSet=\['setB'\]                 \
   \.\*setC\.\*::needsToBeBetween_b_and_s=\['setC'\] \
   \.\*setA\.\*::shouldBeLast=\['setA'\]"            \
  "\.\*setD\.\*::alwaysFirst=$test0                  \
   argset_01=$suite                                  \
   \.\*regex\.\*::argset_02=$test0                   \
   \.\*setB\.\*::beSecondSet=$test0                     \
   \.\*setC\.\*::needsToBeBetween_b_and_s=$test0     \
   \.\*setA\.\*::shouldBeLast=$test0"
result=$?

result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step2 "setD arg0 arg1 setB setC setA" true
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step3] STEP ]<-"
. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 \
  "argset_01=\['arg0','arg1'\]                    \
   \.\*regex\.\*::argset_02=\[\]" \
  "argset_01=$suite                              \
   \.\*regex\.\*::argset_02=$test0"
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 \
  "\.\*setB\.\*::beSecondSet=\['setB'\]             \
   \.\*setA\.\*::shouldBeLast=\['setA'\]             \
   \.\*setD\.\*::alwaysFirst=\['setD'\]             \
   \.\*setC\.\*::needsToBeBetween_b_and_s=\['setC'\]" \
  "\.\*setB\.\*::beSecondSet=$test0                \
   \.\*setA\.\*::shouldBeLast=$test0                \
   \.\*setD\.\*::alwaysFirst=$test0                \
   \.\*setC\.\*::needsToBeBetween_b_and_s=$test0" false
result=$?

. $CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 "arg0 arg1" true
result=$?


# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log
exit $result