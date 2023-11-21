#!/bin/sh
result=$1
logdir=$2
testname=$3
stepnames=$4

testStdout_loc=$( format $testStdout_fmt logdir=$logdir suite=$suite testname=$testname )

justify "<" "*" 100 "-->[TEST [$testname] STDOUT] "
checkTest                                                                       \
  TEST_STDOUT_CORRECT_TEST                                                      \
  "Correct test run"                                                            \
  0 $result                                                                     \
  $testStdout_loc                                                               \
  "\[test::$testname\][ ]*Preparing working directory"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR                                                           \
  "Root dir is set correctly"                                                   \
  0 $result                                                                     \
  $testStdout_loc                                                               \
  "Running from root directory $logdir"                                         \
  "\[file::\w+\]"                                                               \
  "Preparing working directory"
result=$?

checkTestBetween                                                                \
  TEST_STDOUT_ROOTDIR_AT_TEST                                                   \
  "Root dir is the same at the test level for test [$testname]"                 \
  0 $result                                                                     \
  $testStdout_loc                                                               \
  "Running from root directory $rootDir"                                        \
  "\[test::$testname\][ ]*Preparing working directory"                          \
  "\[test::$testname\][ ]*Checking if results wait is required"
result=$?

for step in $stepnames; do
  stepStdout_loc=$( format $stepStdout_fmt logdir=$logdir suite=$suite testname=$testname step=$step )
  checkTestBetween                                                                \
    TEST_STDOUT_ROOTDIR_AT_STEP                                                   \
    "Root dir is the same at the step level for step [$step]"                     \
    0 $result                                                                     \
    $testStdout_loc                                                               \
    "Running from root directory $logdir"                                         \
    "\[step::$step\][ ]*Preparing working directory"                              \
    "\[step::$step\][ ]*Submitting step $step"
  result=$?

  checkTestBetween                                                                \
    TEST_STDOUT_STEP_REDIRECT                                                     \
    "Step stdout is redirected for step [$step]"                                  \
    0 $result                                                                     \
    $testStdout_loc                                                               \
    "Local step will be redirected to logfile $stepStdout_loc"                    \
    "\[step::$step\].*START $step"                                                \
    "\[step::$step\].*STOP $step"
  result=$?
done

return $result