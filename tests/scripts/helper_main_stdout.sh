#!/bin/sh
result=$1
logdir=$2
suiteStdout=$3
numTests=$4

justify "<" "*" 100 "-->[MAIN STDOUT] "
checkTestBetween                                                                \
  MAIN_STDOUT_ROOTDIR                                                           \
  "Root dir is set correctly"                                                   \
  0 $result                                                                     \
  $suiteStdout                                                                  \
  "Root directory is : $logdir"                                                 \
  "Using Python"                                                                \
  "Preparing working directory"
result=$?


checkTest                                                                       \
  MAIN_STDOUT_NUMTESTS                                                          \
  "Only $numTests test(s) in queue"                                             \
  0 $result                                                                     \
  $suiteStdout                                                                  \
  "Spawning process pool of size [0-9]+ to perform $numTests tests"
result=$?

return $result