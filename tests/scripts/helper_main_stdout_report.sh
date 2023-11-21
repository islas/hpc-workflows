#!/bin/sh
result=$1
suiteStdout=$2
testnames="$3"
suitePass=$4
testsPass=$5

if [ "$suitePass" = true ]; then
  justify "<" "*" 100 "-->[MAIN STDOUT SUCCESS] "

  checkTestLastLine                                                               \
    MAIN_STDOUT_PASS_LASTLINE                                                     \
    "Suite reports success as last line"                                          \
    0 $result                                                                     \
    $suiteStdout                                                                  \
    "\[SUCCESS\] : All tests passed"
  result=$?
else
  justify "<" "*" 100 "-->[MAIN STDOUT FAILURE] "
  
  checkTestLastLine                                                               \
    MAIN_STDOUT_NO_PASS_LASTLINE                                                  \
    "Suite does not report success as last line"                                  \
    1 $result                                                                     \
    $suiteStdout                                                                  \
    "\[SUCCESS\] : All tests passed"
  result=$?

  checkTestLastLine                                                               \
    MAIN_STDOUT_FAIL_LASTLINE                                                     \
    "Suite reports failure as last line"                                          \
    0 $result                                                                     \
    $suiteStdout                                                                  \
    "\[FAILURE\] : Tests \[.*\] failed"
  result=$?
fi

for testname in $testnames; do
  if [ "$testsPass" = true ]; then
    justify "<" "*" 100 "-->[MAIN STDOUT TEST SUCCESS] "

    checkTestBetween                                                                \
      MAIN_STDOUT_TEST_REPORTS_SUCCESS                                              \
      "Test reports success at correct time"                                        \
      0 $result                                                                     \
      $suiteStdout                                                                  \
      "\[SUCCESS\] : Test $testname reported success"                               \
      "Waiting for tests to complete"                                               \
      "Test suite complete"
    result=$?
  else
    justify "<" "*" 100 "-->[MAIN STDOUT TEST FAILURE] "

    checkTestBetween                                                                \
      MAIN_STDOUT_REPORTS_NO_SUCCESS                                                \
      "Test does not report success"                                                \
      1 $result                                                                     \
      $suiteStdout                                                                  \
      "\[SUCCESS\] : Test $testname reported success"                               \
      "Waiting for tests to complete"                                               \
      "Test suite complete"
    result=$?

    checkTestBetween                                                                \
      MAIN_STDOUT_TEST_REPORTS_FAILURE                                              \
      "Test reports failure at correct time"                                        \
      0 $result                                                                     \
      $suiteStdout                                                                  \
      "\[FAILURE\] : Test $testname reported failure"                               \
      "Waiting for tests to complete"                                               \
      "Test suite complete"
    result=$?

  fi
done

return $result