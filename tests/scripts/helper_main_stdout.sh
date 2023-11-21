#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suiteStdout=$3
helper_numTests=$4

justify "<" "*" 100 "-->[MAIN STDOUT] "
checkTestBetween                                                                \
  MAIN_STDOUT_ROOTDIR                                                           \
  "Root dir is set correctly"                                                   \
  0 $helper_result                                                              \
  $helper_suiteStdout                                                           \
  "Root directory is : $helper_logdir"                                          \
  "Using Python"                                                                \
  "Preparing working directory"
helper_result=$?


checkTest                                                                       \
  MAIN_STDOUT_NUMTESTS                                                          \
  "Only $helper_numTests test(s) in queue"                                      \
  0 $helper_result                                                              \
  $helper_suiteStdout                                                           \
  "Spawning process pool of size [0-9]+ to perform $helper_numTests tests"
helper_result=$?

return $helper_result