#!/usr/bin/env python3
import sys
import json
import os
import copy
import argparse
import inspect
import socket

from collections import OrderedDict
from multiprocessing import Pool
from contextlib import redirect_stdout
from datetime import timedelta


import SubmitCommon as sc

from SubmitAction   import SubmitAction
from SubmitOptions  import SubmitOptions
from SubmitArgpacks import SubmitArgpacks
from Test           import Test
from Step           import Step
from HpcArgpacks    import HpcArgpacks




ABS_FILEPATH = os.path.realpath( __file__ )

class Suite( SubmitAction ) :

  AUTO_REDIRECT_TEMPLATE = "{root}/{test}_stdout.log"

  def scope( self ) :
    return "file"

  def __init__( self, name, options, defaultSubmitOptions, globalOpts, parent = "", rootDir = "./" ) :
    self.tests_       = {}
    self.testsStatus_ = {}

    super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )

    self.metadata_   =  {
                          "rel_file"     : os.path.relpath( self.globalOpts_.testsConfig, start=self.rootDir_ ),
                          "rel_offset"   : self.globalOpts_.dirOffset
                        }

    self.log( "Root directory is : {0}".format( self.rootDir_ ) )


  def parseSpecificOptions( self ) :
    for test, testDict in self.options_.items() :
      if test != "submit_options" :
        self.tests_[ test ] = Test( test, testDict, self.submitOptions_, self.globalOpts_, parent=self.ancestry(), rootDir=self.rootDir_ )

    return [] # all keys are valid

  # Take immediate test return and output what happened
  def reportErrs( self, test, testLog ) :
    if testLog["success"] :
      self.log( "{succ} : Test {test} reported success".format( succ=SubmitAction.SUCCESS_STR, test=test ) )
    else :
      self.log( "{fail} : Test {test} reported failure".format( fail=SubmitAction.FAILURE_STR, test=test ) )
    
    return not testLog["success"]

  # On test complete, store status for later use
  def testComplete( self, status ) :
    # Status should be a 3-elem tuple with pass/fail in 0 and 1 test name in 1, and 1 logfile in 2    
    self.testsStatus_[ status[1][0] ] = {}
    self.testsStatus_[ status[1][0] ][ "success" ] = status[0]
    self.testsStatus_[ status[1][0] ][ "logfile" ] = status[2][0]
    self.reportErrs( status[1][0], self.testsStatus_[ status[1][0] ] )

  # Something happened, unsure if this is even recoverable, my guess is not
  def testError( self, e ) :
    self.log( "{fail} : Unknown test failed with exception '{err}'".format( fail=SubmitAction.FAILURE_STR, err=str(e) ) )
    print( e )
    exit( 1 )
  
  ##############################################################################
  #
  # Run multitest on a joint HPC submission
  # This is complex and implies joining relevant resources across all listed tests
  # and submitting it as one single step to be run under the hood on the HPC node
  # as a multitest. 75% of this function is just wrangling those numbers and creating
  # the appropriate step/test and logs for results.
  #
  ##############################################################################
  def runHPCJoin( self, tests ) :

    self.log( "Computing maximum HPC resources of tests..." )
    # All steps must have the same submission type
    hpcSubmit = [ step.submitOptions_.submitType_ for test in tests for step in self.tests_[ test ].steps_.values() if step.submitOptions_.submitType_ != sc.SubmissionType.LOCAL ]
    allEqual  = ( not hpcSubmit or hpcSubmit.count( hpcSubmit[0] ) == len( hpcSubmit ) )

    if not allEqual :
      msg = "Error : Cannot join different types of HPC submissions together"
      self.log( msg )
      raise Exception( msg )

    if not hpcSubmit :
      self.log( "No HPC steps in any of these tests" )
      return False, [ "no logfile" ]

    self.log( "Accumulate maximum HPC resources per test..." )
    self.log_push()
    maxResourcesPerTest = {}
    maxTimePerTest      = {}
    for test in tests :
      self.tests_[ test ].log_push()
      maxResourcesPerTest[ test ], maxTimePerTest[ test ] = self.tests_[ test ].getMaxHPCResources()
      self.tests_[ test ].log_pop()
    
    self.log_pop()

    
    longestTest = len( max( tests, key=len ) )
    phase = 0

    # We need to break it down by expected runtime of each test by size of pool
    # as that is the order they will run in. Could we optimize? Yea probably. Will we? Not right now
    self.log( "Calculating expected runtime of tests across {0} workers [pool size]".format( self.globalOpts_.pool ) )
    self.log_push()
    

    psuedoJobs = [ testname for testname in tests ]
    psuedoRunningMap = {}

    maxResources   = HpcArgpacks( OrderedDict() )
    maxResources.setName( "maxlimit" )
    maxTimelimit   = timedelta()
    # Continue while we have jobs in queue or running
    while len( psuedoJobs ) > 0 or len( psuedoRunningMap ) > 0 :
      # If we have slots in our pool and jobs left, fill in
      while len( psuedoRunningMap ) < self.globalOpts_.pool and len( psuedoJobs ) > 0 :
        pjTest = psuedoJobs.pop( 0 )
        psuedoRunningMap[ pjTest ] = { "hpc_arguments" : maxResourcesPerTest[pjTest], "timelimit" : maxTimePerTest[pjTest] }

      # Find smallest job
      runForKey = min( psuedoRunningMap, key= lambda k : psuedoRunningMap[k]["timelimit"] )
      runFor    = copy.deepcopy( psuedoRunningMap[runForKey]["timelimit"] )
      maxTimelimit += runFor
      # "Run" for that amount of time
      self.log( "Simulating threadpool for {0}".format( psuedoRunningMap[runForKey]["timelimit"] ) )
      self.log_push()

      for key in psuedoRunningMap.keys() :
        psuedoRunningMap[ key ][ "timelimit" ] -= runFor

      ##################################################################################################################
      # RESOURCE CALCULATIONS
      # What would our max resource consumption be whilst running this set?
      # Add all concurrent resources together
      currentResources = HpcArgpacks.joinAll( [ pj["hpc_arguments"] for pj in psuedoRunningMap.values() ], hpcSubmit[0], lambda rhs,lhs : rhs + lhs, print=self.log  )

      # Get maximum
      maxResources.join(
                        currentResources,
                        hpcSubmit[0],
                        max,
                        print=self.log
                        )
      self.log( "[PHASE {phase}] Resources for [ {tests} ] : '{res}', timelimit = {time}".format(
                                                                                                  phase=phase,
                                                                                                  tests=",".join(
                                                                                                                "{0:>{1}}".format(
                                                                                                                                  step, longestTest + ( 1 if len( psuedoRunningMap ) > 1 else 0 ) )
                                                                                                                                  for step in psuedoRunningMap.keys()
                                                                                                                ),
                                                                                                  res=currentResources.format( hpcSubmit[0], print=lambda *args : None ),
                                                                                                  time=runFor
                                                                                                  )
                )
      phase += 1
      #
      ##################################################################################################################
    

      # Re-evaluate for any jobs that completed
      completed = []
      for testname in psuedoRunningMap :
        if psuedoRunningMap[ testname ][ "timelimit" ].total_seconds() <= 0 :
          completed.append( testname )

      # Remove completed
      for pj in completed :
        psuedoRunningMap.pop( pj )

      self.log( "{0} jobs completed during this runtime".format( len( completed ) ) )
      self.log_pop()

    # end of simulated runs
    self.log_pop()

    maxTimelimitStr = SubmitOptions.formatTimelimit( maxTimelimit, hpcSubmit[0] )
    self.log( "Maximum calculated resources for running all tests is '{0}'".format( maxResources.format( hpcSubmit[0], print=lambda *args : None ) ) )
    self.log( "Maximum calculated timelimit for running all tests is '{0}'".format( maxTimelimitStr ) )
    ####################################################################################################################



    # Overrides
    if self.globalOpts_.joinHPC :
      overrideResource = self.globalOpts_.joinHPC
      self.log( "Requested override of resources with '{0}'".format( overrideResource ) )
      maxResources.update( HpcArgpacks( json.loads( self.globalOpts_.joinHPC, object_pairs_hook=OrderedDict ), origin="cli" ) )
      self.log( "  New maximum resources for running all tests is '{0}'".format( maxResources.format( hpcSubmit[0], print=lambda *args : None ) ) )


    self.log_pop()

    ####################################################################################################################
    # reconstruct cli arguments
    posArgs = {}
    optArgs = {}
    hpcJoinOpts = copy.deepcopy( self.globalOpts_ )
    # Overwrite certain options to force running in a particular state
    hpcJoinOpts.joinHPC = None
    hpcJoinOpts.submitType = sc.SubmissionType.LOCAL

    for key, value in vars( hpcJoinOpts ).items() :
      # Do our positional args first
      addTo = optArgs
      if key in [ "testsConfig" ] :
        addTo = posArgs

      # Skip all false and None as we have those as defaults
      if value :
        if isinstance( value, list ) :
          addTo[ key ] = value
        elif isinstance( value, bool ) :
          # As long as we are diligent about action=store_const (True) this will work
          addTo[ key ] = None
        else :
          # Just as str
          addTo[ key ] = str( value )

    args = []
    args.extend( posArgs.values() )
    for k,v in optArgs.items() :
      args.append( "--{opt}".format( opt=k ) )
      if v :
        if isinstance( v, list ) :
          args.extend( list( map( str, v ) ) )
        else :
          args.append( "{val}".format( val=v ) )
    ####################################################################################################################
    # Construct and run

    self.log( "Using current file as launch executable : " + ABS_FILEPATH )
    stepDict = {
                  "submit_options" : 
                  {
                    "submission" : hpcSubmit[0],
                    "timelimit"  : maxTimelimitStr
                  },
                  "command"   : ABS_FILEPATH,
                  "arguments" : args
                }
    testDict = {
                  "steps" : { "submit" : stepDict }
                }

    # Make our current key check for multitest pass
    self.log( "Setting keyphrase for passing to internally defined one")
    hpcJoinOpts.key = "\[file::(.*?)\][ ]*\[SUCCESS\] : All tests passed"

    # Create the test name if not provided
    joinTestName = self.globalOpts_.joinName
    if joinTestName is None :
      joinTestName = "joinHPC_" + "_".join( tests )
      self.log( "No join name provided, defaulting to '{joinName}'".format( joinName=joinTestName ) )

    hpcJoinTest = Test( joinTestName, testDict, self.submitOptions_, hpcJoinOpts, parent=self.ancestry(), rootDir=self.rootDir_ )
    # No argpacks
    hpcJoinTest.steps_["submit"].submitOptions_.arguments_    = SubmitArgpacks( OrderedDict() )
    hpcJoinTest.steps_["submit"].submitOptions_.hpcArguments_ = maxResources
    # No other args
    hpcJoinTest.steps_["submit"].addTestScriptArgs_ = False

    hpcJoinTest.validate()
    success = hpcJoinTest.run()

    ####################################################################################################################
    # Custom wait if requested

    self.log( "Joined HPC tests complete, above success only means tests managed to complete, please see logs for per-test success" )
    success = True

    if not self.globalOpts_.nopost :
      self.log( "Post-processing all test results..." )        
      if self.globalOpts_.dryRun :
        self.log( "Doing dry-run, assumed success" )
      else :
        # Because we submit to the exact same spot with same args, our logfile is already written out :)
        # Our "stdout" will be :
        testSuiteOutput = hpcJoinTest.steps_["submit"].logfile_
        self.log( "Joined HPC test output is : " )
        self.log( "*" *42 )
        print( open( testSuiteOutput, "r" ).read() )
        self.log( "*" *42 )

        testSuiteLogs = {}
        with open( self.logfile_, "r" ) as hpcSuiteLog :
          testSuiteLogs = json.load( hpcSuiteLog, object_pairs_hook=OrderedDict )
        
        metadata = testSuiteLogs.pop( "metadata" )
        success = True
        for test, testLog in testSuiteLogs.items() :

          testErr = self.reportErrs( test, testLog )
          success = success and not testErr

          if testErr :
            self.log_push()
            self.log( "Test output can be found at : " )
            self.log_push()
            self.log( testLog[ "stdout" ] )
            self.log_pop()
            self.tests_[ test ].reportErrs( testLog[ "steps" ], simple=True )

        return success, [ testLog["logfile"] for testLog in testSuiteLogs.values() ]

    # No logfiles to return
    return success, [ hpcJoinTest.logfile_ ]
  
  ##############################################################################
  #
  # Run multiple tests from the suite
  # This is the main workhorse function of multitests, creating a worker pool of 
  # processes and running the exact same suite but with modified CLI options to avoid
  # specialty calling that differs from what a user might be able to do
  # Create a hierarchical logs-point-to-logs for suite->tests->steps to effectively
  # give back results
  #
  ##############################################################################
  def runMultitest( self, tests ) :
    self.log( "Preparing to run multiple tests" )
    self.log_push()
    # Generate all options for tests
    # First deep copy
    individualTestOpts = [ copy.deepcopy( self.globalOpts_ ) for i in range( len( tests ) ) ]
    # Then apply individual tests to specific options
    for testIdx, opt in enumerate( individualTestOpts ) :
      opt.tests       = [tests[testIdx]]
      opt.redirect    = Suite.AUTO_REDIRECT_TEMPLATE.format( root=self.rootDir_, test=tests[testIdx] )
      opt.forceSingle = True
      self.log( "Automatically redirecting {0} to {1}".format(  opt.tests[0], opt.redirect ) )


    if self.globalOpts_.altdirs is not None :
      self.log( "Requested mapping tests to alternate directories" )
      self.log( "Relative path to test config to use in alt directories : " + self.metadata_[ "rel_file" ] )
      testDirs      = []
      if len( self.globalOpts_.altdirs ) != len( tests ) :
        self.log( "Alternate directories not provided or amount less than number of tests, naming automatically" )
        testDirs = [ test for test in tests ]
      else :
        self.log( "Alternate directories provided will be mapped in order to test order" )
        testDirs = [ altdir for altdir in self.globalOpts_.altdirs ]

      for testIdx, opt in enumerate( individualTestOpts ) :
        opt.testsConfig = testDirs[testIdx] + "/" + os.path.basename( self.globalOpts_.testsConfig )

    self.log_pop()

    self.log( "Spawning process pool of size {0} to perform {1} tests".format( self.globalOpts_.pool, len(tests) ) )
    self.log_push()
    results = {}
    with Pool( processes=self.globalOpts_.pool ) as pool :
      for individualTest in individualTestOpts :
        self.log( "Launching test {0}".format( individualTest.tests[0] ) )
        results[individualTest.tests[0]] = pool.apply_async(
                                                            runSuite,
                                                            ( individualTest, ),
                                                            callback=self.testComplete
                                                            )
      
      self.log( "Waiting for tests to complete - BE PATIENT" )

      # When using an error_callback, it hangs, this instead will force quit
      for testname, res in results.items() :
        res.get()

      pool.close()
      pool.join()

    self.log_pop()

    if self.globalOpts_.nopost :
      self.log( "No results post-processing requested, testing complete" )
    else :
      self.log( "Test suite complete, writing test results to master log file : " )
      self.log_push()
      self.log( self.logfile_ )
      self.log_pop()

      # Get all test logs
      testSuiteLogs = { "metadata" : self.metadata_ }
      failedTests   = []
      for testIdx, test in enumerate( tests ) :
        testSuiteLogs[ test ] = {}
        testSuiteLogs[ test ][ "success" ] = self.testsStatus_[ test ][ "success" ]
        testSuiteLogs[ test ][ "logfile" ] = self.testsStatus_[ test ][ "logfile" ]
        # This isn't in the testStatus_ since it doesn't make sense to output that per-test
        testSuiteLogs[ test ][ "stdout"  ] = individualTestOpts[testIdx].redirect
        testSuiteLogs[ test ][ "line"    ] = SubmitAction.getLastLine( individualTestOpts[testIdx].redirect )

        if not self.testsStatus_[ test ][ "success" ] :
          failedTests.append( test )

        stepsLog = None
        with open( testSuiteLogs[ test ]["logfile"], "r" ) as stepsLogfile :
          stepsLog = json.load( stepsLogfile, object_pairs_hook=OrderedDict )
        testSuiteLogs[ test ][ "steps" ] = stepsLog

      with open( self.logfile_, "w" ) as testSuiteLogfile :
        json.dump( testSuiteLogs, testSuiteLogfile, indent=2 )
      
      # Now dump metadata so we can do list comprehension
      testSuiteLogs.pop( "metadata" )
      if failedTests :
        self.log( "{fail} : Tests [ {tests} ] failed".format( fail=SubmitAction.FAILURE_STR, tests=", ".join( failedTests ) ) )
      else :
        self.log( "{succ} : All tests passed".format( succ=SubmitAction.SUCCESS_STR ) )

      return not ( False in [ testLog[ "success"] for testLog in testSuiteLogs.values() ] ), [ testSuiteLogs[ test ][ "logfile" ] for test in tests ]

    # Unsure where all logs will be, maybe probably
    return True, [ self.tests_[ test ].logfile_ for test in tests ]

  # main entry point for testing
  def run( self, tests ) :
    currentDir = os.getcwd()
    self.log( "Storing current working directory [{cwd}]".format( cwd=currentDir ) )
    self.log( "  Will return to this directory at the end of testing" )

    for test in tests :
      if test not in self.tests_.keys() :
        msg = "Error: no test named '{0}'".format( test )
        self.log( msg )
        raise Exception( msg )
      
      self.tests_[test].validate()

    self.setWorkingDirectory()

    # Let joining steps into a single HPC job take precedence
    success = True
    logs    = []
    if self.globalOpts_.forceSingle :
      success = True
      logs    = []
      for test in tests :
        success = success and self.tests_[ test ].run()
        logs.append( self.tests_[ test ].logfile_ )
    else :
      if hasattr( self.globalOpts_, 'joinHPC' ) :
        success, logs = self.runHPCJoin( tests )
      else :
        success, logs = self.runMultitest( tests )
    
    # Popping back to old cwd
    os.chdir( currentDir )
    return success, logs

# A separated helper function to wrap this in a callable format
def runSuite( options ) :
  sc.LABEL_LENGTH = options.labelLength

  opts = SubmitOptions()
  opts.account_    = options.account

  if options.submitType is None :
    # Set default to LOCAL, but do not force
    opts.submitType_ = sc.SubmissionType.LOCAL
  else :
    opts.submitType_         = options.submitType
    opts.lockSubmitType_     = True
    print( "Forcing submission type to {0} for all steps".format( opts.submitType_ ) )
  
  if opts.submitType_ != sc.SubmissionType.LOCAL and opts.account_ is None:
    # We don't have an account && we are not running local
    err = "Error: No account provided for non-local run."
    print( err )
    raise Exception( err )

  if options.inlineLocal and options.threadpool > 1 :
    print( "Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)" )
    options.threadpool = 1

  # Quickly convert to abs path
  options.testsConfig = os.path.abspath( options.testsConfig )

  fp    = open( options.testsConfig, 'r' )
  # Go up one to get repo root - change this if you change the location of this script
  testDir = os.path.dirname( options.testsConfig )
  root  = os.path.abspath( ( testDir if testDir else "." )  + "/" + options.dirOffset )

  # Construct simplified name 
  basename = os.path.splitext( os.path.basename( options.testsConfig ) )[0]

  # Check if a host config was specified to use in lieu of fqdn
  if options.forceFQDN is None :
    # Use fqdn as the default host selection
    options.forceFQDN = socket.getfqdn() 

  success = False
  logs    = []
  # Done at the highest level
  if options.redirect is not None :
    with open( options.redirect, "w" ) as redirect :
      with redirect_stdout( redirect ) :
        testSuite = Suite( 
                          basename,
                          json.load( fp ),
                          opts,
                          options,
                          parent=options.globalPrefix,
                          rootDir=root
                          )
        success, logs = testSuite.run( options.tests )
        # if success and options.message :
        #   print( options.message )
  else :
    testSuite = Suite( 
                          basename,
                          json.load( fp ),
                          opts,
                          options,
                          parent=options.globalPrefix,
                          rootDir=root
                          )
    success, logs = testSuite.run( options.tests )
    # if success and options.message :
    #   print( options.message ) 

  return ( success, options.tests, logs )

def getOptionsParser():
  parser = argparse.ArgumentParser( epilog=inspect.cleandoc("""
                                                            All tests & steps will be run with root dir = <abs path to json> + dirOffset
                                                            Meaning if no [dirOffset] is provided, the root dir from which all working directories
                                                            are evaluated will be from the location of the JSON test suite definition file

                                                            Test & steps will be prefixed with current context, except for
                                                            sections delineated with '***...***' as those will be raw step 
                                                            command output.

                                                            Scripts running from this framework should always take at least one 
                                                            prefix arguments ($1) before any other arguments which will be the 
                                                            working directory that should immediate be cd'ed to.

                                                            Likewise, if a script is submitted to an HPC run (non-LOCAL) and requests automatic
                                                            post-processing, this will always assume failure unless the <KEY PHRASE> is at the end
                                                            of the logfile. Thus, scripts running in this mode should assume the same and only output
                                                            success <KEY PHRASE> when completing successfully AT THE VERY END AS THE LAST LINE.
                                                            """ ),
                                  formatter_class=argparse.RawTextHelpFormatter
                                  )

  parser.add_argument( 
                      "testsConfig",
                      help="JSON file defining set of tests",
                      type=str,
                      default=""
                      )
  parser.add_argument( 
                      "-t", "--tests",
                      help="Test names matching respective JSON test name to run",
                      dest="tests",
                      type=str,
                      nargs="+",
                      default=[]
                      )
  parser.add_argument( 
                      "-s", "--submitType",
                      dest="submitType",
                      help="Override type of submission to use for all steps submitted",
                      type=sc.SubmissionType,
                      choices=list( sc.SubmissionType ),
                      default=None
                      )
  parser.add_argument( 
                      "-a", "--account",
                      dest="account",
                      help="Account to use when submitting to an HPC",
                      type=str,
                      default=None
                      )
  parser.add_argument( 
                      "-d", "--dirOffset",
                      dest="dirOffset",
                      help="Offset from root dir to run entire suite from",
                      type=str,
                      default=""
                      )
  parser.add_argument( 
                      "-j", "--joinHPC",
                      dest="joinHPC",
                      help="Join test submissions into single collective HPC submission, use additional argument to override submission arguments using config syntax, e.g -j '{\"select\":{\"-l \":{\"select\":1}}}'",
                      type=str,
                      nargs="?",
                      default=argparse.SUPPRESS
                      )
  parser.add_argument( 
                      "-jn", "--joinName",
                      dest="joinName",
                      help="Combined test name of joined test, default is all test names concatenated",
                      type=str,
                      default=None
                      )
  parser.add_argument( 
                      "-alt", "--altdirs",
                      dest="altdirs",
                      help="Use alternate directories for multitest submission mapped 1-to-1, default is to use <root dir>/<testname> if none are provided",
                      type=str,
                      nargs="*",
                      default=None
                      )
  parser.add_argument( 
                      "-l", "--labelLength",
                      dest="labelLength",
                      help="Length of left-justify label string [file|test|step]",
                      type=int,
                      default=sc.LABEL_LENGTH
                      )
  parser.add_argument( 
                      "-g", "--globalPrefix",
                      dest="globalPrefix",
                      help="Global prefix to name step submission names, added as <PREFIX>.<rest of name>",
                      type=str,
                      default=None
                      )
  parser.add_argument( 
                      "-dry", "--dryRun",
                      dest="dryRun",
                      help="Walk through test submission but do not run",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument( 
                      "-nf", "--nofatal",
                      dest="nofatal",
                      help="HPC submission - Force continuation of test even if submission return code is error",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument( 
                      "-nw", "--nowait",
                      dest="nowait",
                      help="HPC submission - Don't wait for all jobs completion, which is done via a final .results job with dependency on all jobs",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument( 
                      "-np", "--nopost",
                      dest="nopost",
                      help="HPC submission - Don't post-process log files for results using <KEY PHRASE>",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument(
                      "-k", "--key",
                      dest="key",
                      help="Post-processing <KEY PHRASE> regex to signal a script logfile passed successfully. Assumed failed if not last line of script logfile. (default : \"%(default)s\")",
                      default="TEST ((?:\w+|[.-])+) PASS",
                      type=str
                      )
  parser.add_argument(
                      "-p", "--pool",
                      dest="pool",
                      help="Process pool size when running multiple tests, if serial test runs are desired set to 1",
                      default=4,
                      type=int
                      )
  parser.add_argument(
                      "-tp", "--threadpool",
                      dest="threadpool",
                      help="Threadpool size when running multiple steps, if serial step runs are desired set to 1",
                      default=4,
                      type=int
                      )
  parser.add_argument(
                      "-r", "--redirect",
                      dest="redirect",
                      help="Redirect test suite '[scope::name]' output to file",
                      default=None,
                      type=str
                      )
  parser.add_argument(
                      "-i", "--inlineLocal",
                      dest="inlineLocal",
                      help="Do not redirect local step output to automatically named logfile, instead output directly to stdout",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  parser.add_argument(
                      "-ff", "--forceFQDN",
                      dest="forceFQDN",
                      help="Force the selection of host-specific \"submit_options\" to use input as the assumed FQDN",
                      default=None,
                      type=str
                      )

  parser.add_argument(
                      "-fs", "--forceSingle",
                      dest="forceSingle",
                      help="Force multi-testing to run in single-process mode",
                      default=False,
                      const=True,
                      action='store_const'
                      )
  return parser

class Options(object):
  """Empty namespace"""
  pass

def main() :
  print( "Using Python version : " )
  print( sys.version )
  parser  = getOptionsParser()
  options = Options()
  parser.parse_args( namespace=options )

  success, tests, logs = runSuite( options )

  if not success :
    exit( 1 )

if __name__ == '__main__' :
  main()
