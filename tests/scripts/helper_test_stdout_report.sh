#!/bin/sh
result=$1
logdir=$2

suite=$3
testname=$4
testPass=$5
mapping="$6"

testStdout_loc=$( format $testStdout_fmt logdir=$logdir suite=$suite testname=$testname )


if [ "$testPass" = true ]; then
  justify "<" "*" 100 "-->[TEST [$testname] STDOUT SUCCESS] "
  checkTestLastLine                                                               \
    TEST_STDOUT_PASS_LASTLINE                                                     \
    "Test reports success as last line"                                           \
    0 $result                                                                     \
    $testStdout_loc                                                               \
    "\[test::$testname\][ ]*\[SUCCESS\] : Test $testname completed successfully"
  result=$?
else
  justify "<" "*" 100 "-->[TEST [$testname] STDOUT FAILURE] "
  checkTestLastLine                                                               \
    TEST_STDOUT_FAIL_LASTLINE                                                     \
    "Test reports failure as last line"                                           \
    0 $result                                                                     \
    $testStdout_loc                                                               \
    "\[test::$testname\][ ]*\[FAILURE\] : Steps \[ .* \] failed"
  result=$?
fi


steps=$( getKeys "$mapping" )
for step in $steps; do

  if [ "$( getValuesAtKey "$mapping" $step )" = true ]; then
    checkTestBetween                                                                \
      TEST_STDOUT_STEP_REPORTS_SUCCESS                                              \
      "Step [$step] reports success at correct time"                                \
      0 $result                                                                     \
      $testStdout_loc                                                               \
      "\[step::$step\][ ]*\[SUCCESS\]"                                              \
      "\[step::$step\][ ]*Results for $step"                                        \
      "\[test::$testname\][ ]*Writing relevant logfiles"
    result=$?
  else

    checkTestBetween                                                                \
      TEST_STDOUT_STEP_REPORTS_FAILURE                                              \
      "Step [$step] reports failure at correct time"                                \
      0 $result                                                                     \
      $testStdout_loc                                                               \
      "\[step::$step\][ ]*\[FAILURE\]"                                              \
      "\[step::$step\][ ]*Results for $step"                                        \
      "\[test::$testname\][ ]*Writing relevant logfiles"
    result=$?

    checkTestBetween                                                                \
      TEST_STDOUT_STEP_REPORTS_LASTLINE                                             \
      "Step [$step] reports lastline reason for failure"                            \
      0 $result                                                                     \
      $testStdout_loc                                                               \
      "\[step::$step\][ ]*Line: \".*\""                                             \
      "\[step::$step\][ ]*\[FAILURE\] : Missing key"                                \
      "\[step::$step\][ ]*.*ERROR ERROR ERROR"
    result=$?

  fi
done

return $result