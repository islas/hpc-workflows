#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_mapping="$4"

helper_suite_relfile="$5"
helper_suite_reloffset="$6"
helper_suiteStdout=$7

SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )
. $SOURCE_DIR/helpers.sh
. $SOURCE_DIR/checkers.sh

helper_masterlog=$( format $masterlog_fmt logdir=$helper_logdir suite=$helper_suite )

justify "<" "*" 100 "-->[LOG FILES GENERATED] "
# Check files exist
test -f $helper_suiteStdout
reportTest                                                                      \
  SUITE_STDOUT_CAPTURE                                                          \
  "Suite stdout captured"                                                       \
  0 $helper_result $?
helper_result=$?

test -f $helper_masterlog
reportTest                                                                      \
  MASTERLOG_EXISTS                                                              \
  "Suite summary log generated"                                                 \
  0 $helper_result $?
helper_result=$?

helper_tests=$( getKeys "$helper_mapping" )
for helper_testname in $helper_tests; do
  helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )
  test -f $helper_testStdout_loc
  reportTest                                                                      \
    TEST_STDOUT_CAPTURE                                                           \
    "Test stdout captured at $helper_testStdout_loc"                              \
    0 $helper_result $?
  helper_result=$?

  helper_testlog_loc=$( format $testlog_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )
  test -f $helper_testlog_loc
  reportTest                                                                      \
    TEST_LOG_EXISTS                                                               \
    "Test summary log generated at $helper_testlog_loc"                           \
    0 $helper_result $?
  helper_result=$?

  helper_steps=$( splitValues $( getValuesAtKey "$helper_mapping" $helper_testname ) )
  for helper_step in $helper_steps; do
    helper_stepStdout_loc=$( format $stepStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname step=$helper_step )
    test -f $helper_stepStdout_loc
    reportTest                                                                      \
      STEP_STDOUT_CAPTURE                                                           \
      "Step stdout captured at $helper_stepStdout_loc"                              \
      0 $helper_result $?
    helper_result=$?
  done

done


justify "<" "*" 100 "-->[SANITY CHECKS ON CHECK FUNCTIONS] "
checkTestJson                                                                   \
  SANITY_CHECK_JSON_DNE                                                         \
  "Make sure JSON check fails when key DNE"                                     \
  1 $helper_result                                                              \
  $helper_masterlog                                                             \
  "['metadata']['does_not_exist']"                                              \
  $helper_suite_relfile
helper_result=$?


checkTestJson                                                                   \
  SANITY_CHECK_JSON_NOMATCH                                                     \
  "Make sure JSON check fails when value mismatch"                              \
  1 $helper_result                                                              \
  $helper_masterlog                                                             \
  "['metadata']"                                                                \
  "definitely not this"
helper_result=$?


justify "<" "*" 100 "-->[MASTERLOG METADATA] "
checkTestJson                                                                   \
  MASTERLOG_METADATA_RELFILE                                                    \
  "Ensure masterlog contains metadata for test file"                            \
  0 $helper_result                                                              \
  $helper_masterlog                                                             \
  "['metadata']['rel_file']"                                                    \
  $helper_suite_relfile
helper_result=$?


checkTestJson                                                                   \
  MASTERLOG_METADATA_RELDIR                                                     \
  "Ensure masterlog contains metadata for relative dir"                         \
  0 $helper_result                                                              \
  $helper_masterlog                                                             \
  "['metadata']['rel_offset']"                                                  \
  "$helper_suite_reloffset"
helper_result=$?


exit $helper_result