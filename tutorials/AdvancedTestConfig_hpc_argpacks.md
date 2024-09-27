# Utilizing advanced features - HPC <ins>argpacks</ins>
In this tutorial we will be exploring how to use advanced features of the framework. We will be using common terminology found in the repo's README.md - refer to that for any underlined terms that need clarification. Additionally, we will be building upon the material covered in the [Advanced Test Config - Regex Argpacks](./AdvancedTestConfig_regex_argpacks.ipynb); please review that tutorial if you haven't already. Anything in `"code-quoted"` format refers specifically to the test config, and anything in <ins>underlined</ins> format refers to specific terminology that can be found in the [README.md](../README.md).



```python
# Get notebook location
shellReturn = !pwd
notebookDirectory = shellReturn[0]
print( "Working from " + notebookDirectory )
```

    Working from /home/runner/work/hpc-workflows/hpc-workflows/tutorials


Advanced usage of the json config option `"hpc_arguments"` under `"submit_options"` will be the focus of this tutorial :



```python
# Output template file documenting options
from IPython.display import Markdown as md
md( "```jsonc\n" + open( notebookDirectory + "/../.ci/template.json", "r" )
                        .read()
                        .split( "// specifics to each HPC system" )[1]
                        .split( "// timelimit" )[0] + 
   "\n```" )
```




```jsonc

    "hpc_arguments"     :
    {
      // NO KEYWORDS at this level or below
      // argpacks can be any valid string but all must be unique
      // Recommended to not contain spaces or periods, character pattern
      // '::' is reserved for regex-based argpacks
      "<argpack>" : 
      {
        // <option> will be appended to the job submission, if an empty dict
        // is provided nothing more will happen with respect to this <argpack>
        // Entries will be joined via HPC-specific syntax then concatenated with "<option>" :
        //   non-empty values in key-value pairs join with ( '=' for PBS | ':' for SLURM )
        //   keys (with value if present)             with ( ':' for PBS | ',' for SLURM )
        // {"-l ":{"select":1,"ngpus":4}} for PBS would result in the following being added to the HPC submission
        //   -l select=1:ngpus=4
        // {"gres=":{"gpu:tesla":2,"shard":64}} for SLURM would result in the following being added to the HPC submission
        //   --gres=gpu:tesla:2,shard:64
        "<option>" : // HPC flag or option to pass in, only one allowed per argpack, use {} for flag only
        {
          "<unique-resource-name>" : "number or string", // non-unit numbers do not need quotes, for empty value use ""
          // <regex> should be a valid regex usable by python's re module
          // <unique-resource-name> CANNOT match the above <unique-resource-name>
          // future definitions will only override the specific full unique match with <regex> included
          "<regex>::<unique-resource-name>"  : 0         // only a single value is accepted
        }
      },
      // <regex> should be a valid regex usable by python's re module
      // <argpack> can match the above <argpack>, but final resolving at the step level should be unique
      // future definitions will only override the specific full unique match with <regex> included
      "<regex>::<argpack>" : {} // same layout as the above "hpc_arguments" <argpack>
    },
   
    
```




## HPC Arguments as <ins>argpacks</ins>

We should now be sufficiently familiar with <ins>argpacks</ins>, both regex and regular. For those looking to submit tests to an HPC grid, there is very often a desire to specify resources and generally the computing environment to check out for your use case. The testing framework facilitates this through the use of <ins>argpacks</ins>, with some slight caveats. While the core concepts remain the same, to differentiate them we will refer to "normal" argpacks as <ins>step argpacks</ins> and HPC ones as <ins>hpc argpacks</ins> (a third exists called <ins>resource argpacks</ins> but we'll get to that shortly)

For our examples, as it would require an actual grid to demonstate we will be using the `-dry` option to simulate what would happen without actual execution as a dry-run. Due to the layout of the framework, this will result in command outputs that could be copy-pasted and executed in a valid hpc setup, so by inspecting those we can build confidence that this would work in a real system. 

To simplify later instructions, we will assume we are writing inputs for a PBS-style grid, however syntax changes for writing SLURM inputs is essentially the same and will be covered the following example. 


### Hello HPC World! Setting up HPC submissions

Let's first construct a basic example that runs locally. Our "Hello World!" equivalent (same from the [Basic Test Config->Writing our own test config](./BasicTestConfig.ipynb#Writing-our-own-test-config))



```bash
%%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing to run multiple tests
    [file::our-config]                        Automatically redirecting our-test to /home/runner/work/hpc-workflows/hpc-workflows/our-test_stdout.log
    [file::our-config]                      Spawning process pool of size 4 to perform 1 tests
    [file::our-config]                        Launching test our-test
    [file::our-config]                        Waiting for tests to complete - BE PATIENT
    [file::our-config]                        [SUCCESS] : Test our-test reported success
    [file::our-config]                      Test suite complete, writing test results to master log file : 
    [file::our-config]                        /home/runner/work/hpc-workflows/hpc-workflows/our-config.log
    [file::our-config]                      [SUCCESS] : All tests passed


Great, no errors or if there are that's not great and try resolving them by restarting this notebook.

We will use the `-fs` and `-i` options, and shortly add `-dry` as well.


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Preparing working directory
    [test::our-config.our-test]               Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Checking if results wait is required...
    [test::our-config.our-test]               No HPC submissions, no results waiting required
    [step::our-config.our-test.our-step0]   Preparing working directory
    [step::our-config.our-test.our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Submitting step our-step0...
    [step::our-config.our-test.our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0]     Running command:
    [step::our-config.our-test.our-step0]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az714-33.22nzjvkrszmuhkvqy55p1tioig.phxx.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     ***************START our-step0***************
    
    
    TEST echo_normal.sh PASS
    
    [step::our-config.our-test.our-step0]     ***************STOP our-step0 ***************
    [step::our-config.our-test.our-step0]   Finished submitting step our-step0
    
    [test::our-config.our-test]             Checking remaining steps...
    [test::our-config.our-test]             No remaining steps, test submission complete
    [test::our-config.our-test]             Outputting results...
    [step::our-config.our-test.our-step0]   Results for our-step0
    [step::our-config.our-test.our-step0]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    [step::our-config.our-test.our-step0]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.our-test.our-step0]     [SUCCESS]
    [test::our-config.our-test]             Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test]               /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-config.our-test]             [SUCCESS] : Test our-test completed successfully


Now if we set the `"submission"` type to an HPC option (PBS) we should start to get some different output (using `-dry` to now account for potentially no HPC system available):


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS"
  },
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry

# this is just to suppress bash magic failing error clutter
echo ""
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS"
      },
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Error: Invalid submission options [Missing account on non-LOCAL submission]
    {'working_directory': None, 'queue': None, 'hpc_arguments': <HpcArgpacks.HpcArgpacks object at 0x7fb42c9f4070>, 'timelimit': None, 'wait': None, 'submitType': <SubmissionType.PBS: 'PBS'>, 'lockSubmitType': False, 'debug': None, 'account': None, 'name': 'our-config.our-test.our-step0', 'dependencies': None, 'arguments': <SubmitArgpacks.SubmitArgpacks object at 0x7fb42c9f40d0>, 'union_parse': {'submission': 'PBS'}}
    Traceback (most recent call last):
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 730, in <module>
        main()
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 724, in main
        success, tests, logs = runSuite( options )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 526, in runSuite
        success, logs = testSuite.run( options.tests )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 441, in run
        self.tests_[test].validate()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Test.py", line 61, in validate
        step.validate()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Step.py", line 77, in validate
        self.submitOptions_.validate( print=self.log )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitOptions.py", line 167, in validate
        raise Exception( errMsg )
    Exception: Error: Invalid submission options [Missing account on non-LOCAL submission]
    {'working_directory': None, 'queue': None, 'hpc_arguments': <HpcArgpacks.HpcArgpacks object at 0x7fb42c9f4070>, 'timelimit': None, 'wait': None, 'submitType': <SubmissionType.PBS: 'PBS'>, 'lockSubmitType': False, 'debug': None, 'account': None, 'name': 'our-config.our-test.our-step0', 'dependencies': None, 'arguments': <SubmitArgpacks.SubmitArgpacks object at 0x7fb42c9f40d0>, 'union_parse': {'submission': 'PBS'}}
    


Our run should have failed with some helpful output that we have not given an account to use for our submission. As accounts are what are used to bill to grid allocations and sometimes they are kept private within an organization this is not put into the test config. Instead we will provide it via command-line options using `--account/-a`. Let's say our account is `WORKFLOWS` : 


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS"
  },
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS

# this is just to suppress bash magic failing error clutter
echo ""
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS"
      },
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Error: Invalid submission options [Missing queue on non-LOCAL submission]
    {'working_directory': None, 'queue': None, 'hpc_arguments': <HpcArgpacks.HpcArgpacks object at 0x7f039d53c070>, 'timelimit': None, 'wait': None, 'submitType': <SubmissionType.PBS: 'PBS'>, 'lockSubmitType': False, 'debug': None, 'account': 'WORKFLOWS', 'name': 'our-config.our-test.our-step0', 'dependencies': None, 'arguments': <SubmitArgpacks.SubmitArgpacks object at 0x7f039d53c0d0>, 'union_parse': {'submission': 'PBS'}}
    Traceback (most recent call last):
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 730, in <module>
        main()
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 724, in main
        success, tests, logs = runSuite( options )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 526, in runSuite
        success, logs = testSuite.run( options.tests )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 441, in run
        self.tests_[test].validate()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Test.py", line 61, in validate
        step.validate()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Step.py", line 77, in validate
        self.submitOptions_.validate( print=self.log )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitOptions.py", line 167, in validate
        raise Exception( errMsg )
    Exception: Error: Invalid submission options [Missing queue on non-LOCAL submission]
    {'working_directory': None, 'queue': None, 'hpc_arguments': <HpcArgpacks.HpcArgpacks object at 0x7f039d53c070>, 'timelimit': None, 'wait': None, 'submitType': <SubmissionType.PBS: 'PBS'>, 'lockSubmitType': False, 'debug': None, 'account': 'WORKFLOWS', 'name': 'our-config.our-test.our-step0', 'dependencies': None, 'arguments': <SubmitArgpacks.SubmitArgpacks object at 0x7f039d53c0d0>, 'union_parse': {'submission': 'PBS'}}
    


We have another error : we need to provide a queue to submit to. We should also set a timelimit, though not required. When using HPC submissions `"queue"` becomes a required field that must be defined by the time the step to run is resolved. Let's say our queue is economy and our timelimit is 1 minute.

The information we have so far is most likely not enough to make a full HPC job submission, but for now let's assume that we don't need anything else to at least get things running.



```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00"
  },
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00"
      },
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Preparing working directory
    [test::our-config.our-test]               Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Checking if results wait is required...
    [test::our-config.our-test]               Final results will wait for all jobs complete
    [step::our-config.our-test.our-step0]   Preparing working directory
    [step::our-config.our-test.our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Submitting step our-step0...
    [step::our-config.our-test.our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0]     Running command:
    [step::our-config.our-test.our-step0]       qsub -q economy -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test.our-step0 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az714-33.22nzjvkrszmuhkvqy55p1tioig.phxx.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     ***************START our-step0***************
    
    [step::our-config.our-test.our-step0]     Doing dry-run, no ouptut
    
    [step::our-config.our-test.our-step0]     ***************STOP our-step0 ***************
    [step::our-config.our-test.our-step0]     Finding job ID in "12345"
    [step::our-config.our-test.our-step0]   Finished submitting step our-step0
    
    [test::our-config.our-test]             Checking remaining steps...
    [test::our-config.our-test]             No remaining steps, test submission complete
    [test::our-config.our-test]             Doing dry-run, assumed complete
    [test::our-config.our-test]             Outputting results...
    [step::our-config.our-test.our-step0]   Results for our-step0
    [step::our-config.our-test.our-step0]     Doing dry-run, assumed success
    [test::our-config.our-test]             Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test]               /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-config.our-test]             [SUCCESS] : Test our-test completed successfully


Two things should stand out as different when looking at the output :
* first is that our dry-run option has made the text where our inline output would have been into a statement that it is a dry-run
* second is that our step command _looks_ like it became way more complicated.

The command that would run is now [for PBS] `qsub` to submit our HPC job. What follows is the translation of information either determined internally or given by us via config or command line option into that command's most standard flags. Breaking it down we see :
* from our config
  * `-q economy`
  * `-l walltime=00:01:00`
* from command line
  * `-A WORKFLOWS`
* internally determined from ancestry to set the job name and output file location
  * `-N our-config.our-test.our-step0`
  * `-j oe -o /home/aislas/hpc-workflows/our-config.our-test.our-step0.log`

### Simple <ins>hpc argpacks</ins> structure

The framework has no idea what else needs to be required or what flags are necessary, so `"hpc_arguments"` as <ins>argpacks</ins> handles generalized input. It is on YOU the user to fill in the rest of what would be required to submit your job.

<div class="alert alert-block alert-info">
<b>Recall:</b>
The <code>"submit_options"</code> block is hierarchally inherited as they get closer to steps so for global options we need only define them once at the top level to be sufficient
</div>
 
We should now start to fill in the resource requests. First we will want at least one node. As noted in the [.ci/template.json](../.ci/template.json) we will first need to make an <ins>hpc argpack</ins> with the flag we want as the first key. Note that unlike <ins>step argpacks</ins>, the value of <ins>hpc argpacks</ins> will be a `{}` dictionary of one key pointing to another nested dictionary instead of `[]` for a list of arguments. 


```python
# Output template file documenting options
from IPython.display import Markdown as md
md( "```jsonc\n" + open( notebookDirectory + "/../.ci/template.json", "r" )
                        .read()
                        .split( "// specifics to each HPC system" )[1]
                        .split( "        {" )[0] + 
   "\n```" )
```




```jsonc

    "hpc_arguments"     :
    {
      // NO KEYWORDS at this level or below
      // argpacks can be any valid string but all must be unique
      // Recommended to not contain spaces or periods, character pattern
      // '::' is reserved for regex-based argpacks
      "<argpack>" : 
      {
        // <option> will be appended to the job submission, if an empty dict
        // is provided nothing more will happen with respect to this <argpack>
        // Entries will be joined via HPC-specific syntax then concatenated with "<option>" :
        //   non-empty values in key-value pairs join with ( '=' for PBS | ':' for SLURM )
        //   keys (with value if present)             with ( ':' for PBS | ',' for SLURM )
        // {"-l ":{"select":1,"ngpus":4}} for PBS would result in the following being added to the HPC submission
        //   -l select=1:ngpus=4
        // {"gres=":{"gpu:tesla":2,"shard":64}} for SLURM would result in the following being added to the HPC submission
        //   --gres=gpu:tesla:2,shard:64
        "<option>" : // HPC flag or option to pass in, only one allowed per argpack, use {} for flag only

```



Let's focus first on just forming the <ins>hpc argpack</ins> and getting our flag to appear, worrying about entries into the sub-dictionary later. We'll name our argpack "node_select" : 


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      "node_select" : { "-l" : {} }
    }
  },
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          "node_select" : { "-l" : {} }
        }
      },
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Preparing working directory
    [test::our-config.our-test]               Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Checking if results wait is required...
    [test::our-config.our-test]               Final results will wait for all jobs complete
    [step::our-config.our-test.our-step0]   Preparing working directory
    [step::our-config.our-test.our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Submitting step our-step0...
    [step::our-config.our-test.our-step0]     Gathering HPC argument packs...
    [step::our-config.our-test.our-step0]       From [our-config] adding HPC argument pack 'node_select' :
    [step::our-config.our-test.our-step0]         Adding option '-l'
    [step::our-config.our-test.our-step0]       Final argpack output for node_select : '-l'
    [step::our-config.our-test.our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0]     Running command:
    [step::our-config.our-test.our-step0]       qsub -l -q economy -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test.our-step0 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az714-33.22nzjvkrszmuhkvqy55p1tioig.phxx.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     ***************START our-step0***************
    
    [step::our-config.our-test.our-step0]     Doing dry-run, no ouptut
    
    [step::our-config.our-test.our-step0]     ***************STOP our-step0 ***************
    [step::our-config.our-test.our-step0]     Finding job ID in "12345"
    [step::our-config.our-test.our-step0]   Finished submitting step our-step0
    
    [test::our-config.our-test]             Checking remaining steps...
    [test::our-config.our-test]             No remaining steps, test submission complete
    [test::our-config.our-test]             Doing dry-run, assumed complete
    [test::our-config.our-test]             Outputting results...
    [step::our-config.our-test.our-step0]   Results for our-step0
    [step::our-config.our-test.our-step0]     Doing dry-run, assumed success
    [test::our-config.our-test]             Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test]               /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-config.our-test]             [SUCCESS] : Test our-test completed successfully


We should now see that there is an additional `-l` option to `qsub` before all the automatic hpc arguments. Also, if we look closely at the supplemental output between `Submitting step our-step0...` and `Running command:` we see _all_ <ins>argpack</ins> gathering. So now there is info under `Gathering HPC argument packs...` detailing the addition of our "node_select" entry and the option `-l` being added. The final generated output is listed as well for debug purposes on more complex entries.

### Using <ins>resource argpacks</ins>

Now to add our node count selection. To do this we will write a <ins>resource argpack</ins> inside the dictionary of our `"<option>"` (in this case `"-l"`). These <ins>argpacks</ins> take only one value (int or string) vs the list of <ins>step argpacks</ins> or the dictionary of <ins>hpc argpacks</ins>. Our resource will be "select" and we will request one node.


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      "select" : { "-l" : { "select" : 1 } }
    }
  },
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          "select" : { "-l" : { "select" : 1 } }
        }
      },
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Preparing working directory
    [test::our-config.our-test]               Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Checking if results wait is required...
    [test::our-config.our-test]               Final results will wait for all jobs complete
    [step::our-config.our-test.our-step0]   Preparing working directory
    [step::our-config.our-test.our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Submitting step our-step0...
    [step::our-config.our-test.our-step0]     Gathering HPC argument packs...
    [step::our-config.our-test.our-step0]       From [our-config] adding HPC argument pack 'select' :
    [step::our-config.our-test.our-step0]         Adding option '-l'
    [step::our-config.our-test.our-step0]           From our-config adding resource 'select' : 1
    [step::our-config.our-test.our-step0]       Final argpack output for select : '-lselect=1'
    [step::our-config.our-test.our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0]     Running command:
    [step::our-config.our-test.our-step0]       qsub -lselect=1 -q economy -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test.our-step0 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az714-33.22nzjvkrszmuhkvqy55p1tioig.phxx.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     ***************START our-step0***************
    
    [step::our-config.our-test.our-step0]     Doing dry-run, no ouptut
    
    [step::our-config.our-test.our-step0]     ***************STOP our-step0 ***************
    [step::our-config.our-test.our-step0]     Finding job ID in "12345"
    [step::our-config.our-test.our-step0]   Finished submitting step our-step0
    
    [test::our-config.our-test]             Checking remaining steps...
    [test::our-config.our-test]             No remaining steps, test submission complete
    [test::our-config.our-test]             Doing dry-run, assumed complete
    [test::our-config.our-test]             Outputting results...
    [step::our-config.our-test.our-step0]   Results for our-step0
    [step::our-config.our-test.our-step0]     Doing dry-run, assumed success
    [test::our-config.our-test]             Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test]               /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-config.our-test]             [SUCCESS] : Test our-test completed successfully


The output under `Gathering HPC argument packs...` now has an additional line indented under `Adding option -l`. Much like the <ins>step argpacks</ins>, a `From <origin> ...` prefix is added to the details of the <ins>resource argpack</ins>. Actually, our <ins>hpc argpack</ins> also has this, but it is listed as `[<origins>]` (plural) as the nested nature can lead to multiple contributors to the final result.

Our "select" resource was added using the syntax for PBS noted in the .ci/template.json of `=` to join the resource name `"select"` ant value `1` in the config together. One problem though - our resultant argument to `qsub` is `-lselect=1`! This isn't correct syntax at all...

Referring back to the .ci/template.json, a particular line to focus on now is :



```python
# Output template file documenting options
from IPython.display import Markdown as md
md( "```jsonc\n" + open( notebookDirectory + "/../.ci/template.json", "r" )
                        .read()
                        .split( "with respect to this <argpack>" )[1]
                        .split( "//   non-empty" )[0] + 
   "\n```" )
```




```jsonc

        // Entries will be joined via HPC-specific syntax then concatenated with "<option>" :
        
```



There is no additional formatting in the concatenation of our <ins>resource argpacks</ins> and the `"<option>"` we specified. Looking back at our `"-l"` entry, there is no space to separate resource arguments and the flag. Let's change that :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      "select" : { "-l " : { "select" : 1 } }
    }
  },
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          "select" : { "-l " : { "select" : 1 } }
        }
      },
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Preparing working directory
    [test::our-config.our-test]               Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Checking if results wait is required...
    [test::our-config.our-test]               Final results will wait for all jobs complete
    [step::our-config.our-test.our-step0]   Preparing working directory
    [step::our-config.our-test.our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Submitting step our-step0...
    [step::our-config.our-test.our-step0]     Gathering HPC argument packs...
    [step::our-config.our-test.our-step0]       From [our-config] adding HPC argument pack 'select' :
    [step::our-config.our-test.our-step0]         Adding option '-l '
    [step::our-config.our-test.our-step0]           From our-config adding resource 'select' : 1
    [step::our-config.our-test.our-step0]       Final argpack output for select : '-l select=1'
    [step::our-config.our-test.our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0]     Running command:
    [step::our-config.our-test.our-step0]       qsub -l select=1 -q economy -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test.our-step0 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az714-33.22nzjvkrszmuhkvqy55p1tioig.phxx.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     ***************START our-step0***************
    
    [step::our-config.our-test.our-step0]     Doing dry-run, no ouptut
    
    [step::our-config.our-test.our-step0]     ***************STOP our-step0 ***************
    [step::our-config.our-test.our-step0]     Finding job ID in "12345"
    [step::our-config.our-test.our-step0]   Finished submitting step our-step0
    
    [test::our-config.our-test]             Checking remaining steps...
    [test::our-config.our-test]             No remaining steps, test submission complete
    [test::our-config.our-test]             Doing dry-run, assumed complete
    [test::our-config.our-test]             Outputting results...
    [step::our-config.our-test.our-step0]   Results for our-step0
    [step::our-config.our-test.our-step0]     Doing dry-run, assumed success
    [test::our-config.our-test]             Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test]               /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-config.our-test]             [SUCCESS] : Test our-test completed successfully


That looks like a fully successful `qsub` command now! The same concept could be applied to SLURM, where an `"<option>"` like "--gres=" uses no spaces to appropriately concatenate the listed resources.


#### Regex-based HPC <ins>argpacks</ins>

While there are some differences in the value syntax and final constucted output between the <ins>argpack</ins> variants, the ability hierarchically pass down, override, and filter via regexes and <ins>ancestry</ins> remains more or less the same. These core features are why they are all named <ins>argpacks</ins>.
<br><br>
##### Limitations on <ins>resource argpacks</ins>
The <ins>resource argpacks</ins> allow for `"<regex>::<argpack>"` syntax with the caveat that the "basename" `"<argpack>"` MUST be unique. This special limitation is in place because `"<argpack>"` is always used as the resource name, regex or not. Thus to  avoid resource duplications if two or more <ins>resource argpacks</ins> appear with the same "basename" (one at least being regex-based) within the same <ins>hpc argpack</ins> the suite will throw an error. 

While this seems limiting at first, the safety to only select unique resources within an <ins>hpc argpack</ins> is crucial to a higher success rate of submitted jobs when dealing with regexes and variably applicable arguments. Additionally, multiple regex-<ins>resource argpacks</ins> may still exist with smart management of <ins>hpc argpacks</ins> as wrappers. 
<br><br>
##### Limitations on <ins>hpc argpacks</ins>
The <ins>hpc argpacks</ins> allow for `"<regex>::<argpack>"` syntax with a caveat similar to that of <ins>resource argpacks'</ins> uniqueness requirements. The <ins>hpc argpacks</ins> must be unique for a particular step. This means that for any specific step after its host-specific `"submit_options"` have been selected, and all <ins>argpacks</ins> of all varieties have been resolved for it based on inheritance, overriding, and <ins>ancestry</ins> that matches regexes uniqueness must be preserved, but beforehand duplicates may exist. Thus, multiple <ins>hpc argpacks</ins> with the same "basename" can exist in the config, but at the step level no duplicates can be selected.

These rules are in principle simple, but can admittedly seem complex at first so let's walk through a few examples. To start let's show the simpler uniqueness requirements of <ins>resource argpacks</ins> :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      "select" : { "-l " : { ".*less-nodes.*::select" : 1 } }
    }
  },
  "our-test" :
  {
    "submit_options" :
    {
      "hpc_arguments" : 
      {
        "select" : { "-l " : { ".*more-nodes.*::select" : 2 } }
      }
    },
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
echo ""
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          "select" : { "-l " : { ".*less-nodes.*::select" : 1 } }
        }
      },
      "our-test" :
      {
        "submit_options" :
        {
          "hpc_arguments" : 
          {
            "select" : { "-l " : { ".*more-nodes.*::select" : 2 } }
          }
        },
        "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
      }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [test::our-config.our-test]             Argument pack select at our-config.our-test '.*more-nodes.*::select' name conflict with '.*less-nodes.*::select', declared at our-config
    Traceback (most recent call last):
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 730, in <module>
        main()
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 724, in main
        success, tests, logs = runSuite( options )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 518, in runSuite
        testSuite = Suite( 
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 41, in __init__
        super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitAction.py", line 32, in __init__
        self.parse()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitAction.py", line 67, in parse
        optionKeys = self.parseSpecificOptions()
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 54, in parseSpecificOptions
        self.tests_[ test ] = Test( test, testDict, self.submitOptions_, self.globalOpts_, parent=self.ancestry(), rootDir=self.rootDir_ )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Test.py", line 30, in __init__
        super().__init__( name, options, defaultSubmitOptions, globalOpts, parent, rootDir )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitAction.py", line 32, in __init__
        self.parse()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitAction.py", line 62, in parse
        self.submitOptions_.update( SubmitOptions( self.options_[ submitKey ], origin=self.ancestry(), print=self.log ), print=self.log )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitOptions.py", line 133, in update
        if rhs.hpcArguments_.arguments_         : self.hpcArguments_.update( rhs.hpcArguments_, print=print )    
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/HpcArgpacks.py", line 35, in update
        self.nestedArguments_[key].update( rhs.nestedArguments_[key], print )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitArgpacks.py", line 47, in update
        self.validate( print=print )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitArgpacks.py", line 86, in validate
        raise Exception( err )
    Exception: Argument pack select at our-config.our-test '.*more-nodes.*::select' name conflict with '.*less-nodes.*::select', declared at our-config
    


We should see that the run failed at the test level. When `"our-test"` was being instantiated it inherited the top-level `"hpc_arguments"`, causing the conflict since both <ins>resource argpacks</ins> listed use the same "basename" 'select'.

To have our step be able to select less nodes based on its name, we should use an <ins>hpc argpack</ins> as a wrapper instead:


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      ".*less-nodes.*::select" : { "-l " : { "select" : 1 } }
    }
  },
  "our-test" :
  {
    "submit_options" :
    {
      "hpc_arguments" : 
      {
        ".*more-nodes.*::select" : { "-l " : { "select" : 2 } }
      }
    },
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          ".*less-nodes.*::select" : { "-l " : { "select" : 1 } }
        }
      },
      "our-test" :
      {
        "submit_options" :
        {
          "hpc_arguments" : 
          {
            ".*more-nodes.*::select" : { "-l " : { "select" : 2 } }
          }
        },
        "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
      }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Preparing working directory
    [test::our-config.our-test]               Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test]             Checking if results wait is required...
    [test::our-config.our-test]               Final results will wait for all jobs complete
    [step::our-config.our-test.our-step0-less-nodes] Preparing working directory
    [step::our-config.our-test.our-step0-less-nodes]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0-less-nodes]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0-less-nodes] Submitting step our-step0-less-nodes...
    [step::our-config.our-test.our-step0-less-nodes]   Gathering HPC argument packs...
    [step::our-config.our-test.our-step0-less-nodes]     From [our-config] adding HPC argument pack '.*less-nodes.*::select' :
    [step::our-config.our-test.our-step0-less-nodes]       Adding option '-l '
    [step::our-config.our-test.our-step0-less-nodes]         From our-config adding resource 'select' : 1
    [step::our-config.our-test.our-step0-less-nodes]     Final argpack output for .*less-nodes.*::select : '-l select=1'
    [step::our-config.our-test.our-step0-less-nodes]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0-less-nodes]   Running command:
    [step::our-config.our-test.our-step0-less-nodes]     qsub -l select=1 -q economy -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test.our-step0-less-nodes -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0-less-nodes.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az714-33.22nzjvkrszmuhkvqy55p1tioig.phxx.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0-less-nodes]   ***************START our-step0-less-nodes***************
    
    [step::our-config.our-test.our-step0-less-nodes]   Doing dry-run, no ouptut
    
    [step::our-config.our-test.our-step0-less-nodes]   ***************STOP our-step0-less-nodes***************
    [step::our-config.our-test.our-step0-less-nodes]   Finding job ID in "12345"
    [step::our-config.our-test.our-step0-less-nodes] Finished submitting step our-step0-less-nodes
    
    [test::our-config.our-test]             Checking remaining steps...
    [test::our-config.our-test]             No remaining steps, test submission complete
    [test::our-config.our-test]             Doing dry-run, assumed complete
    [test::our-config.our-test]             Outputting results...
    [step::our-config.our-test.our-step0-less-nodes] Results for our-step0-less-nodes
    [step::our-config.our-test.our-step0-less-nodes]   Doing dry-run, assumed success
    [test::our-config.our-test]             Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test]               /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-config.our-test]             [SUCCESS] : Test our-test completed successfully


From the above config, we see that the <ins>hpc argpack</ins> 'select' is technically duplicated as `".*more-nodes.*::select"` and `".*less-nodes.*::select"`. Note however that at the time the step is determining what to run only one is used. To show that two cannot exist at this point we can make either the regexes match verbatim or at least match the final step <ins>ancestry</ins>. Let's do the latter : 


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "economy",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      ".*less-nodes.*::select" : { "-l " : { "select" : 1 } }
    }
  },
  "our-test" :
  {
    "submit_options" :
    {
      "hpc_arguments" : 
      {
        ".*our.*::select" : { "-l " : { "select" : 2 } }
      }
    },
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -dry -a WORKFLOWS
echo ""
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "economy",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          ".*less-nodes.*::select" : { "-l " : { "select" : 1 } }
        }
      },
      "our-test" :
      {
        "submit_options" :
        {
          "hpc_arguments" : 
          {
            ".*our.*::select" : { "-l " : { "select" : 2 } }
          }
        },
        "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
      }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0-less-nodes] Argument pack select at our-config.our-test '.*our.*::select' name conflict with '.*less-nodes.*::select', declared at our-config
    Traceback (most recent call last):
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 730, in <module>
        main()
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 724, in main
        success, tests, logs = runSuite( options )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 526, in runSuite
        success, logs = testSuite.run( options.tests )
      File "/home/runner/work/hpc-workflows/hpc-workflows/tutorials/../.ci/runner.py", line 441, in run
        self.tests_[test].validate()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Test.py", line 61, in validate
        step.validate()
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/Step.py", line 77, in validate
        self.submitOptions_.validate( print=self.log )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitOptions.py", line 170, in validate
        self.hpcArguments_.selectAncestrySpecificSubmitArgpacks( print=print )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/HpcArgpacks.py", line 69, in selectAncestrySpecificSubmitArgpacks
        finalHpcArgpacks.validate( print=print )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/HpcArgpacks.py", line 42, in validate
        super().validate( print )
      File "/home/runner/work/hpc-workflows/hpc-workflows/.ci/SubmitArgpacks.py", line 86, in validate
        raise Exception( err )
    Exception: Argument pack select at our-config.our-test '.*our.*::select' name conflict with '.*less-nodes.*::select', declared at our-config
    


Now our config is failing to load since if `our-step0-less-nodes` were to have run it would have selected both <ins>hpc argpacks</ins>. Before running any of the steps to prevent wasted time of potentially failing in the middle of a test due to framework-imposed rules all aspects are validated first. This ensures that to the best of the framework's knowledge your submitted steps should be acceptable by the scheduler.

The above example also shows why duplicates for <ins>hpc argpacks</ins> are allowed generically before being restricted at the step level. It allows us to make "wrappers" as shown in the `"hpc_arguments" : { ".*more-nodes.*::select" ...` example to effectively override resources with regexes whilst adhering to the <ins>resource argpacks</ins> rules.

