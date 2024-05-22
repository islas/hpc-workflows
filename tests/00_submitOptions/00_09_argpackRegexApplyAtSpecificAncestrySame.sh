#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/helpers.sh
. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"
echo "Purpose:"
echo "  Demonstrate when argpack names match (for regex after <regex>:: pattern) they are applied in order supplied"

# Run various tests from json and do checks
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
suite=00_submitOptions
test0=applyAtSpecificAncestry-sameregex
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
$CURRENT_SOURCE_DIR/../scripts/helper_logs_generated.sh \
  $result $CURRENT_SOURCE_DIR $suite                      \
  "$test0=[$test0_step0,$test0_step1,$test0_step2,$test0_step3]"           \
  "$suite_relfile"                                        \
  "$suite_reloffset"                                      \
  $suiteStdout
result=$?

justify "^" "*" 100 "->[CHECK REGEX TEST]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_masterlog_report.sh \
  $result $CURRENT_SOURCE_DIR $suite                        \
  $test0 true "$test0_step0=true"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_main_stdout.sh $result $CURRENT_SOURCE_DIR $suiteStdout 1
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_main_stdout_report.sh $result $suiteStdout $test0 true true
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 \
  "$test0_step0=./tests/scripts/echo_normal.sh \
   $test0_step1=./tests/scripts/echo_normal.sh \
   $test0_step2=./tests/scripts/echo_normal.sh \
   $test0_step3=./tests/scripts/echo_normal.sh"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_working_dir.sh $result $CURRENT_SOURCE_DIR $suite $test0 \
  "$test0_step0=../../ \
   $test0_step1=../../ \
   $test0_step2=../../ \
   $test0_step3=../../"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_report.sh $result $CURRENT_SOURCE_DIR $suite $test0 true \
  "$test0_step0=true \
   $test0_step1=true \
   $test0_step2=true \
   $test0_step3=true"
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step0] STEP ]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 \
  "\.\*setB\.\*::argRegex=\['setB'\]             \
   \.\*setA\.\*::argRegex=\['setA'\]             \
   argset_01=\['arg0','arg1'\]                    \
   \.\*regex\.\*::argset_02=\[\]" \
  "\.\*setB\.\*::argRegex=$suite.$test0          \
   \.\*setA\.\*::argRegex=$suite.$test0          \
   argset_01=$suite                              \
   \.\*regex\.\*::argset_02=$suite.$test0"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 \
  "\.\*setD\.\*::argRegex=\['setD'\]             \
   \.\*setC\.\*::argRegex=\['setC'\]" \
  "\.\*setD\.\*::argRegex=$suite.$test0          \
   \.\*setC\.\*::argRegex=$suite.$test0" false
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step0 "setB setA arg0 arg1" true
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step1] STEP ]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 \
  "\.\*setD\.\*::argRegex=\['setD'\]             \
   \.\*setC\.\*::argRegex=\['setC'\]             \
   argset_01=\['arg0','arg1'\]                    \
   \.\*regex\.\*::argset_02=\[\]" \
  "\.\*setD\.\*::argRegex=$suite.$test0          \
   \.\*setC\.\*::argRegex=$suite.$test0          \
   argset_01=$suite                              \
   \.\*regex\.\*::argset_02=$suite.$test0"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 \
  "\.\*setB\.\*::argRegex=\['setB'\]             \
   \.\*setA\.\*::argRegex=\['setA'\]" \
  "\.\*setB\.\*::argRegex=$suite.$test0          \
   \.\*setA\.\*::argRegex=$suite.$test0" false
result=$?


$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step1 "setD setC arg0 arg1" true
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step2] STEP ]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step2 \
  "\.\*setB\.\*::argRegex=\['setB'\]             \
   \.\*setA\.\*::argRegex=\['setA'\]             \
   \.\*setD\.\*::argRegex=\['setD'\]             \
   \.\*setC\.\*::argRegex=\['setC'\]             \
   argset_01=\['arg0','arg1'\]                    \
   \.\*regex\.\*::argset_02=\[\]" \
  "\.\*setB\.\*::argRegex=$suite.$test0          \
   \.\*setA\.\*::argRegex=$suite.$test0          \
   \.\*setD\.\*::argRegex=$suite.$test0          \
   \.\*setC\.\*::argRegex=$suite.$test0          \
   argset_01=$suite                              \
   \.\*regex\.\*::argset_02=$suite.$test0"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step2 "setB setA setD setC arg0 arg1" true
result=$?

justify "^" "*" 100 "->[CHECK [$test0_step3] STEP ]<-"
$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 \
  "argset_01=\['arg0','arg1'\]                    \
   \.\*regex\.\*::argset_02=\[\]" \
  "argset_01=$suite                              \
   \.\*regex\.\*::argset_02=$suite.$test0"
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_test_stdout_argpacks.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 \
  "\.\*setB\.\*::argRegex=\['setB'\]             \
   \.\*setA\.\*::argRegex=\['setA'\]             \
   \.\*setD\.\*::argRegex=\['setD'\]             \
   \.\*setC\.\*::argRegex=\['setC'\]" \
  "\.\*setB\.\*::argRegex=$suite.$test0          \
   \.\*setA\.\*::argRegex=$suite.$test0          \
   \.\*setD\.\*::argRegex=$suite.$test0          \
   \.\*setC\.\*::argRegex=$suite.$test0" false
result=$?

$CURRENT_SOURCE_DIR/../scripts/helper_step_stdout.sh $result $CURRENT_SOURCE_DIR $suite $test0 $test0_step3 "arg0 arg1" true
result=$?


# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log
exit $result