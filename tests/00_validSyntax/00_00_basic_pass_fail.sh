#!/bin/sh
# https://stackoverflow.com/a/29835459
CURRENT_SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )

. $CURRENT_SOURCE_DIR/../scripts/checkers.sh

echo "Tests for $( basename $0 )"

# Run various tests from json and do checks
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/00_vs_submitOptions.json -t basic > $redirect 2>&1
result=$?
justify "<" "*" 100 "-->[SUITE RUN OK] "
reportTest                                                                      \
  SUITE_SUCCESS                                                                 \
  "Suite should report success when everything passes"                          \
  0 0 $result

justify "<" "*" 100 "-->[LOG FILES GENERATED] "
# Check files exist
test -f $redirect
reportTest                                                                      \
  SUITE_STDOUT_CAPTURE                                                          \
  "Suite stdout captured"                                                       \
  0 $result $?
result=$?

test -f $CURRENT_SOURCE_DIR/basic_stdout.log
reportTest                                                                      \
  TEST_STDOUT_CAPTURE                                                           \
  "Test stdout captured"                                                        \
  0 $result $?
result=$?

test -f $CURRENT_SOURCE_DIR/00_vs_submitOptions.basic.step.log
reportTest                                                                      \
  STEP_STDOUT_CAPTURE                                                           \
  "Step stdout captured"                                                        \
  0 $result $?
result=$?

test -f $CURRENT_SOURCE_DIR/00_vs_submitOptions.basic.log
reportTest                                                                      \
  TEST_LOG_EXISTS                                                               \
  "Test summary log generated"                                                  \
  0 $result $?
result=$?

test -f $CURRENT_SOURCE_DIR/00_vs_submitOptions.log
reportTest                                                                      \
  MASTERLOG_EXISTS                                                              \
  "Suite summary log generated"                                                 \
  0 $result $?
result=$?


justify "<" "*" 100 "-->[SANITY CHECKS ON CHECK FUNCTIONS] "
checkTestJson                                                                   \
  SANITY_CHECK_JSON_DNE                                                         \
  "Make sure JSON check fails when key DNE"                                     \
  1 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['metadata']['does_not_exist']"                                              \
  00_vs_submitOptions.json
result=$?


checkTestJson                                                                   \
  SANITY_CHECK_JSON_NOMATCH                                                     \
  "Make sure JSON check fails when value mismatch"                              \
  1 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['metadata']"                                                                \
  "definitely not this"
result=$?


justify "<" "*" 100 "-->[MASTERLOG METADATA] "
checkTestJson                                                                   \
  MASTERLOG_METADATA_RELFILE                                                    \
  "Ensure masterlog contains metadata for test file"                            \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['metadata']['rel_file']"                                                    \
  00_vs_submitOptions.json
result=$?


checkTestJson                                                                   \
  MASTERLOG_METADATA_RELDIR                                                     \
  "Ensure masterlog contains metadata for relative dir"                         \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['metadata']['rel_offset']"                                                  \
  ""
result=$?

justify "<" "*" 100 "-->[MASTERLOG SUCCESS] "
checkTestJson                                                                   \
  MASTERLOG_REPORT_TEST                                                         \
  "Ensure masterlog reports test success"                                       \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['basic']['success']"                                                        \
  True
result=$?


checkTestJson                                                                   \
  MASTERLOG_REPORT_STEP                                                         \
  "Ensure masterlog reports step success"                                       \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['basic']['steps']['step']['success']"                                       \
  True
result=$?

justify "<" "*" 100 "-->[MAIN STDOUT FOR TEST SUCCESS] "
checkTestBetween                                                                \
  MAIN_STDOUT_ROOTDIR                                                           \
  "Root dir is set correctly"                                                   \
  0 $result                                                                     \
  $redirect                                                                     \
  "Root directory is : $CURRENT_SOURCE_DIR"                                     \
  "Using Python"                                                                \
  "Preparing working directory"
result=$?


checkTest                                                                       \
  MAIN_STDOUT_ONETEST                                                           \
  "Only one test is in queue"                                                   \
  0 $result                                                                     \
  $redirect                                                                     \
  "Spawning process pool of size [0-9]+ to perform 1 tests"
result=$?


checkTestBetween                                                                \
  MAIN_STDOUT_TEST_REPORTS_SUCCESS                                              \
  "Test reports success at correct time"                                        \
  0 $result                                                                     \
  $redirect                                                                     \
  "\[SUCCESS\] : Test basic reported success"                                   \
  "Waiting for tests to complete"                                               \
  "Test suite complete"
result=$?

checkTestLastLine                                                               \
  MAIN_STDOUT_PASS_LASTLINE                                                     \
  "Suite reports success as last line"                                           \
  0 $result                                                                     \
  $redirect                                                                     \
  "\[SUCCESS\] : All tests passed"
result=$?

justify "<" "*" 100 "-->[TEST STDOUT FOR TEST SUCCESS] "
checkTest                                                                       \
  TEST_STDOUT_CORRECT_TEST                                                      \
  "Correct test run"                                                            \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "\[test::basic\][ ]*Preparing working directory"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR                                                           \
  "Root dir is set correctly"                                                   \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "Root directory is : $CURRENT_SOURCE_DIR"                                     \
  "\[file::00_vs_submitOptions\]"                                               \
  "Preparing working directory"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR_AT_TEST                                                   \
  "Root dir is the same at the test level"                                      \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "Root directory is : $CURRENT_SOURCE_DIR"                                     \
  "\[test::basic\][ ]*Preparing working directory"                              \
  "\[test::basic\][ ]*Checking if results wait is required"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR_AT_STEP                                                   \
  "Root dir is the same at the step level"                                      \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "Root directory is : $CURRENT_SOURCE_DIR"                                     \
  "\[step::step\][ ]*Preparing working directory"                               \
  "\[step::step\][ ]*Submitting step step"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_STEP_REDIRECT                                                     \
  "Step stdout is redirected"                                                   \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "Local step will be redirected to logfile"                                    \
  "\[step::step\].*START step"                                                  \
  "\[step::step\].*STOP step"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_STEP_REPORTS_SUCCESS                                              \
  "Step reports success at correct time"                                        \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "\[step::step\][ ]*\[SUCCESS\]"                                               \
  "\[step::step\][ ]*Results for step"                                          \
  "\[test::basic\][ ]*Writing relevant logfiles"
result=$?

checkTestLastLine                                                               \
  TEST_STDOUT_PASS_LASTLINE                                                     \
  "Test reports success as last line"                                           \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/basic_stdout.log                                          \
  "\[test::basic\][ ]*\[SUCCESS\] : Test basic completed successfully"
result=$?


justify "<" "*" 100 "-->[STEP STDOUT FOR STEP SUCCESS] "
checkTest                                                                       \
  STEP_STDOUT_CORRECT_STEP                                                      \
  "Correct step run"                                                            \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.basic.step.log                        \
  "arg0 arg1"
result=$?

checkTestLastLine                                                               \
  STEP_STDOUT_PASS_LASTLINE                                                     \
  "Step reports success as last line"                                           \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.basic.step.log                        \
  "TEST .* PASS"
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log


justify "^" "*" 100 "->[NEGATIVE TESTS]<-"

# Run again, but negative tests cases
redirect=$( mktemp $CURRENT_SOURCE_DIR/test_XXXX )
$CURRENT_SOURCE_DIR/../../.ci/runner.py $CURRENT_SOURCE_DIR/00_vs_submitOptions.json -t basic-fail > $redirect 2>&1
shouldFail=$?
justify "<" "*" 100 "-->[SUITE FAILS OK] "
reportTest                                                                      \
  SUITE_FAILURE                                                                 \
  "Suite should report failure when step fails in a test"                       \
  1 $result $shouldFail


justify "<" "*" 100 "-->[MASTERLOG FAILURE] "
checkTestJson                                                                   \
  MASTERLOG_REPORT_TEST                                                         \
  "Ensure masterlog reports test failure"                                       \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['basic-fail']['success']"                                                   \
  False
result=$?


checkTestJson                                                                   \
  MASTERLOG_REPORT_STEP                                                         \
  "Ensure masterlog reports step failure"                                       \
  0 $result                                                                     \
  $CURRENT_SOURCE_DIR/00_vs_submitOptions.log                                   \
  "['basic-fail']['steps']['step']['success']"                                  \
  False
result=$?

justify "<" "*" 100 "-->[MAIN STDOUT FOR TEST FAILURE] "
checkTestBetween                                                                \
  MAIN_STDOUT_REPORTS_NO_SUCCESS                                                \
  "Test does not report success"                                                \
  1 $result                                                                     \
  $redirect                                                                     \
  "\[SUCCESS\] : Test basic reported success"                                   \
  "Waiting for tests to complete"                                               \
  "Test suite complete"
result=$?

checkTestBetween                                                                \
  MAIN_STDOUT_TEST_REPORTS_FAILURE                                              \
  "Test reports failure at correct time"                                        \
  1 $result                                                                     \
  $redirect                                                                     \
  "\[FAILURE\] : Test basic reported failure"                                   \
  "Waiting for tests to complete"                                               \
  "Test suite complete"
result=$?

checkTestLastLine                                                               \
  MAIN_STDOUT_NO_PASS_LASTLINE                                                  \
  "Suite does not report success as last line"                                  \
  1 $result                                                                     \
  $redirect                                                                     \
  "\[SUCCESS\] : All tests passed"
result=$?

checkTestLastLine                                                               \
  MAIN_STDOUT_FAIL_LASTLINE                                                     \
  "Suite reports failure as last line"                                          \
  0 $result                                                                     \
  $redirect                                                                     \
  "\[FAILURE\] : Tests \[.*\] failed"
result=$?

# Cleanup run
rm $redirect
rm $CURRENT_SOURCE_DIR/*.log

exit $result
