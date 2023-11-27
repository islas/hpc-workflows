#!/bin/sh
helper_result=$1
helper_suiteStdout=$2
helper_testnames="$3"
helper_suitePass=$4
helper_testsPass=$5

SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )
. $SOURCE_DIR/helpers.sh
. $SOURCE_DIR/checkers.sh

if [ "$helper_suitePass" = true ]; then
  justify "<" "*" 100 "-->[MAIN STDOUT SUCCESS] "

  checkTestLastLine                                                               \
    MAIN_STDOUT_PASS_LASTLINE                                                     \
    "Suite reports success as last line"                                          \
    0 $helper_result                                                              \
    $helper_suiteStdout                                                           \
    "\[SUCCESS\] : All tests passed"
  helper_result=$?
else
  justify "<" "*" 100 "-->[MAIN STDOUT FAILURE] "
  
  checkTestLastLine                                                               \
    MAIN_STDOUT_NO_PASS_LASTLINE                                                  \
    "Suite does not report success as last line"                                  \
    1 $helper_result                                                              \
    $helper_suiteStdout                                                           \
    "\[SUCCESS\] : All tests passed"
  helper_result=$?

  checkTestLastLine                                                               \
    MAIN_STDOUT_FAIL_LASTLINE                                                     \
    "Suite reports failure as last line"                                          \
    0 $helper_result                                                              \
    $helper_suiteStdout                                                           \
    "\[FAILURE\] : Tests \[.*\] failed"
  helper_result=$?
fi

for helper_testname in $helper_testnames; do
  if [ "$helper_testsPass" = true ]; then
    justify "<" "*" 100 "-->[MAIN STDOUT TEST SUCCESS] "

    checkTestBetween                                                                \
      MAIN_STDOUT_TEST_REPORTS_SUCCESS                                              \
      "Test [$helper_testname] reports success at correct time"                     \
      0 $helper_result                                                              \
      $helper_suiteStdout                                                           \
      "\[SUCCESS\] : Test $helper_testname reported success"                        \
      "Waiting for tests to complete"                                               \
      "Test suite complete"
    helper_result=$?
  else
    justify "<" "*" 100 "-->[MAIN STDOUT TEST FAILURE] "

    checkTestBetween                                                                \
      MAIN_STDOUT_REPORTS_NO_SUCCESS                                                \
      "Test [$helper_testname] does not report success"                             \
      1 $helper_result                                                              \
      $helper_suiteStdout                                                           \
      "\[SUCCESS\] : Test $helper_testname reported success"                        \
      "Waiting for tests to complete"                                               \
      "Test suite complete"
    helper_result=$?

    checkTestBetween                                                                \
      MAIN_STDOUT_TEST_REPORTS_FAILURE                                              \
      "Test [$helper_testname] reports failure at correct time"                     \
      0 $helper_result                                                              \
      $helper_suiteStdout                                                           \
      "\[FAILURE\] : Test $helper_testname reported failure"                        \
      "Waiting for tests to complete"                                               \
      "Test suite complete"
    helper_result=$?

  fi
done

exit $helper_result