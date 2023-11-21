#!/bin/sh
result=$1
logdir=$2
suite=$3
testname=$4
step=$5
expected="$6"
pass=$7

stepStdout_loc=$( format $stepStdout_fmt logdir=$logdir suite=$suite testname=$testname step=$step )



justify "<" "*" 100 "-->[STEP [$step] STDOUT] "
checkTest                                                                       \
  STEP_STDOUT_CORRECT_STEP                                                      \
  "Correct step run"                                                            \
  0 $result                                                                     \
  $stepStdout_loc                                                               \
  "$expected"
result=$?

if [ "$pass" = true ]; then
  checkTestLastLine                                                               \
    STEP_STDOUT_PASS_LASTLINE                                                     \
    "Step reports success as last line"                                           \
    0 $result                                                                     \
    $stepStdout_loc                                                               \
    "TEST .* PASS"
  result=$?
else
  checkTestLastLine                                                               \
  STEP_STDOUT_FAIL_LASTLINE                                                       \
  "Step does not have last line pass marker"                                      \
  1 $result                                                                       \
  $stepStdout_loc                                                                 \
  "TEST .* PASS"
  result=$?
fi

return $result