#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_mapping="$5"

SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )
. $SOURCE_DIR/helpers.sh
. $SOURCE_DIR/checkers.sh

helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )

justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT STEP DEPENDENCY ORDER] "

helper_steps=$( getKeys "$helper_mapping" )
for helper_step in $helper_steps; do

  helper_stepStartLine=$( getLine $helper_testStdout_loc                                                        \
                          "\[step::$helper_step\][ ]*Preparing working directory" | awk -F ':' '{print $1}' )

  helper_stepDependencies=$( splitValues $( getValuesAtKey "$helper_mapping" $helper_step ) )
  if [ -n "$helper_stepDependencies" ]; then
    justify "<" "*" 100 "-->[STEP [$helper_step] DEPENDENCY ORDER] "

    helper_stepDepEndLine=9999999
    helper_stepDepIdx=0
    for helper_stepDep in $helper_stepDependencies; do
      # Check that the stepDep finishes before our step even starts
      helper_stepDepEndLine=$( getLine $helper_testStdout_loc                                                        \
                                  "\[step::$helper_stepDep\][ ]*Finished submitting step $helper_stepDep" | awk -F ':' '{print $1}' )
      test $helper_stepStartLine -gt $helper_stepDepEndLine
      reportTest                                                           \
        TEST_STDOUT_STEP_ORDER_DEP_$helper_stepDepIdx                      \
        "Dependency [$helper_stepDep] finishes before [$helper_step] starts"   \
        0 $helper_result $?
      helper_result=$?

      # Set new index
      helper_stepDepIdx=$(( $helper_stepDepIdx + 1 ))
    done
  else
    # This step has no dependencies, it should start whenever but before the test is done (obviously)
    checkTestBetween                                                                \
      TEST_STDOUT_STEP_NO_DEPENDENCIES                                              \
      "Step [$helper_step] has no dependencies and need only finish by test end"    \
      0 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "\[step::$helper_step\][ ]*Finished submitting step $helper_step"             \
      "\[test::$helper_testname\][ ]*Preparing working directory"                   \
      "\[test::$helper_testname\][ ]*No remaining steps, test submission complete"
    helper_result=$?
  fi
done

exit $helper_result