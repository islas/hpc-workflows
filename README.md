[![Regression Tests](https://github.com/islas/hpc-workflows/actions/workflows/regtests.yml/badge.svg)](https://github.com/islas/hpc-workflows/actions/workflows/regtests.yml)
# CI/CD Agnostic Testing Framework
Built on python and sh, this framework aims to divorce the testing environment and control for running regression tests from the CI/CD tools (Github Workflows, Azure DevOps, Jenkins, etc.) allowing for portable usage. Likewise as this can exist outside those tools, the testing framework allows configuration for running tests in either a complex job-submission style HPC system or a local run, better allowing debugging of failing tests beyond logs available from said tools. The added benefit in this is immense as the local tests will replicate the CI/CD build as close as possible with differences only arising from changes in user-CI/CD environment and any job parallelization done.


## Quick Start

### Terminology
You should be generally familiar with testing and/or whatever environment you want to integrate this with. Beyond that we will introduce a few keywords and concepts before describing how the test framework works. Feel free to skip ahead to later sections and jump back to this if you need term clarification.

#### Entry Point and Test Config
* Run script - The entry point for all tests will be the [.ci/runner.py](./.ci/runner.py). From this point on it will simply be referred to as the <ins>*run script*</ins> (to avoid confusion with GitHub Runners - may change in the future).
* Test config - The defintion of tests will always reside in a JSON-formatted file called the <ins>*test config*</ins> which will be able to be parsed by Python's [json module](https://docs.python.org/3/library/json.html) (this does not support comments - may change in the future).
* Report script - An optional end-point for tests is to use [.ci/reporter.py](./.ci/reporter.py) to gather a final report for a set of tests run. This will be known as the <ins>*report script*</ins> or <ins>*reporter*</ins>.

#### Test Config Terminology
These will be listed with the following format: <br>
`<Term> - [<json keyword if applicable>] (<code implementation>) - Description`<br>

* Suite ([Suite](.ci/runner.py)) - Analogous to the test config but just refers to the collection of tests as opposed to the JSON file
* Submit Options [`"submit_options"`] ([SubmitOptions](.ci/SubmitOptions.py)) - Details the *how* a script, test or suite should be run, particularly powerful in defining any HPC-specifics and host-specific variations scripts must know about
* Test [<anything not `"submit_options"`>] ([Test](.ci/Test.py)) - Defines a test within the suite, contains the steps and optionally higher-precedence specification of submit options for this test
* Step [<anything under `"steps"` inside test] ([Step](.ci/Step.py)) - Defines a step within a test, like a test can contain specific submit options. Most important though, it defines the script to run and any interdependencies between other steps in this test
* Submit Action ([SubmitAction](.ci/SubmitAction.py)) - Base class for suite/test/step which constitutes a runnable "action" with submit options

#### Additional Terminology
* Root directory - All suites/tests/steps/etc. always start from the root directory which by default is the directory path to the test config supplied
* Working directory - If specified, a working path is applied to the respective submit action from the root directory before anything else occurs
* arguments
  * Submit Options / argpacks - These arguments are called argpacks that allow lists of arguments to be organized into named groups and default applied to all subsequent actions (regex argpacks allow for filtering/conditional application)
  * Steps / normal arguments - These arguments are **always** applied to the step script first before any argpakcs evaluation
* Dependency - List interdependency between steps using common HPC nomenclature `after*`
* Ancestry - The equivalent "fully-qualified-name" of an action with `.` delimter to separate suite/test/step, e.g. For a test config `myconfig.json` with test `simple` and step `foobar`, step `foobar`'s ancestry would be `myconfig.simple.foobar`
* Keyphrase - a specifically formatted string that steps will need to match as their last line to mark success

### How it works
The test framework functions off of a limited few key principles ingrained into the test config format (see [example.json](.ci/example.json) for simplified example or [regression suite](tests/00_submitOptions/00_submitOptions.json) for in-depth working example) :
* Each test is independent of another
  * Anything under `"steps"` in a test must be a uniquely identified step
* Each step will execute *only one* command script
  * Steps are default considered to have failed *__UNLESS__* the very last line of the command script output matches the designated success keyphrase (default is `TEST ((?:\w+|[.-])+) PASS`, see [regression suite step](tests/scripts/echo_normal.sh))
* Submit options can exist at any level *and*
  * Any definition of submit options in a parent action are inherited as defaults to the subsequent children actions (e.g. test submit options are default applied to its respective steps)
  * Any redefinition of the exact same option or argpack in children will override and take precedence
  * Under `"submit_options"`, anything not a keyword will be assumed to be a host-specific set of `"submit_options"` applied after all generic non-host-specifc options if the FQDN of the host machine running the test(s) contains that string
  * Only the final cummulative submit options at a step are applied and used in running your tests' scripts
  * Argpacks are applied *after* step arguments based on alphabetic order first and order of appearance in test config second
  * Regex-based argpacks will use `<regex>::argpack` format where `argpack` is the name used for order sorting and `<regex>` is used to filter based on step ancestry

That's it! This shouldn't be too much to follow, but if the above did not make sense even when refering to the [terminology](#terminology) please refer to the tutorials or regression tests that thoroughly walk through some of these concepts.

With a properly written test config and the above principles it should become intuitive what each step or test would do. 

### Running
Once you have a test config that you think should execute the things you want it to do, the next step is to actually have the run script execute your test(s). To do this in the simplest manner will be:
```
# The run script location does not matter
<location to hpc-workflows>/.ci/runner.py <path to your test config> -t <test to run>
```

As an example you can use the test config provided in the regression suite to run some basic tests :
```
./hpc-workflows/.ci/runner.py tests/00_submitOptions/00_submitOptions.json -t basic
```

One can run multiple tests, listed as space-delimited arguments into the `-t <test to run>` option like so : 
```
./hpc-workflows/.ci/runner.py tests/00_submitOptions/00_submitOptions.json -t basic overrideAtTest basic-regex
```
Note that this will try to run all listed tests simultaneously within a job pool (default 4). If you have tests that interfere with one another (e.g. cleaning any previous build or writing common files in the same directories) this may prove problematic. For this situation you may either want to redesign your tests or code if possible to maximize parallelization in the same directory or look into the advanced features of multiple alternate directory mapping in the advanced launch options tutorial to isolate each test. The regression suite tests do not have this problem so if you wish to see what multiple tests running at once looks like the above command will work.

For further customization of launching tests refer to the help option (`./hpc-workflows/.ci/runner.py --help`) or the tutorials on launch options.

### Reporting
Normally, each suite run, test, and step report their respective logfiles' location and some basic info for you to use in debugging. This makes the output clean and convenient if you have access to the logfiles, for instance if you are running your tests locally. However, when running in a CI/CD environment most users do not have the option to log in to the host machine and search logfiles. One could upload all the logfiles generated for all or even just failed tests, and this is certainly not a bad solution especially for posterity. This does rely on some specific integration into that particular CI/CD environment and may not always be scriptable, i.e. dynamically generate list of files to upload in a neat format with the chosen CI/CD solution.

As an alternative [or augmentation] to this, one can use the report script to generate a logdump that as clean as possible outputs all failed tests' and steps' logfiles with a final summary. Depending on your steps' outputs this may end up being very long, but this method will always work with any CI/CD environment and not require extra CI/CD setup to gather logfiles.

An example excerpt is shown below for the final summary after all failed test and step logs are printed to the console :
```
~ How to use brief ~
^^ !!! ALL LOG FILES ARE PRINTED TO SCREEN ABOVE FOR REFERENCE !!! ^^
To find when a logfile is printed search for (remove single quotes) :
'Opening logfile <logfile>'
OR
'Closing logfile <logfile>'
Replacing <logfile> with the logfile you wish to see

Or refer to log files : 
master log [developers only]=====> /glade/u/home/aislas/hpc-workflows/tests/00_submitOptions/00_submitOptions.log
  basic-fail stdout =============> /glade/u/home/aislas/hpc-workflows/tests/00_submitOptions/basic-fail_stdout.log
    step stdout =================> /glade/u/home/aislas/hpc-workflows/tests/00_submitOptions/00_submitOptions.basic-fail.step.log

^^ !!! ALL LOG FILES ARE PRINTED TO SCREEN ABOVE FOR REFERENCE !!! ^^

SUMMARY OF TEST FAILURES
NAME                     REASON                                  
basic-fail               [test::basic-fail]  [FAILURE] : Steps [ step ] failed
[TO REPRODUCE LOCALLY] : ./hpc-workflows/.ci/runner.py 00_submitOptions.json -t basic-fail -s LOCAL
  step                   arg0 arg1                               

Note: HPC users should use '-s LOCAL' in reproduce command with caution
      as it will run directly where you are, consider using an interactive node
FAILURE!
```

## Why not Bazel, Earthly, Docker, etc...?

### Firstly : more dependencies
Yes you could say "well now it becomes one dependency, just download <insert your alt tool>" but now you have everything THAT tool is built on + learning that tool's syntax, setup, etc. This is meant to be as barebones as possible with generally simple rules in the json layout - _THAT'S IT_. 

Chances are you have `python3` and `sh` on your system so after that it's on you to figure out the rest of your dependencies as normal. That's normally where Docker/other tools to manage your dependencies come in. You don't need a swiss-army-knife-do-it-all-get-my-dependencies-and-make-me-coffee toolchain. This just runs scripts, no more no less. You need dependencies solved? Either write your solution in `sh` or make use of another tool to solve _that problem_ (PS you can probably still make use of this software _inside that tool_ because it's so simple.)

### Second : HPC runs
Almost all solutions out there assume single-node dedicated isolation of environments (containers) to solve their problem. Beyond the dependencies that brings as noted in #1, imagine trying to do this on a multi-node HPC system that takes 1000s of CPUs and sprinkle in a couple of GPUs. Using Singularity can solve this, but now your users need Singularity and any complexity that brings. Yes containerization _can_ be useful and _can_ be used with this system but it solves something different (replication isolated environments vs replication of testing procedures). Both can be done together and/or separate, but as it stands no solutions that solve CI/CD agnostic testing solve it for natively running on an HPC system.

### Third : ease of setup
There is none aside from cloning this code. Same could be said for other systems, but afterwards what's next? Reading syntax documentation on how to write `test.my-custom-yaml` or some other esoteric markup (or maybe even straight coding-based) language. It's json, don't know how to write it? A quick glance at [the wiki page](https://en.wikipedia.org/wiki/JSON#Syntax) tells you almost everything you need to know. Need to know the options and how they work, look at the tutorials for more documentation or [regression test config](tests/00_submitOptions/00_submitOptions.json) for an in-depth working example.

### Fourth and finally : flexibility
This does not require running containers nor prohibit usage of containers. It can run _trully_ locally on a machine in user environment or a container or an HPC job, even in in an interactive HPC session. So if one is dead set on usage of containers to solve their dependencies, this can just as easily be incorporated into that workflow. Want to run a specific step that failed? Just run the exact command that the test did. Don't want to run it as an HPC job? Just don't submit and run it locally. You don't even need this code at that point since you're copy-pasting shell commands from your test scripts and thus can more directly run your tests independent of intricate test frameworks/harnesses.
