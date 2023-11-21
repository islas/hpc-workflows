#!/bin/sh
check()
{
  # Very simple
  func_filename="$1"
  func_regex="$2"
  grep -Esq "$func_regex" "$func_filename"
  return $?
}

checkBetween()
{
  func_filename="$1"
  func_regex="$2"
  func_pat1="$3"
  func_pat2="$4"
  # Check that func_pat1 and func_pat2 exist
  if [ $( grep -Esc "${func_pat1}" "$func_filename" ) -gt 0 ] && [ $( grep -Esc "${func_pat2}" "$func_filename" ) -gt 0 ]; then
    # https://stackoverflow.com/a/38972737
    awk '/'"${func_pat1}"'/,/'"${func_pat2}"'/' "$func_filename" | grep -Eq "$func_regex" "$func_filename"
    return $?
  else
    return 1
  fi
}

checkLastLine()
{
  func_filename="$1"
  func_regex="$2"
  tail -n 1 "$func_filename" | grep -Eq "$func_regex" 
  return $?
}

checkJson()
{
  func_filename="$1"
  func_location="$2"
  func_expect="$3"
  func_value=$( python3 -c "import json; checkDict=json.load( open( '$func_filename', 'r' ) ); print( checkDict$func_location )" 2>&1 )
  if [ "$func_value" = "$func_expect" ]; then
    return 0
  else
    return 1
  fi
}

filterLines()
{
  func_filename="$1"
  func_matchLines="$2"
  func_tmpfile=$( mktemp test_XXXX )
  sed -n -e "s@\(${func_matchLines}.*\)@\1@p" > $func_tmpfile

  echo $func_tmpfile
}

reportResult()
{
  func_mostRecent=$1
  func_previous=$2
  func_expectRes=$3
  if [ $func_mostRecent -eq $func_expectRes ]; then
    echo "  SUCCESS"
  else 
    echo "X FAILURE"
  fi

  if [ $func_mostRecent -eq $func_expectRes ] && [ $func_previous -eq 0 ]; then
    return 0
  else
    return 1
  fi
}


reportTest()
{
  func_testname="$1"
  func_testdesc="$2"
  func_expectRes="$3"
  func_previousResult=$4
  func_result=$5
  func_report=$( reportResult $func_result $func_previousResult $func_expectRes )
  func_totalResult=$?
  printf "%-12s%-36s%s\n" "$func_report" "$func_testname" "$func_testdesc"
  return $func_totalResult
}

checkTest()
{
  func_testname="$1"
  func_testdesc="$2"
  func_expectRes=$3
  func_previousResult=$4
  func_filename="$5"
  func_regex="$6"

  check "$func_filename" "$func_regex"
  reportTest $func_testname "$func_testdesc" $func_expectRes $func_previousResult $?
  func_result=$?
  return $func_result
}

checkTestBetween()
{
  func_testname="$1"
  func_testdesc="$2"
  func_expectRes=$3
  func_previousResult=$4
  func_filename="$5"
  func_regex="$6"
  func_pat1="$7"
  func_pat2="$8"

  checkBetween "$func_filename" "$func_regex" "$func_pat1" "$func_pat2"
  reportTest $func_testname "$func_testdesc" $func_expectRes $func_previousResult $?
  func_result=$?
  return $func_result
}

checkTestLastLine()
{
  func_testname="$1"
  func_testdesc="$2"
  func_expectRes=$3
  func_previousResult=$4
  func_filename="$5"
  func_regex="$6"

  checkLastLine "$func_filename" "$func_regex"
  reportTest $func_testname "$func_testdesc" $func_expectRes $func_previousResult $?
  func_result=$?
  return $func_result
}

checkTestJson()
{
  func_testname="$1"
  func_testdesc="$2"
  func_expectRes=$3
  func_previousResult=$4
  func_filename="$5"
  func_location="$6"
  func_expect="$7"

  checkJson "$func_filename" "$func_location" "$func_expect"
  reportTest $func_testname "$func_testdesc" $func_expectRes $func_previousResult $?
  func_result=$?
  return $func_result
}