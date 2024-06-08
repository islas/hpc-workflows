#!/bin/sh
helper_result=$1
helper_logdir=$2
helper_suite=$3
helper_testname=$4
helper_step=$5
helper_mapping="$6"
helper_mappingOrigin="$7"
helper_argpackExist="$8"

SOURCE_DIR=$( CDPATH= cd -- "$(dirname -- "$0")" && pwd )
. $SOURCE_DIR/helpers.sh
. $SOURCE_DIR/checkers.sh

helper_testStdout_loc=$( format $testStdout_fmt logdir=$helper_logdir suite=$helper_suite testname=$helper_testname )

justify "<" "*" 100 "-->[TEST [$helper_testname] STDOUT ARGPACKS] "

helper_argpacks=$( getKeys "$helper_mapping" )
helper_argpackLine=0
helper_argpackIdx=0
for helper_argpack in $helper_argpacks; do
  helper_argpack_formatted=$( getValuesAtKey "$helper_mapping" $helper_argpack | sed "s/,/, /" )
  helper_argpack_origin=$( getValuesAtKey "$helper_mappingOrigin" $helper_argpack )

  if [ "$helper_argpackExist" = false ]; then
    checkTestBetween                                                                \
      TEST_STDOUT_NO_ARGPACK_AT_STEP                                                \
      "Argpack $helper_argpack is not injected into step [$helper_step] regardless of value or origin" \
      1 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "From .*[ ]*adding arguments pack '$helper_argpack'"                          \
      "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Submitting step $helper_step"                      \
      "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Running command:"
    helper_result=$?
  else
    checkTestBetween                                                                \
      TEST_STDOUT_ARGPACK_AT_STEP                                                   \
      "Argpack $helper_argpack is injected into step [$helper_step] from $helper_argpack_origin as value $helper_argpack_formatted"        \
      0 $helper_result                                                              \
      $helper_testStdout_loc                                                        \
      "From $helper_argpack_origin[ ]*adding arguments pack '$helper_argpack'[ ]*: $helper_argpack_formatted" \
      "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Submitting step $helper_step"                      \
      "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Running command:"
    helper_result=$?

    # Find line where argpack occurs - we don't need to aggregate result just yet since the above check
    # verifies the pattern
    helper_argpackCurrLine=$( getLineBetween $helper_testStdout_loc                                                        \
                                "From $helper_argpack_origin[ ]*adding arguments pack '$helper_argpack'[ ]*: $helper_argpack_formatted" \
                                "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Submitting step $helper_step"                      \
                                "\[step::$helper_suite.$helper_testname.$helper_step\][ ]*Running command:" | awk '{print $1}' )
    test $helper_argpackCurrLine -gt $helper_argpackLine
    reportTest                                                                      \
      TEST_STDOUT_ARGPACK_ORDER_IDX_$helper_argpackIdx                              \
      "Argpack $helper_argpack appears at index $helper_argpackIdx"                 \
      0 $helper_result $?
    helper_result=$?

    # Set new index and last line number found
    helper_argpackLine=$helper_argpackCurrLine
    helper_argpackIdx=$(( $helper_argpackIdx + 1 ))
  fi
done

exit $helper_result