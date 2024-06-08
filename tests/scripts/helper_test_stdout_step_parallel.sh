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

justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT STEP PARALLEL PHASE] "

helper_steps=$( getKeys "$helper_mapping" )
for helper_step in $helper_steps; do

  helper_stepEndLine=$( getLine $helper_testStdout_loc                                                        \
                          "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Finished submitting step $helper_step" | awk -F ':' '{print $1}' )

  helper_stepsParallel=$( splitValues $( getValuesAtKey "$helper_mapping" $helper_step ) )
  if [ -n "$helper_stepsParallel" ]; then
    justify "<" "*" 100 "-->[STEP [$helper_step] PARALLEL STEPS] "

    helper_stepParStartLine=9999999
    helper_stepParIdx=0
    for helper_stepPar in $helper_stepsParallel; do
      # Check that the stepPar starts before our step even finishes
      helper_stepParStartLine=$( getLineBetween $helper_testStdout_loc                                                        \
                                "\[step::$helper_suite.$helper_testname.$helper_stepPar\][ ]*Submitting step $helper_stepPar"   \
                                "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Submitting step $helper_step"         \
                                "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Finished submitting step $helper_step" | awk '{print $1}' )

      test $helper_stepEndLine -gt $helper_stepParStartLine
      reportTest                                                           \
        TEST_STDOUT_STEP_PARALLEL_$helper_stepParIdx                      \
        "Parallel step [$helper_stepPar] starts before [$helper_step] finishes"  \
        0 $helper_result $?
      helper_result=$?

      # Set new index
      helper_stepParIdx=$(( $helper_stepParIdx + 1 ))
    done
  else
    justify "<" "*" 100 "-->[STEP [$helper_step] SERIAL STEP] "
    # This step has no parallel steps, it should look like it runs serially aside from already running jobs printing
    # We can do this check like this since the code ensures locking printing to the console whilst a job
    # is preparing to submit and only relinquishes the lock between START/STOP phase
    checkTestBetween                                                                \
      TEST_STDOUT_STEP_NO_PARALLEL                                                  \
      "Step [$helper_step] has no parallel steps and should not have any steps submit while running" \
      1 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "\[step::.*\][ ]*Submitting step"                                \
      "\[step::$helper_suite.$helper_testname.$helper_step\].*START $helper_step"         \
      "\[step::$helper_suite.$helper_testname.$helper_step\].*STOP $helper_step"
    helper_result=$?
  fi
done

exit $helper_result