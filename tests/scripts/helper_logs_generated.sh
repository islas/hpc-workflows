#!/bin/sh
result=$1
logdir=$2
suite=$3
mapping="$4"

suite_relfile="$5"
suite_reloffset="$6"
suiteStdout=$7


masterlog=$( format $masterlog_fmt logdir=$logdir suite=$suite )

justify "<" "*" 100 "-->[LOG FILES GENERATED] "
# Check files exist
test -f $suiteStdout
reportTest                                                                      \
  SUITE_STDOUT_CAPTURE                                                          \
  "Suite stdout captured"                                                       \
  0 $result $?
result=$?

test -f $masterlog
reportTest                                                                      \
  MASTERLOG_EXISTS                                                              \
  "Suite summary log generated"                                                 \
  0 $result $?
result=$?

tests=$( getKeys "$mapping" )
for testname in $tests; do
  testStdout_loc=$( format $testStdout_fmt logdir=$logdir suite=$suite testname=$testname )
  test -f $testStdout_loc
  reportTest                                                                      \
    TEST_STDOUT_CAPTURE                                                           \
    "Test stdout captured at $testStdout_loc"                                     \
    0 $result $?
  result=$?

  testlog_loc=$( format $testlog_fmt logdir=$logdir suite=$suite testname=$testname )
  test -f $testlog_loc
  reportTest                                                                      \
    TEST_LOG_EXISTS                                                               \
    "Test summary log generated at $testlog_loc"                                  \
    0 $result $?
  result=$?

  steps=$( splitValues $( getValuesAtKey "$mapping" $testname ) )
  for step in $steps; do
    stepStdout_loc=$( format $stepStdout_fmt logdir=$logdir suite=$suite testname=$testname step=$step )
    test -f $stepStdout_loc
    reportTest                                                                      \
      STEP_STDOUT_CAPTURE                                                           \
      "Step stdout captured at $stepStdout_loc"                                     \
      0 $result $?
    result=$?
  done

done


justify "<" "*" 100 "-->[SANITY CHECKS ON CHECK FUNCTIONS] "
checkTestJson                                                                   \
  SANITY_CHECK_JSON_DNE                                                         \
  "Make sure JSON check fails when key DNE"                                     \
  1 $result                                                                     \
  $masterlog                                                                    \
  "['metadata']['does_not_exist']"                                              \
  $suite_relfile
result=$?


checkTestJson                                                                   \
  SANITY_CHECK_JSON_NOMATCH                                                     \
  "Make sure JSON check fails when value mismatch"                              \
  1 $result                                                                     \
  $masterlog                                                                    \
  "['metadata']"                                                                \
  "definitely not this"
result=$?


justify "<" "*" 100 "-->[MASTERLOG METADATA] "
checkTestJson                                                                   \
  MASTERLOG_METADATA_RELFILE                                                    \
  "Ensure masterlog contains metadata for test file"                            \
  0 $result                                                                     \
  $masterlog                                                                    \
  "['metadata']['rel_file']"                                                    \
  $suite_relfile
result=$?


checkTestJson                                                                   \
  MASTERLOG_METADATA_RELDIR                                                     \
  "Ensure masterlog contains metadata for relative dir"                         \
  0 $result                                                                     \
  $masterlog                                                                    \
  "['metadata']['rel_offset']"                                                  \
  "$suite_reloffset"
result=$?

return $result