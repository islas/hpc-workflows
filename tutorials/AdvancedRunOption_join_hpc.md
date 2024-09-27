# Utilizing advanced features - Joining <ins>tests</ins> for HPC submissions
In this tutorial we will be exploring how to use advanced features of the framework. We will be using common terminology found in the repo's README.md - refer to that for any underlined terms that need clarification. Additionally, we will be building upon the material covered in the [Advanced Test Config - HPC argpacks](./AdvancedTestConfig_hpc_argpacks.ipynb); please review that tutorial if you haven't already. Anything in `"code-quoted"` format refers specifically to the test config, and anything in <ins>underlined</ins> format refers to specific terminology that can be found in the [README.md](../README.md).



```python
# Get notebook location
shellReturn = !pwd
notebookDirectory = shellReturn[0]
print( "Working from " + notebookDirectory )
```

    Working from /home/runner/work/hpc-workflows/hpc-workflows/tutorials


Advanced usage of the <ins>run script</ins> command line option `-j` will be the focus of this tutorial :


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -h | \
  tr $'\n' '@' | \
  sed -e 's/[ ]\+-h.*\?entire suite from/.../g' | \
  sed -e 's/[ ]\+-alt.*/.../g' | \
  tr '@' $'\n'
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    usage: runner.py [-h] [-t TESTS [TESTS ...]] [-s {PBS,SLURM,LOCAL}]
                     [-a ACCOUNT] [-d DIROFFSET] [-j [JOINHPC]] [-jn JOINNAME]
                     [-alt [ALTDIRS ...]] [-l LABELLENGTH] [-g GLOBALPREFIX]
                     [-dry] [-nf] [-nw] [-np] [-k KEY] [-p POOL] [-tp THREADPOOL]
                     [-r REDIRECT] [-i] [-ff FORCEFQDN] [-fs]
                     testsConfig
    
    positional arguments:
      testsConfig           JSON file defining set of tests
    
    options:
    ...
      -j [JOINHPC], --joinHPC [JOINHPC]
                            Join test submissions into single collective HPC submission, use additional argument to override submission arguments using config syntax, e.g -j '{"select":{"-l ":{"select":1}}}'
      -jn JOINNAME, --joinName JOINNAME
                            Combined test name of joined test, default is all test names concatenated
    ...


## Joining Tests for Single HPC Submission

Tests can specify general resource usage and steps can further refine those requirements. This works well to individually submit each step independently to an HPC grid. However, for relatively small steps or if the smallest resource allocations are comparably large (e.g. whole node allocations for large core-count CPUs) one may want to aggregate the tests into larger workloads to be more effective with the resources. 

This can also be an appealing option if queue times on the grids are long, requiring individually submitted steps to each wait in the queue. Thus for steps with dependencies this would emulate re-entering the queue multiple times.

To avoid the need to over-spec the test suite to one particular machine (remember we want this to remain generic and flexible) the framework natively supports joining tests and steps into single job submissions. Tests and steps should now be able to remain as small logically separate components, steering away from machine-specific large and fragile multiple tests in one script designs.

<div class="alert alert-block alert-info">
<b>Check the FQDN of the node if using host-specific selections!</b>
When using cummulative join features for HPC runs the host that actually runs the final individual step is actually the HPC node and not the login node from which the command was launched. Joining tests under one HPC job bundles all the specified tests and their respective steps into one HPC launch step that then runs the tests normally in the node. This can at times lead to different FQDN naming between where the initial launch of the job and where the step is finally run, depending on how your computing system had been configured.
<br><br>
    
Final <ins>step argacks</ins> to the step only rely on the location where the step script is started (i.e. when "Running command" for that step is shown). This cah be affected by using the joining capabilities as the selected <ins>submit options</ins> may differ between where you launch and where it runs.

The <ins>hpc argpacks</ins> required for the steps to be submitted to the grid, total aggregated via joining or submitted normally, will only ever rely on the host that starts the test suite (the HPC login node). They are never used in the node environment for the fully joined submission and thus are not affected by changes in FQDN.

**ALTERNATIVELY** consider using the `--forceFQDN` option to manually specify the selection criteria
</div>

### Where do resource amounts come from?
Recall that each step in the end specifies its own individual set of `"arguments"` from its cummulative ancestry. The `"hpc_arguments"` work the same way as all keys under `"submit_options"` do. The difference here is that `"hpc_arguments"` is slightly more complex dictionary as opposed to a single dictionary of lists.

As HPC systems can be very different in scheduler args, format, and resources available to request one of the simplest approaches is to let the user specify the details as explained in the [Advanced Test Config - HPC argpacks](./AdvancedTestConfig_hpc_argpacks.ipynb) tutorial. This then provides a generally easy means to isolate resource amounts as the <ins>resource argpacks</ins> values. 


### Accepted Formats
Internally, when steps and tests are joined for HPC submission values from <ins>resource argpacks</ins> are attempted to be joined and if unsuccessful the first value for that resource key is used. It's not a perfect solution but is easy to understand and works for the most part. Supported values that can be joined are :
* integers
* memory amount strings in the format `[0-9]+(t|g|m|k)?(b|w)` where `(t|g|m|k)` correspond to unit prefix multipliers and `(b|w)` to bytes or words as units, case insensitive - e.g. "4GB"

### Initial Config
To see this in action we will show one resource of each style in PBS-style :
* nodes as integers
* memory per node as memory string
* job priority as non-joinable string 

First, an initial setup :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "main",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      "select" : 
      { 
        "-l " : 
        {
          "select" : 1,
          "mem"    : "32gb"
        }
      },
      "priority" :
      {
        "-l " :
        {
          "job_priority" : "economy"
        }
      }
    }
  },
  "our-test" :
  {
    "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } }
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
        "queue"      : "main",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          "select" : 
          { 
            "-l " : 
            {
              "select" : 1,
              "mem"    : "32gb"
            }
          },
          "priority" :
          {
            "-l " :
            {
              "job_priority" : "economy"
            }
          }
        }
      },
      "our-test" :
      {
        "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } }
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
    [step::our-config.our-test.our-step0]   Preparing working directory
    [step::our-config.our-test.our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test.our-step0]   Submitting step our-step0...
    [step::our-config.our-test.our-step0]     Gathering HPC argument packs...
    [step::our-config.our-test.our-step0]       From [our-config] adding HPC argument pack 'select' :
    [step::our-config.our-test.our-step0]         Adding option '-l '
    [step::our-config.our-test.our-step0]           From our-config adding resource 'select' : 1
    [step::our-config.our-test.our-step0]           From our-config adding resource 'mem'    : 32gb
    [step::our-config.our-test.our-step0]       Final argpack output for select : '-l select=1:mem=32gb'
    [step::our-config.our-test.our-step0]       From [our-config] adding HPC argument pack 'priority' :
    [step::our-config.our-test.our-step0]         Adding option '-l '
    [step::our-config.our-test.our-step0]           From our-config adding resource 'job_priority' : economy
    [step::our-config.our-test.our-step0]       Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.our-test.our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test.our-step0]     Running command:
    [step::our-config.our-test.our-step0]       qsub -l select=1:mem=32gb -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test.our-step0 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
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


### Accumulating Resources

Now that we have a setup, let's make some additional tests. As the resources are defined for the whole config, all tests will use and request the same amount of resources :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "main",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      "select" : 
      { 
        "-l " : 
        {
          "select" : 1,
          "mem"    : "32gb"
        }
      },
      "priority" :
      {
        "-l " :
        {
          "job_priority" : "economy"
        }
      }
    }
  },
  "our-test0" :
  {
    "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } }
  },
  "our-test1" :
  {
    "steps" : { "our-step1" : { "command" : "./tests/scripts/echo_normal.sh" } }
  },
  "our-test2" :
  {
    "steps" : { "our-step2" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test0 our-test1 our-test2 -fs -i -dry -a WORKFLOWS
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "main",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          "select" : 
          { 
            "-l " : 
            {
              "select" : 1,
              "mem"    : "32gb"
            }
          },
          "priority" :
          {
            "-l " :
            {
              "job_priority" : "economy"
            }
          }
        }
      },
      "our-test0" :
      {
        "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } }
      },
      "our-test1" :
      {
        "steps" : { "our-step1" : { "command" : "./tests/scripts/echo_normal.sh" } }
      },
      "our-test2" :
      {
        "steps" : { "our-step2" : { "command" : "./tests/scripts/echo_normal.sh" } }
      }
    }
    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test0]            Preparing working directory
    [test::our-config.our-test0]              Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test0]            Checking if results wait is required...
    [test::our-config.our-test0]              Final results will wait for all jobs complete
    [step::our-config.our-test0.our-step0]  Preparing working directory
    [step::our-config.our-test0.our-step0]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test0.our-step0]    Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test0.our-step0]  Submitting step our-step0...
    [step::our-config.our-test0.our-step0]    Gathering HPC argument packs...
    [step::our-config.our-test0.our-step0]      From [our-config] adding HPC argument pack 'select' :
    [step::our-config.our-test0.our-step0]        Adding option '-l '
    [step::our-config.our-test0.our-step0]          From our-config adding resource 'select' : 1
    [step::our-config.our-test0.our-step0]          From our-config adding resource 'mem'    : 32gb
    [step::our-config.our-test0.our-step0]      Final argpack output for select : '-l select=1:mem=32gb'
    [step::our-config.our-test0.our-step0]      From [our-config] adding HPC argument pack 'priority' :
    [step::our-config.our-test0.our-step0]        Adding option '-l '
    [step::our-config.our-test0.our-step0]          From our-config adding resource 'job_priority' : economy
    [step::our-config.our-test0.our-step0]      Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.our-test0.our-step0]    Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test0.our-step0]    Running command:
    [step::our-config.our-test0.our-step0]      qsub -l select=1:mem=32gb -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test0.our-step0 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test0.our-step0.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test0.our-step0]    ***************START our-step0***************
    
    [step::our-config.our-test0.our-step0]    Doing dry-run, no ouptut
    
    [step::our-config.our-test0.our-step0]    ***************STOP our-step0 ***************
    [step::our-config.our-test0.our-step0]    Finding job ID in "12345"
    [step::our-config.our-test0.our-step0]  Finished submitting step our-step0
    
    [test::our-config.our-test0]            Checking remaining steps...
    [test::our-config.our-test0]            No remaining steps, test submission complete
    [test::our-config.our-test0]            Doing dry-run, assumed complete
    [test::our-config.our-test0]            Outputting results...
    [step::our-config.our-test0.our-step0]  Results for our-step0
    [step::our-config.our-test0.our-step0]    Doing dry-run, assumed success
    [test::our-config.our-test0]            Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test0]              /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test0.log
    [test::our-config.our-test0]            [SUCCESS] : Test our-test0 completed successfully
    [test::our-config.our-test1]            Preparing working directory
    [test::our-config.our-test1]              Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test1]            Checking if results wait is required...
    [test::our-config.our-test1]              Final results will wait for all jobs complete
    [step::our-config.our-test1.our-step1]  Preparing working directory
    [step::our-config.our-test1.our-step1]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test1.our-step1]    Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test1.our-step1]  Submitting step our-step1...
    [step::our-config.our-test1.our-step1]    Gathering HPC argument packs...
    [step::our-config.our-test1.our-step1]      From [our-config] adding HPC argument pack 'select' :
    [step::our-config.our-test1.our-step1]        Adding option '-l '
    [step::our-config.our-test1.our-step1]          From our-config adding resource 'select' : 1
    [step::our-config.our-test1.our-step1]          From our-config adding resource 'mem'    : 32gb
    [step::our-config.our-test1.our-step1]      Final argpack output for select : '-l select=1:mem=32gb'
    [step::our-config.our-test1.our-step1]      From [our-config] adding HPC argument pack 'priority' :
    [step::our-config.our-test1.our-step1]        Adding option '-l '
    [step::our-config.our-test1.our-step1]          From our-config adding resource 'job_priority' : economy
    [step::our-config.our-test1.our-step1]      Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.our-test1.our-step1]    Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test1.our-step1]    Running command:
    [step::our-config.our-test1.our-step1]      qsub -l select=1:mem=32gb -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test1.our-step1 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test1.our-step1.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test1.our-step1]    ***************START our-step1***************
    
    [step::our-config.our-test1.our-step1]    Doing dry-run, no ouptut
    
    [step::our-config.our-test1.our-step1]    ***************STOP our-step1 ***************
    [step::our-config.our-test1.our-step1]    Finding job ID in "12345"
    [step::our-config.our-test1.our-step1]  Finished submitting step our-step1
    
    [test::our-config.our-test1]            Checking remaining steps...
    [test::our-config.our-test1]            No remaining steps, test submission complete
    [test::our-config.our-test1]            Doing dry-run, assumed complete
    [test::our-config.our-test1]            Outputting results...
    [step::our-config.our-test1.our-step1]  Results for our-step1
    [step::our-config.our-test1.our-step1]    Doing dry-run, assumed success
    [test::our-config.our-test1]            Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test1]              /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test1.log
    [test::our-config.our-test1]            [SUCCESS] : Test our-test1 completed successfully
    [test::our-config.our-test2]            Preparing working directory
    [test::our-config.our-test2]              Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.our-test2]            Checking if results wait is required...
    [test::our-config.our-test2]              Final results will wait for all jobs complete
    [step::our-config.our-test2.our-step2]  Preparing working directory
    [step::our-config.our-test2.our-step2]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test2.our-step2]    Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test2.our-step2]  Submitting step our-step2...
    [step::our-config.our-test2.our-step2]    Gathering HPC argument packs...
    [step::our-config.our-test2.our-step2]      From [our-config] adding HPC argument pack 'select' :
    [step::our-config.our-test2.our-step2]        Adding option '-l '
    [step::our-config.our-test2.our-step2]          From our-config adding resource 'select' : 1
    [step::our-config.our-test2.our-step2]          From our-config adding resource 'mem'    : 32gb
    [step::our-config.our-test2.our-step2]      Final argpack output for select : '-l select=1:mem=32gb'
    [step::our-config.our-test2.our-step2]      From [our-config] adding HPC argument pack 'priority' :
    [step::our-config.our-test2.our-step2]        Adding option '-l '
    [step::our-config.our-test2.our-step2]          From our-config adding resource 'job_priority' : economy
    [step::our-config.our-test2.our-step2]      Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.our-test2.our-step2]    Script : ./tests/scripts/echo_normal.sh
    [step::our-config.our-test2.our-step2]    Running command:
    [step::our-config.our-test2.our-step2]      qsub -l select=1:mem=32gb -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.our-test2.our-step2 -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test2.our-step2.log -- /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.our-test2.our-step2]    ***************START our-step2***************
    
    [step::our-config.our-test2.our-step2]    Doing dry-run, no ouptut
    
    [step::our-config.our-test2.our-step2]    ***************STOP our-step2 ***************
    [step::our-config.our-test2.our-step2]    Finding job ID in "12345"
    [step::our-config.our-test2.our-step2]  Finished submitting step our-step2
    
    [test::our-config.our-test2]            Checking remaining steps...
    [test::our-config.our-test2]            No remaining steps, test submission complete
    [test::our-config.our-test2]            Doing dry-run, assumed complete
    [test::our-config.our-test2]            Outputting results...
    [step::our-config.our-test2.our-step2]  Results for our-step2
    [step::our-config.our-test2.our-step2]    Doing dry-run, assumed success
    [test::our-config.our-test2]            Writing relevant logfiles to view in master log file : 
    [test::our-config.our-test2]              /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test2.log
    [test::our-config.our-test2]            [SUCCESS] : Test our-test2 completed successfully


Each should have its own set of resources requested via `qsub` in the final output command. If we go ahead and auto-join them for one large job we would instead get (we remove the `-fs` flag as that takes precedence over joining) :


```bash
%%bash -s "$notebookDirectory" 

$1/../.ci/runner.py $1/../our-config.json -t our-test0 our-test1 our-test2 -i -dry -a WORKFLOWS -j
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Computing maximum HPC resources of tests...
    [file::our-config]                      Accumulate maximum HPC resources per test...
    [test::our-config.our-test0]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test0]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test0]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test0]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test0]                    [PHASE 0] Resources for [ our-step0 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test0]                    1 jobs completed during this runtime
    [test::our-config.our-test0]                All jobs simulated, stopping
    [test::our-config.our-test0]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.our-test1]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test1]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test1]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test1]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test1]                    [PHASE 0] Resources for [ our-step1 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test1]                    1 jobs completed during this runtime
    [test::our-config.our-test1]                All jobs simulated, stopping
    [test::our-config.our-test1]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.our-test2]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test2]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test2]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test2]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test2]                    [PHASE 0] Resources for [ our-step2 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test2]                    1 jobs completed during this runtime
    [test::our-config.our-test2]                All jobs simulated, stopping
    [test::our-config.our-test2]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [file::our-config]                      Calculating expected runtime of tests across 4 workers [pool size]
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                          [PHASE 0] Resources for [  our-test0, our-test1, our-test2 ] : '-l select=3:mem=96gb -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          3 jobs completed during this runtime
    [file::our-config]                      Maximum calculated resources for running all tests is '-l select=3:mem=96gb -l job_priority=economy'
    [file::our-config]                      Maximum calculated timelimit for running all tests is '00:01:00'
    [file::our-config]                      Using current file as launch executable : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [file::our-config]                      Setting keyphrase for passing to internally defined one
    [file::our-config]                      No join name provided, defaulting to 'joinHPC_our-test0_our-test1_our-test2'
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Preparing working directory
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Checking if results wait is required...
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   Final results will wait for all jobs complete
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Preparing working directory
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Submitting step submit...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Gathering HPC argument packs...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     From [join] adding HPC argument pack 'select' :
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]       Adding option '-l '
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'select' : 3
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'mem'    : 96gb
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     Final argpack output for select : '-l select=3:mem=96gb'
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     From [join] adding HPC argument pack 'priority' :
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]       Adding option '-l '
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'job_priority' : economy
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Script : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Running command:
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     qsub -l select=3:mem=96gb -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.joinHPC_our-test0_our-test1_our-test2.submit -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_our-test0_our-test1_our-test2.submit.log -- /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py /home/runner/work/hpc-workflows/hpc-workflows/our-config.json --tests our-test0 our-test1 our-test2 --submitType LOCAL --account WORKFLOWS --labelLength 32 --dryRun --key "TEST ((?:\w+|[.-])+) PASS" --pool 4 --threadpool 1 --inlineLocal --forceFQDN fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   *************** START submit  ***************
    
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Doing dry-run, no ouptut
    
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   ***************  STOP submit  ***************
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Finding job ID in "12345"
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Finished submitting step submit
    
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Checking remaining steps...
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] No remaining steps, test submission complete
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Doing dry-run, assumed complete
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Outputting results...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Results for submit
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Doing dry-run, assumed success
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Writing relevant logfiles to view in master log file : 
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_our-test0_our-test1_our-test2.log
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] [SUCCESS] : Test joinHPC_our-test0_our-test1_our-test2 completed successfully
    [file::our-config]                      Joined HPC tests complete, above success only means tests managed to complete, please see logs for per-test success
    [file::our-config]                      Post-processing all test results...
    [file::our-config]                      Doing dry-run, assumed success


We see that the output looks completely different than what we are used to. We start with a flurry of preprocessing of phases, calculation of resources, simulating threadpools, and so on... confusing stuff. All this happens before we even get to something we are familiar with of `Submitting step submit...`.

What is going? Before we can even submit an aggregated job we need to know what each test would take as resources. To get that we need to know what each step would take _and_ any explicit order of execution dictated by dependencies _AS WELL AS_ implicit order based on the size of the thread pool. 

That is used to tally the total maximum resources a test would use. As a pessimistic approximation, we use that maximum as what a test would use for its entire duration. From there the process pool is used to account for implicit execution order of tests, once again doing the same process of maximum resource usage but now based on the tests' allotments instead of steps. The final aggregation is what will be placed on the command line for the HPC submission command arguments.

Looking at the final maximums reported by `[file::our-config]` at `Maximum calculated resources|timelimit...`, it should be intuitive that we've effectively tripled our resource amounts for anything numeric and supported since with a process pool of 4 all the tests we listed will run concurrently. Likewise, our timelimit did not change for that same reason.

What follows is a in-situ generated test and step combo that submits a job to run this suite again locally in the node(s) requested with the aggregated resource total, and all options (implicit, default, provided and auto-filled) to the <ins>run script</ins> explicitly listed including, especially, the tests we initially wanted to run. In essence, the join feature acts as a wrapper to resubmitting multi-test running locally in a node environment and calculating the resources it would take to accomplish that.


To demonstrate that our command line options would be listened to, say we want our aggregated tests to run in a process pool of 1 as we can only check out one node at a time as an arbitraty reason. Regardless, we want to control the run options of the local run that would occur, and the resource request should reflect that :


```bash
%%bash -s "$notebookDirectory" 

$1/../.ci/runner.py $1/../our-config.json -t our-test0 our-test1 our-test2 -i -dry -a WORKFLOWS -j -p 1
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Computing maximum HPC resources of tests...
    [file::our-config]                      Accumulate maximum HPC resources per test...
    [test::our-config.our-test0]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test0]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test0]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test0]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test0]                    [PHASE 0] Resources for [ our-step0 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test0]                    1 jobs completed during this runtime
    [test::our-config.our-test0]                All jobs simulated, stopping
    [test::our-config.our-test0]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.our-test1]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test1]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test1]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test1]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test1]                    [PHASE 0] Resources for [ our-step1 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test1]                    1 jobs completed during this runtime
    [test::our-config.our-test1]                All jobs simulated, stopping
    [test::our-config.our-test1]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.our-test2]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test2]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test2]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test2]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test2]                    [PHASE 0] Resources for [ our-step2 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test2]                    1 jobs completed during this runtime
    [test::our-config.our-test2]                All jobs simulated, stopping
    [test::our-config.our-test2]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [file::our-config]                      Calculating expected runtime of tests across 1 workers [pool size]
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                          [PHASE 0] Resources for [ our-test0 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          1 jobs completed during this runtime
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                            Joining argpack 'select'   from [join] into maxlimit
    [file::our-config]                            Joining argpack 'priority' from [join] into maxlimit
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                          [PHASE 1] Resources for [ our-test1 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          1 jobs completed during this runtime
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                            Joining argpack 'select'   from [join] into maxlimit
    [file::our-config]                            Joining argpack 'priority' from [join] into maxlimit
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                          [PHASE 2] Resources for [ our-test2 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          1 jobs completed during this runtime
    [file::our-config]                      Maximum calculated resources for running all tests is '-l select=1:mem=32gb -l job_priority=economy'
    [file::our-config]                      Maximum calculated timelimit for running all tests is '00:03:00'
    [file::our-config]                      Using current file as launch executable : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [file::our-config]                      Setting keyphrase for passing to internally defined one
    [file::our-config]                      No join name provided, defaulting to 'joinHPC_our-test0_our-test1_our-test2'
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Preparing working directory
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Checking if results wait is required...
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   Final results will wait for all jobs complete
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Preparing working directory
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Submitting step submit...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Gathering HPC argument packs...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     From [join] adding HPC argument pack 'select' :
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]       Adding option '-l '
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'select' : 1
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'mem'    : 32gb
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     Final argpack output for select : '-l select=1:mem=32gb'
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     From [join] adding HPC argument pack 'priority' :
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]       Adding option '-l '
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'job_priority' : economy
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Script : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Running command:
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     qsub -l select=1:mem=32gb -l job_priority=economy -q main -l walltime=00:03:00 -A WORKFLOWS -N our-config.joinHPC_our-test0_our-test1_our-test2.submit -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_our-test0_our-test1_our-test2.submit.log -- /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py /home/runner/work/hpc-workflows/hpc-workflows/our-config.json --tests our-test0 our-test1 our-test2 --submitType LOCAL --account WORKFLOWS --labelLength 32 --dryRun --key "TEST ((?:\w+|[.-])+) PASS" --pool 1 --threadpool 1 --inlineLocal --forceFQDN fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   *************** START submit  ***************
    
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Doing dry-run, no ouptut
    
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   ***************  STOP submit  ***************
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Finding job ID in "12345"
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Finished submitting step submit
    
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Checking remaining steps...
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] No remaining steps, test submission complete
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Doing dry-run, assumed complete
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Outputting results...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Results for submit
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Doing dry-run, assumed success
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Writing relevant logfiles to view in master log file : 
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_our-test0_our-test1_our-test2.log
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] [SUCCESS] : Test joinHPC_our-test0_our-test1_our-test2 completed successfully
    [file::our-config]                      Joined HPC tests complete, above success only means tests managed to complete, please see logs for per-test success
    [file::our-config]                      Post-processing all test results...
    [file::our-config]                      Doing dry-run, assumed success


The maximum outputs are now :
```
[file::our-config]  Maximum calculated resources for running all tests is '-l select=1:mem=32gb -l job_priority=economy'
[file::our-config]  Maximum calculated timelimit for running all tests is '00:03:00'
```

We are running the joined tests serially in our HPC job submission, and only increasing our runtime accordingly since they are require the same resources.

### Overriding joined resources

In the first joined resource grouping you may have noticed that we selected 3 nodes :

`-l select=3:mem=96gb -l job_priority=economy`

This might be fine, but let's say that each node can request up to 128GB and has more than enough resources to run all the tests at the same time. We _could_ rewrite the tests to all fit together specifically and only request one node in one of the tests so the final output requests just `-l select=1...`, but that is bad design for a few reasons :
1. Now the tests __MUST___ run together, limiting our ability to mix and match other tests
2. The tests' definitions do not stand on their own, limiting our ability to run each test independently
3. Leaving out resources to be filled by another test obfuscates that test's requirements
4. Writing the tests in this manner assumes particular hardware capabilities rather than writing to what a test _needs_

The suggested alternative is to override elements of the joined `"hpc_arguments"` at the command-line. This would be difficult to automate, inquiring about all the potential combination of resources what nodes are at your disposal and their respective capabilities, and so on. It _could_ be done, but is beyond the scope and philosophy of this framework to remain simple. 

To override the final resource aggregation, we would pass in an argument to the `-j` flag in the format of the `"hpc_arguments"` `{}` dictionary that was accumulated. Recall that the joining aggregates your resultant `"hpc_arguments"` for each step (resolving all host-specifics and regex <ins>hpc argpacks</ins>) and then tests into one large set of <ins>hpc argpacks</ins>. Due to the uniqueness requirements of each plus the added output help of `From [<origin>] adding '<hpc argpack>'...From <origin> adding resource '<resource argpack>[ : <value if present> ]`, it should be possible to write an `"hpc_arguments"` `{}` that can index and override any resource value.

<div class="alert alert-block alert-info">
<b>Flags and resource names cannot be changed!</b>

As the flags and resource names are used as dictionary keys, it is impossible to change their value when writing the override dictionary. This may be changed in the future, but is a limitation worth noting for now.
</div>

Let's go ahead and re-run our joined tests submission but set the node count to 1, and for extra credit bump the priority to premium. 

As our node selection is under <ins>hpc argpack</ins> `"select"`, then `"-l "`, and finally under <ins>resource argpack</ins> `"select"` we would use `{"select":{"-l ":{"select":1}}}` to override that (unnecessary spaces are left out for compactness, but can be left in).

Job priority is under `"priority"` -> `"-l "` -> `"job_priority"`. Thus `{"priority":{"-l ":{"job_priority":"premium"}}}` should be what we want.

Since `-j` only accepts one argument, we will need to merge these two dictionaries. Once again, the uniqueness requirements save us to dissallow confusing conflicts. As a final override we should now have :

`{"select":{"-l ":{"select":1}},"priority":{"-l ":{"job_priority":"premium"}}}`

Now to run with that as a string input argument to `-j` :



```bash
%%bash -s "$notebookDirectory" 

$1/../.ci/runner.py $1/../our-config.json -t our-test0 our-test1 our-test2 \
                                          -i -dry -a WORKFLOWS \
                                          -j '{"select":{"-l ":{"select":1}},"priority":{"-l ":{"job_priority":"premium"}}}'
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Computing maximum HPC resources of tests...
    [file::our-config]                      Accumulate maximum HPC resources per test...
    [test::our-config.our-test0]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test0]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test0]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test0]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test0]                    [PHASE 0] Resources for [ our-step0 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test0]                    1 jobs completed during this runtime
    [test::our-config.our-test0]                All jobs simulated, stopping
    [test::our-config.our-test0]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.our-test1]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test1]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test1]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test1]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test1]                    [PHASE 0] Resources for [ our-step1 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test1]                    1 jobs completed during this runtime
    [test::our-config.our-test1]                All jobs simulated, stopping
    [test::our-config.our-test1]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.our-test2]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.our-test2]                Calculating expected runtime of steps across 1 thread workers [threadpool size]
    [test::our-config.our-test2]                  Simulating threadpool for 0:01:00
    [test::our-config.our-test2]                    Calculate max instantaneous resources for this phase
    [test::our-config.our-test2]                    [PHASE 0] Resources for [ our-step2 ] : '-l select=1:mem=32gb -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.our-test2]                    1 jobs completed during this runtime
    [test::our-config.our-test2]                All jobs simulated, stopping
    [test::our-config.our-test2]              Maximum HPC resources required will be '-l select=1:mem=32gb -l job_priority=economy' with timelimit '00:01:00'
    [file::our-config]                      Calculating expected runtime of tests across 4 workers [pool size]
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                          [PHASE 0] Resources for [  our-test0, our-test1, our-test2 ] : '-l select=3:mem=96gb -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          3 jobs completed during this runtime
    [file::our-config]                      Maximum calculated resources for running all tests is '-l select=3:mem=96gb -l job_priority=economy'
    [file::our-config]                      Maximum calculated timelimit for running all tests is '00:01:00'
    [file::our-config]                      Requested override of resources with '{"select":{"-l ":{"select":1}},"priority":{"-l ":{"job_priority":"premium"}}}'
    [file::our-config]                        New maximum resources for running all tests is '-l select=1:mem=96gb -l job_priority=premium'
    [file::our-config]                      Using current file as launch executable : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [file::our-config]                      Setting keyphrase for passing to internally defined one
    [file::our-config]                      No join name provided, defaulting to 'joinHPC_our-test0_our-test1_our-test2'
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Preparing working directory
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Checking if results wait is required...
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   Final results will wait for all jobs complete
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Preparing working directory
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Submitting step submit...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Gathering HPC argument packs...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     From [join, cli] adding HPC argument pack 'select' :
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]       Adding option '-l '
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From cli  adding resource 'select' : 1
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From join adding resource 'mem'    : 96gb
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     Final argpack output for select : '-l select=1:mem=96gb'
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     From [cli] adding HPC argument pack 'priority' :
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]       Adding option '-l '
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]         From cli adding resource 'job_priority' : premium
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     Final argpack output for priority : '-l job_priority=premium'
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Script : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Running command:
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]     qsub -l select=1:mem=96gb -l job_priority=premium -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.joinHPC_our-test0_our-test1_our-test2.submit -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_our-test0_our-test1_our-test2.submit.log -- /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py /home/runner/work/hpc-workflows/hpc-workflows/our-config.json --tests our-test0 our-test1 our-test2 --submitType LOCAL --account WORKFLOWS --labelLength 32 --dryRun --key "TEST ((?:\w+|[.-])+) PASS" --pool 4 --threadpool 1 --inlineLocal --forceFQDN fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   *************** START submit  ***************
    
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Doing dry-run, no ouptut
    
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   ***************  STOP submit  ***************
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Finding job ID in "12345"
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Finished submitting step submit
    
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Checking remaining steps...
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] No remaining steps, test submission complete
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Doing dry-run, assumed complete
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Outputting results...
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit] Results for submit
    [step::our-config.joinHPC_our-test0_our-test1_our-test2.submit]   Doing dry-run, assumed success
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] Writing relevant logfiles to view in master log file : 
    [test::our-config.joinHPC_our-test0_our-test1_our-test2]   /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_our-test0_our-test1_our-test2.log
    [test::our-config.joinHPC_our-test0_our-test1_our-test2] [SUCCESS] : Test joinHPC_our-test0_our-test1_our-test2 completed successfully
    [file::our-config]                      Joined HPC tests complete, above success only means tests managed to complete, please see logs for per-test success
    [file::our-config]                      Post-processing all test results...
    [file::our-config]                      Doing dry-run, assumed success


After the max calculations, we get another line now : `Requested override of resources with <our input>...New maximum...is <what we wanted as final resources>`. Additionally, at the `[step::submit] Submitting step submit...Gathering HPC argument packs...` we now see that the `<origin>` for `'select'` is listed as `cli`, same for our `'job_priority'` <ins>resource argpack</ins>.

### Usage with regex <ins>hpc and resource argpacks</ins>

The above example was fairly simple as all the tests and steps use the same resources. To provide a more realistic complex setup that would make use of regex <ins>argpacks</ins> let's adjust our config.



```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "PBS",
    "queue"      : "main",
    "timelimit"  : "00:01:00",
    "hpc_arguments" :
    {
      ".*quartnode.*::select" : 
      { 
        "-l " : 
        {
          "select" : 1,
          "mem"    : "32gb",
          "ncpus"  : 32,
          ".*mpi.*::mpiprocs" : 32
        }
      },
      ".*fullnode.*::select" :
      { 
        "-l " : 
        {
          "select" : 1,
          "mem"    : "128gb",
          "ncpus"  : 128,
          ".*mpi.*::mpiprocs" : 128
        }
      },
      "priority" :
      {
        "-l " :
        {
          "job_priority" : "economy"
        }
      }
    }
  },
  "quartnode-simple" :
  {
    "submit_options" :
    {
      "hpc_arguments" : { ".*quartnode.*::select" : { "-l " : { "mem" : "16gb" } } }
    },
    "steps" : 
    {
      "our-step0" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      },
      "our-step0-mpi" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      }
    }
  },
  "quartnode" :
  {
    "steps" : 
    {
      "our-step0" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      },
      "our-step0-mpi" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      }
    }
  },
  "fullnode-simple" :
  {
    "steps" : 
    {
      "our-step0" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      },
      "our-step0-mpi" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      }
    }
  },
  "fullnode-double" :
  {
    "submit_options" :
    {
      "hpc_arguments" : { ".*fullnode.*::select" : { "-l " : { "select" : 2 } } }
    },
    "steps" : 
    {
      "our-step0" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      },
      "our-step0-mpi" :
      {
        "command" : "./tests/scripts/echo_normal.sh"
      }
    }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "submit_options" :
      {
        "submission" : "PBS",
        "queue"      : "main",
        "timelimit"  : "00:01:00",
        "hpc_arguments" :
        {
          ".*quartnode.*::select" : 
          { 
            "-l " : 
            {
              "select" : 1,
              "mem"    : "32gb",
              "ncpus"  : 32,
              ".*mpi.*::mpiprocs" : 32
            }
          },
          ".*fullnode.*::select" :
          { 
            "-l " : 
            {
              "select" : 1,
              "mem"    : "128gb",
              "ncpus"  : 128,
              ".*mpi.*::mpiprocs" : 128
            }
          },
          "priority" :
          {
            "-l " :
            {
              "job_priority" : "economy"
            }
          }
        }
      },
      "quartnode-simple" :
      {
        "submit_options" :
        {
          "hpc_arguments" : { ".*quartnode.*::select" : { "-l " : { "mem" : "16gb" } } }
        },
        "steps" : 
        {
          "our-step0" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          },
          "our-step0-mpi" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          }
        }
      },
      "quartnode" :
      {
        "steps" : 
        {
          "our-step0" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          },
          "our-step0-mpi" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          }
        }
      },
      "fullnode-simple" :
      {
        "steps" : 
        {
          "our-step0" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          },
          "our-step0-mpi" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          }
        }
      },
      "fullnode-double" :
      {
        "submit_options" :
        {
          "hpc_arguments" : { ".*fullnode.*::select" : { "-l " : { "select" : 2 } } }
        },
        "steps" : 
        {
          "our-step0" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          },
          "our-step0-mpi" :
          {
            "command" : "./tests/scripts/echo_normal.sh"
          }
        }
      }
    }


If our nodes can support 128GB, 128 CPUs (and that many mpi ranks), joining all with a process pool of 4+ and thread pool of 2+ per process would have each running concurrently (we remove the `-i` option which is forcing serialization of steps). That means all the `"quartnode..."` tests can be combined into one node and the `"fullnode..."` tests take 1+ nodes apiece. The `"fullnode-double"` will have each step taking two nodes. Let's see what the joining would look like without modifications :


```bash
%%bash -s "$notebookDirectory" 

$1/../.ci/runner.py $1/../our-config.json -t quartnode-simple quartnode fullnode-simple fullnode-double \
                                          -dry -a WORKFLOWS -j -p 4 -tp 2
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Computing maximum HPC resources of tests...
    [file::our-config]                      Accumulate maximum HPC resources per test...
    [test::our-config.quartnode-simple]       Computing maximum HPC resources per runnable step phase...
    [test::our-config.quartnode-simple]         Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.quartnode-simple]           Simulating threadpool for 0:01:00
    [test::our-config.quartnode-simple]             Calculate max instantaneous resources for this phase
    [test::our-config.quartnode-simple]                 Joining argpack '.*quartnode.*::select' from [our-config, our-config.quartnode-simple] into joinall
    [test::our-config.quartnode-simple]                 Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.quartnode-simple]               Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.quartnode-simple]             [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=2:mem=32gb:ncpus=64:mpiprocs=32 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.quartnode-simple]             2 jobs completed during this runtime
    [test::our-config.quartnode-simple]         All jobs simulated, stopping
    [test::our-config.quartnode-simple]       Maximum HPC resources required will be '-l select=2:mem=32gb:ncpus=64:mpiprocs=32 -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.quartnode]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.quartnode]                Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.quartnode]                  Simulating threadpool for 0:01:00
    [test::our-config.quartnode]                    Calculate max instantaneous resources for this phase
    [test::our-config.quartnode]                        Joining argpack '.*quartnode.*::select' from [our-config] into joinall
    [test::our-config.quartnode]                        Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.quartnode]                      Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.quartnode]                    [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=2:mem=64gb:ncpus=64:mpiprocs=32 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.quartnode]                    2 jobs completed during this runtime
    [test::our-config.quartnode]                All jobs simulated, stopping
    [test::our-config.quartnode]              Maximum HPC resources required will be '-l select=2:mem=64gb:ncpus=64:mpiprocs=32 -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.fullnode-simple]        Computing maximum HPC resources per runnable step phase...
    [test::our-config.fullnode-simple]          Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.fullnode-simple]            Simulating threadpool for 0:01:00
    [test::our-config.fullnode-simple]              Calculate max instantaneous resources for this phase
    [test::our-config.fullnode-simple]                  Joining argpack '.*fullnode.*::select'  from [our-config] into joinall
    [test::our-config.fullnode-simple]                  Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.fullnode-simple]                Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.fullnode-simple]              [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=2:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.fullnode-simple]              2 jobs completed during this runtime
    [test::our-config.fullnode-simple]          All jobs simulated, stopping
    [test::our-config.fullnode-simple]        Maximum HPC resources required will be '-l select=2:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.fullnode-double]        Computing maximum HPC resources per runnable step phase...
    [test::our-config.fullnode-double]          Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.fullnode-double]            Simulating threadpool for 0:01:00
    [test::our-config.fullnode-double]              Calculate max instantaneous resources for this phase
    [test::our-config.fullnode-double]                  Joining argpack '.*fullnode.*::select'  from [our-config, our-config.fullnode-double] into joinall
    [test::our-config.fullnode-double]                  Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.fullnode-double]                Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.fullnode-double]              [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=4:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.fullnode-double]              2 jobs completed during this runtime
    [test::our-config.fullnode-double]          All jobs simulated, stopping
    [test::our-config.fullnode-double]        Maximum HPC resources required will be '-l select=4:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy' with timelimit '00:01:00'
    [file::our-config]                      Calculating expected runtime of tests across 4 workers [pool size]
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                          [PHASE 0] Resources for [  quartnode-simple,        quartnode,  fullnode-simple,  fullnode-double ] : '-l select=10:mem=608gb:ncpus=640:mpiprocs=320 -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          4 jobs completed during this runtime
    [file::our-config]                      Maximum calculated resources for running all tests is '-l select=10:mem=608gb:ncpus=640:mpiprocs=320 -l job_priority=economy'
    [file::our-config]                      Maximum calculated timelimit for running all tests is '00:01:00'
    [file::our-config]                      Using current file as launch executable : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [file::our-config]                      Setting keyphrase for passing to internally defined one
    [file::our-config]                      No join name provided, defaulting to 'joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double'
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Preparing working directory
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Checking if results wait is required...
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double]   Final results will wait for all jobs complete
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Preparing working directory
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Submitting step submit...
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Gathering HPC argument packs...
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     From [join] adding HPC argument pack 'select' :
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]       Adding option '-l '
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From join adding resource 'select'   : 10
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From join adding resource 'mem'      : 608gb
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From join adding resource 'ncpus'    : 640
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From join adding resource 'mpiprocs' : 320
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     Final argpack output for select : '-l select=10:mem=608gb:ncpus=640:mpiprocs=320'
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     From [join] adding HPC argument pack 'priority' :
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]       Adding option '-l '
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From join adding resource 'job_priority' : economy
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Script : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Running command:
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     qsub -l select=10:mem=608gb:ncpus=640:mpiprocs=320 -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit.log -- /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py /home/runner/work/hpc-workflows/hpc-workflows/our-config.json --tests quartnode-simple quartnode fullnode-simple fullnode-double --submitType LOCAL --account WORKFLOWS --labelLength 32 --dryRun --key "TEST ((?:\w+|[.-])+) PASS" --pool 4 --threadpool 2 --forceFQDN fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   *************** START submit  ***************
    
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Doing dry-run, no ouptut
    
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   ***************  STOP submit  ***************
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Finding job ID in "12345"
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Finished submitting step submit
    
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Checking remaining steps...
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] No remaining steps, test submission complete
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Doing dry-run, assumed complete
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Outputting results...
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Results for submit
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Doing dry-run, assumed success
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Writing relevant logfiles to view in master log file : 
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double]   /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.log
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] [SUCCESS] : Test joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double completed successfully
    [file::our-config]                      Joined HPC tests complete, above success only means tests managed to complete, please see logs for per-test success
    [file::our-config]                      Post-processing all test results...
    [file::our-config]                      Doing dry-run, assumed success


What? Our results are completely wrong as in they would not even be allowed to be submitted!

The framework has no idea what our fictitious hardware capabilities are, what nodes we have, or the like. All it will do is aggregate the `"hpc_arguments"`, adding together things that can be added. That in the end gives us this monstrosity :

`-l select=10:mem=608gb:ncpus=640:mpiprocs=320 -l job_priority=economy`

8 steps, each taking at least one node :
* cores :
  * 4 take only 32 cpus
  * 2 take 128 cpus
  * 2 take 128 cpus per node at 2x nodes
* mpi ranks
  * 2 take only 32 cpus
  * 1 take 128 cpus
  * 1 take 128 cpus per node at 2x nodes
* memory :
  * 2 take 16GB
  * 2 take 32GB
  * 2 take 128GB
  * 2 take 128BG per node at 2x nodes

Clearly the framework has simply added all theses together without consideration that our particular setup is 128 CPUS/128GB per node. And of course, how would it know? That's our job to inform it since node configuration and heterogeneous setups make it difficult to account for every possible aggregation.

Interestingly, it does the math right, logically joining the `".*mpi.*::mpiprocs"` <ins>resource argpacks</ins> and even moreso the `"<regex>::select"` <ins>hpc argpacks</ins> despite the `<regex>` portions being different. If we look at the `[step::submit] Submitting step submit...Gathering HPC argument packs...` section, we see that the <ins>argpack</ins> names no longer have regexes in them. When joining, the <ins>argpack</ins> "basename" for <ins>hpc and resource argpacks</ins> is used to aggregate common entries. Furthermore, as we only care about the "basename" and many regex <ins>argpacks</ins> may be contributed from respective steps it makes no sense to track or use the original regexes as keys into our final joining `"hpc_arguments"` so instead it is simply stripped out. 

This is one of the key reasons for why <ins>hpc argpacks</ins> also carry a uniqueness limitation, as it ensures proper aggregation in a logical manner when joining. It also makes indexing for overriding at the command line more obvious rather than matching any one regex.


We've started to see that for large jobs we may not want to use this joining feature unless we want to only enter the batch queue system once. Its strength primarily lies in joining jobs into one node, but you are free to use the feature as you see fit. Regardless, for the sake of this exercise let's fix this up with overrides that make more sense. 

Firstly, we _know_ our nodes are limited to 128 cores/ranks/GB so we will use the following : 

`{"select":{"-l ":{"mem":"128GB","ncpus":128,"mpiprocs":128}}}`

Note that we don't need to use the regexes here as we are modifying the final maximum which strips it. Also, we are fully requesting `mpiprocs` even though for half the steps none are used and for a quarter they only need half that amount if packed into a single node (2x tests each with 32 mpi ranks). This might be better solved with a heterogeneous resource submission and further highlights where this feature breaks down, but let's continue with this less-efficient approach for completness. 

Second, as we are now maximizing the request of our nodes, we pack the 4 `simple` tests into one node reducing the count from 10 to 7, resulting in :

`{"select":{"-l ":{"select":7,"mem":"128GB","ncpus":128,"mpiprocs":128}}}`


```bash
%%bash -s "$notebookDirectory" 

$1/../.ci/runner.py $1/../our-config.json -t quartnode-simple quartnode fullnode-simple fullnode-double \
                                          -dry -a WORKFLOWS -p 4 -tp 2 \
                                          -j '{"select":{"-l ":{"select":7,"mem":"128GB","ncpus":128,"mpiprocs":128}}}'
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Computing maximum HPC resources of tests...
    [file::our-config]                      Accumulate maximum HPC resources per test...
    [test::our-config.quartnode-simple]       Computing maximum HPC resources per runnable step phase...
    [test::our-config.quartnode-simple]         Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.quartnode-simple]           Simulating threadpool for 0:01:00
    [test::our-config.quartnode-simple]             Calculate max instantaneous resources for this phase
    [test::our-config.quartnode-simple]                 Joining argpack '.*quartnode.*::select' from [our-config, our-config.quartnode-simple] into joinall
    [test::our-config.quartnode-simple]                 Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.quartnode-simple]               Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.quartnode-simple]             [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=2:mem=32gb:ncpus=64:mpiprocs=32 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.quartnode-simple]             2 jobs completed during this runtime
    [test::our-config.quartnode-simple]         All jobs simulated, stopping
    [test::our-config.quartnode-simple]       Maximum HPC resources required will be '-l select=2:mem=32gb:ncpus=64:mpiprocs=32 -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.quartnode]              Computing maximum HPC resources per runnable step phase...
    [test::our-config.quartnode]                Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.quartnode]                  Simulating threadpool for 0:01:00
    [test::our-config.quartnode]                    Calculate max instantaneous resources for this phase
    [test::our-config.quartnode]                        Joining argpack '.*quartnode.*::select' from [our-config] into joinall
    [test::our-config.quartnode]                        Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.quartnode]                      Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.quartnode]                    [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=2:mem=64gb:ncpus=64:mpiprocs=32 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.quartnode]                    2 jobs completed during this runtime
    [test::our-config.quartnode]                All jobs simulated, stopping
    [test::our-config.quartnode]              Maximum HPC resources required will be '-l select=2:mem=64gb:ncpus=64:mpiprocs=32 -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.fullnode-simple]        Computing maximum HPC resources per runnable step phase...
    [test::our-config.fullnode-simple]          Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.fullnode-simple]            Simulating threadpool for 0:01:00
    [test::our-config.fullnode-simple]              Calculate max instantaneous resources for this phase
    [test::our-config.fullnode-simple]                  Joining argpack '.*fullnode.*::select'  from [our-config] into joinall
    [test::our-config.fullnode-simple]                  Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.fullnode-simple]                Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.fullnode-simple]              [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=2:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.fullnode-simple]              2 jobs completed during this runtime
    [test::our-config.fullnode-simple]          All jobs simulated, stopping
    [test::our-config.fullnode-simple]        Maximum HPC resources required will be '-l select=2:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy' with timelimit '00:01:00'
    [test::our-config.fullnode-double]        Computing maximum HPC resources per runnable step phase...
    [test::our-config.fullnode-double]          Calculating expected runtime of steps across 2 thread workers [threadpool size]
    [test::our-config.fullnode-double]            Simulating threadpool for 0:01:00
    [test::our-config.fullnode-double]              Calculate max instantaneous resources for this phase
    [test::our-config.fullnode-double]                  Joining argpack '.*fullnode.*::select'  from [our-config, our-config.fullnode-double] into joinall
    [test::our-config.fullnode-double]                  Joining argpack 'priority'              from [our-config] into joinall
    [test::our-config.fullnode-double]                Unsure how to operate on resources economy and economy together, defaulting to economy
    [test::our-config.fullnode-double]              [PHASE 0] Resources for [      our-step0  our-step0-mpi ] : '-l select=4:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy', timelimit = 0:01:00
    [test::our-config.fullnode-double]              2 jobs completed during this runtime
    [test::our-config.fullnode-double]          All jobs simulated, stopping
    [test::our-config.fullnode-double]        Maximum HPC resources required will be '-l select=4:mem=256gb:ncpus=256:mpiprocs=128 -l job_priority=economy' with timelimit '00:01:00'
    [file::our-config]                      Calculating expected runtime of tests across 4 workers [pool size]
    [file::our-config]                        Simulating threadpool for 0:01:00
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                            Joining argpack 'select'   from [join] into joinall
    [file::our-config]                            Joining argpack 'priority' from [join] into joinall
    [file::our-config]                          Unsure how to operate on resources economy and economy together, defaulting to economy
    [file::our-config]                          [PHASE 0] Resources for [  quartnode-simple,        quartnode,  fullnode-simple,  fullnode-double ] : '-l select=10:mem=608gb:ncpus=640:mpiprocs=320 -l job_priority=economy', timelimit = 0:01:00
    [file::our-config]                          4 jobs completed during this runtime
    [file::our-config]                      Maximum calculated resources for running all tests is '-l select=10:mem=608gb:ncpus=640:mpiprocs=320 -l job_priority=economy'
    [file::our-config]                      Maximum calculated timelimit for running all tests is '00:01:00'
    [file::our-config]                      Requested override of resources with '{"select":{"-l ":{"select":7,"mem":"128GB","ncpus":128,"mpiprocs":128}}}'
    [file::our-config]                        New maximum resources for running all tests is '-l select=7:mem=128GB:ncpus=128:mpiprocs=128 -l job_priority=economy'
    [file::our-config]                      Using current file as launch executable : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [file::our-config]                      Setting keyphrase for passing to internally defined one
    [file::our-config]                      No join name provided, defaulting to 'joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double'
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Preparing working directory
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Checking if results wait is required...
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double]   Final results will wait for all jobs complete
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Preparing working directory
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Submitting step submit...
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Gathering HPC argument packs...
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     From [cli] adding HPC argument pack 'select' :
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]       Adding option '-l '
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From cli adding resource 'select'   : 7
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From cli adding resource 'mem'      : 128GB
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From cli adding resource 'ncpus'    : 128
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From cli adding resource 'mpiprocs' : 128
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     Final argpack output for select : '-l select=7:mem=128GB:ncpus=128:mpiprocs=128'
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     From [join] adding HPC argument pack 'priority' :
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]       Adding option '-l '
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]         From join adding resource 'job_priority' : economy
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     Final argpack output for priority : '-l job_priority=economy'
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Script : /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Running command:
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]     qsub -l select=7:mem=128GB:ncpus=128:mpiprocs=128 -l job_priority=economy -q main -l walltime=00:01:00 -A WORKFLOWS -N our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit -j oe -o /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit.log -- /home/runner/work/hpc-workflows/hpc-workflows/.ci/runner.py /home/runner/work/hpc-workflows/hpc-workflows/our-config.json --tests quartnode-simple quartnode fullnode-simple fullnode-double --submitType LOCAL --account WORKFLOWS --labelLength 32 --dryRun --key "TEST ((?:\w+|[.-])+) PASS" --pool 4 --threadpool 2 --forceFQDN fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   *************** START submit  ***************
    
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Doing dry-run, no ouptut
    
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   ***************  STOP submit  ***************
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Finding job ID in "12345"
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Finished submitting step submit
    
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Checking remaining steps...
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] No remaining steps, test submission complete
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Doing dry-run, assumed complete
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Outputting results...
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit] Results for submit
    [step::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.submit]   Doing dry-run, assumed success
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] Writing relevant logfiles to view in master log file : 
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double]   /home/runner/work/hpc-workflows/hpc-workflows/our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double.log
    [test::our-config.joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double] [SUCCESS] : Test joinHPC_quartnode-simple_quartnode_fullnode-simple_fullnode-double completed successfully
    [file::our-config]                      Joined HPC tests complete, above success only means tests managed to complete, please see logs for per-test success
    [file::our-config]                      Post-processing all test results...
    [file::our-config]                      Doing dry-run, assumed success


That worked, but we had to basically do the whole aggregation calculations ourselves. This was an extreme example where all the tests and steps run at the same time, but effectively demonstrates the complexities involved with this sort of feature. 

Making it "smarter" might complicate the system further and/or begin to lean toward overspecifying to a particular hardware configuration or batch scheduler. This may be revisited in the future.


Note : A heterogeneous submission would be possible to inject (very poorly) via override as so :

`{"select":{"-l ":{"select":3,"mem":"128GB","ncpus":128,"mpiprocs":"128+1:mem:48GB:ncpus:64:mpiprocs:64+1:...",}}}`

Note : When using the `-j` option you may also use the `-jn` / `--joinName` option to manually specify the joined test's name rather than using the default `"joinHPC_<all tests concatenated>"` which may be overly long for many tests.


```python

```
