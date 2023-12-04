# Creating a basic test config
The definition of all tests from a respective test config as seen in the tests/ examples. In this tutorial we will be breaking down how to write a simple but fully working test config in the expected JSON format. We will be using common terminology found in the repo's README.md - refer to that for any underlined terms that need clarification. Anything in `"code-quoted"` format refers specifically to the test config.

## Test Config Format
So what is the <ins>test config</ins> format, aside from JSON? It will look like this :
```jsonc
{
  // this is the only KEYWORD at this level
  // ALL ENTRIES ARE OPTIONAL UNLESS NOTED
  "submit_options" : // These are globally applied submit options
  {
    // KEYWORDS
   
    // can be relative or absolute, applied from root directory
    "working_directory" : "path",
   
    // generally needed for any HPC system
    "queue"             : "HPC queue",
   
    // specific to each HPC system
    "resources"         : "HPC resources flags and options",
   
    // timelimit for a step to complete
    "timelimit"         : "HH:MM:SS",
   
    // uses HPC wait/blocking feature - generally not recommended
    "wait"              : "true if set",
   
    // use one of the options to specify how steps should run
    "submission"        : "LOCAL", // PBS|SLURM|LOCAL
   
    // dict of argpacks
    "arguments"         :
    {
      // argpacks can be any valid string but all must be unique
      // Recommended to not contain spaces or periods, character pattern
      // '::' is reserved for regex-based argpacks
     
      // list of arguments to this specific <argpack>
      // They DO NOT undergo shell-expansion, so $ENV_VAR will be verbatim passed in
      "<argpack>"          : [ "list", "of", "arguments" ],
     
      // <regex> should be a valid regex usable by python's re module
      // <argpack> can match the above <argpack> string since the full
      // strings are unique, but they will be considered separate and
      // future definitions will only override the specific unique match
      // Single arguments with spaces should be entered as one string
      "<regex>::<argpack>" : [ "-f", "one whole arg", "-x" ]
    },
    // NO MORE KEYWORDS AT THIS LEVEL, ANYTHING ELSE IS CONSIDERED A HOST-SPECIFIC SUBSET
    // subset will be applied if key is found inside host FQDN
    // NOT REGEX - this is just python `if key in fqdn`
    "match-fqdn" :      
    {
      // Any of the "submit_options" KEYWORDS - host-specific subsets cannot be nested
      // When steps are resolved if a host-specific subset matches it will be applied
      // AFTER all generic submit_options have been applied
    },
    // No limit on number of host-specific subsets as long as they are unique
    "may-match-other-host" :
    {
    }
  },
 
  // everything that isn't "submit_options" is considered a test name
  // Like argpacks, they can be named anything unique amongst tests, but
  // avoid using spaces and periods. Recommended characters are [a-zA-Z_-+]
  "test-name" :
  {
    "submit_options" : {}, // EXACT SAME RULES AS ABOVE APPLY
    // Additional KEYWORD
    // A dict of steps, order of entry does not determine order of execution
    "steps" : // REQUIRED KEYWORD
    {
      // NO KEYWORDS AT THIS LEVEL, EVERYTHING IS CONSIDERED A STEP
      // Same naming rules as tests apply
      "step-A" :
      {
        "submit_options" : {}, // EXACT SAME RULES AS ABOVE APPLY (see the pattern?)
        // ADDITIONAL KEYWORDS
         
        // REQUIRED KEYWORD
        // Script to run, not limited to `sh`. Executed from root or working_directory if specified
        "command"        : "filepath/to/script/to/run/from_root_or_workingDir.sh",
        
        // Similar layout to argpack argument listing, but this is not an argpack
        // this list is ALWAYS FIRST before any and all argpacks
        "arguments"      : [ "also", "a list of arguments" ],
        
        // Specify and determine the inter-dependency order of steps
        // NO CIRCULAR OR DEADLOCK PROTECTION LOGIC EXISTS SO BE CAREFUL TO SET THIS CORRECTLY
        "dependencies" :
        {
          // dict of step names verbatim and dependency mapping using 
          // generally standard HPC-dependency nomenclature
          // 
          "step-B" : "afterany" // after|afterok|afternotok|afterany
        }
      },
      "step-B" :
      {
        // submit_options, arguments, and dependecies  are OPTIONAL KEYWORDS
        "command" : "other/command.py"
      }
    }
  },
  "other-test" :
  {
    // submit_options is OPTIONAL KEYWORD
    "steps" :
    {
      // step names only need to be unique within their respective test's "steps" section
      "step-A" : { "command" : "foobar.csh" }
    }
  }
  // ...and so on...
  // ALL KEYWORDS ARE OPTIONAL **EXCEPT** :
  //   [under a test]
  //     - steps
  //   [under a step]
  //     - command
}
```

The bulk of the the configurable power of this layout is generally carried by the `"submit_options"` and its ability to be inherited + overridden, especially on a per-host-FQDN manner. 


## Writing our own test config
The explanation of the file layout is useful for knowing all available options in the test config, but what if you want to just get started or maybe don't even need all the features? What is the simplest way to start? Let's begind with the most barebones config of :
```json
{
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
```


```python
# Get notebook location
shellReturn = !pwd
notebookDirectory = shellReturn[0]
print( "Working from " + notebookDirectory )
```

    Working from /home/runner/work/hpc-workflows/hpc-workflows/tutorials



```bash
%%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "our-test" : { "steps" : { "our-step0" : { "command" : "./tests/scripts/echo_normal.sh" } } }
    }


Now that we have that test config ready, let's run it to make sure it works with our <ins>run script</ins>


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test
```

    Using Python version : 
    3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]
    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing working directory
    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing to run multiple tests
    [file::our-config]    Automatically redirecting our-test to /home/runner/work/hpc-workflows/hpc-workflows/our-test_stdout.log
    [file::our-config]  Spawning process pool of size 4 to perform 1 tests
    [file::our-config]    Launching test our-test
    [file::our-config]    Waiting for tests to complete - BE PATIENT
    [file::our-config]    [SUCCESS] : Test our-test reported success
    [file::our-config]  Test suite complete, writing test results to master log file : 
    [file::our-config]    /home/runner/work/hpc-workflows/hpc-workflows/our-config.log
    [file::our-config]  [SUCCESS] : All tests passed


Excellent! While we won't go into the more complex launch options, we can make the <ins>test</ins> run as if already inside the process pool to see even clearer what would happen in the `_stdout.log` redirect using the `--forceSingle/-fc` option. We could look at the log as well but this way mimics what would happen, and gives you a better idea that nothing truly complex is happening under the hood.


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test --forceSingle # we could shorten this option to -fc
```

    Using Python version : 
    3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]
    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing working directory
    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Preparing working directory
    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Checking if results wait is required
    [test::our-test]      No HPC submissions, no results job added
    [step::our-step0]   Preparing working directory
    [step::our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]   Submitting step our-step0...
    [step::our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step0]     Running command:
    [step::our-step0]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     ***************START our-step0***************
    
    [step::our-step0]     Local step will be redirected to logfile /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    
    [step::our-step0]     ***************STOP our-step0 ***************
    [step::our-step0]   Finished submitting step our-step0
    
    [test::our-test]    Checking remaining steps...
    [test::our-test]    No remaining steps, test submission complete
    [test::our-test]    Outputting results...
    [step::our-step0]   Results for our-step0
    [step::our-step0]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    [step::our-step0]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step0]     [SUCCESS]
    [test::our-test]    Writing relevant logfiles to view in master log file : 
    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-test]    [SUCCESS] : Test our-test completed successfully


One step further is to inline the <ins>step</ins> output. Again, we will not do a deep-dive of launch options here, but instead are building up to a method of running an example <ins>suite of tests</ins> that doesn't rely on opening logfiles. This is mainly to better suit the notebook format. To inline our step we can add `-inlineLocal/-i` to our run script options.


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test -fc -i # using shorthand options
```

    Using Python version : 
    3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]
    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing working directory
    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Preparing working directory
    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Checking if results wait is required
    [test::our-test]      No HPC submissions, no results job added
    [step::our-step0]   Preparing working directory
    [step::our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]   Submitting step our-step0...
    [step::our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step0]     Running command:
    [step::our-step0]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     ***************START our-step0***************
    
    
    TEST echo_normal.sh PASS
    
    [step::our-step0]     ***************STOP our-step0 ***************
    [step::our-step0]   Finished submitting step our-step0
    
    [test::our-test]    Checking remaining steps...
    [test::our-test]    No remaining steps, test submission complete
    [test::our-test]    Outputting results...
    [step::our-step0]   Results for our-step0
    [step::our-step0]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    [step::our-step0]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step0]     [SUCCESS]
    [test::our-test]    Writing relevant logfiles to view in master log file : 
    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-test]    [SUCCESS] : Test our-test completed successfully


## Adding step arguments
Okay, now that we have that printing neatly we can see that our example script doesn't do a whole lot aside from echoing our success <ins>keyphrase</ins> `TEST echo_normal.sh PASS`. Not much of a test?

Let's add some <ins>arguments</ins> and observe how they get routed to the step.


```bash
%%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "our-test" : 
  { 
    "steps" : 
    { 
      "our-step0" : 
      { 
        "command" : "./tests/scripts/echo_normal.sh",
        "arguments" : [ "foobar" ]
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
      "our-test" : 
      { 
        "steps" : 
        { 
          "our-step0" : 
          { 
            "command" : "./tests/scripts/echo_normal.sh",
            "arguments" : [ "foobar" ]
          }
        }
      }
    }


Now we run again, but this time note the changes in both the step command listed after the line starting with `[step::our-step0]...Running command` and the actual step output.


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test -fc -i # using shorthand options
```

    Using Python version : 
    3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]
    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing working directory
    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Preparing working directory
    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Checking if results wait is required
    [test::our-test]      No HPC submissions, no results job added
    [step::our-step0]   Preparing working directory
    [step::our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]   Submitting step our-step0...
    [step::our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step0]     Running command:
    [step::our-step0]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows foobar
    [step::our-step0]     ***************START our-step0***************
    
    foobar
    TEST echo_normal.sh PASS
    
    [step::our-step0]     ***************STOP our-step0 ***************
    [step::our-step0]   Finished submitting step our-step0
    
    [test::our-test]    Checking remaining steps...
    [test::our-test]    No remaining steps, test submission complete
    [test::our-test]    Outputting results...
    [step::our-step0]   Results for our-step0
    [step::our-step0]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    [step::our-step0]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step0]     [SUCCESS]
    [test::our-test]    Writing relevant logfiles to view in master log file : 
    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-test]    [SUCCESS] : Test our-test completed successfully


## Step dependencies
Let's go ahead and add another step, but with this one having a <ins>dependency</ins> on the first causing it to run only after the first has completed.


```bash
%%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "our-test" : 
  { 
    "steps" : 
    { 
      "our-step0" : 
      { 
        "command" : "./tests/scripts/echo_normal.sh",
        "arguments" : [ "foobar" ]
      },
      "our-step1" : 
      { 
        "command" : "./tests/scripts/echo_normal.sh",
        "arguments" : [ "why", "not more", "args?" ],
        "dependencies" : { "our-step0" : "afterany" }
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
      "our-test" : 
      { 
        "steps" : 
        { 
          "our-step0" : 
          { 
            "command" : "./tests/scripts/echo_normal.sh",
            "arguments" : [ "foobar" ]
          },
          "our-step1" : 
          { 
            "command" : "./tests/scripts/echo_normal.sh",
            "arguments" : [ "why", "not more", "args?" ],
            "dependencies" : { "our-step0" : "afterany" }
          }
        }
      }
    }



```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test -fc -i # using shorthand options
```

    Using Python version : 
    3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]
    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing working directory
    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Preparing working directory
    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Checking if results wait is required
    [test::our-test]      No HPC submissions, no results job added
    [step::our-step0]   Preparing working directory
    [step::our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]   Submitting step our-step0...
    [step::our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step0]     Running command:
    [step::our-step0]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows foobar
    [step::our-step0]     ***************START our-step0***************
    
    foobar
    TEST echo_normal.sh PASS
    
    [step::our-step0]     ***************STOP our-step0 ***************
    [step::our-step0]     Notifying children...
    [step::our-step0]   Finished submitting step our-step0
    
    [step::our-step1]   Preparing working directory
    [step::our-step1]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step1]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step1]   Submitting step our-step1...
    [step::our-step1]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step1]     Running command:
    [step::our-step1]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows why "not more" args?
    [step::our-step1]     ***************START our-step1***************
    
    why not more args?
    TEST echo_normal.sh PASS
    
    [step::our-step1]     ***************STOP our-step1 ***************
    [step::our-step1]   Finished submitting step our-step1
    
    [test::our-test]    Checking remaining steps...
    [test::our-test]    No remaining steps, test submission complete
    [test::our-test]    Outputting results...
    [step::our-step0]   Results for our-step0
    [step::our-step0]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    [step::our-step0]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step0]     [SUCCESS]
    [step::our-step1]   Results for our-step1
    [step::our-step1]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step1.log
    [step::our-step1]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step1]     [SUCCESS]
    [test::our-test]    Writing relevant logfiles to view in master log file : 
    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-test]    [SUCCESS] : Test our-test completed successfully


Most of the output should look very similar, but notice that after running `our-step0` there is an additional line now stating `Notifying children...` just before `our-step1` begins to run. This tells us that we have properly tied a dependency between `our-step0` as a parent step and `our-step1` as a dependent child step.

Going a little further, if we look at `our-step1`'s respective `Running command` line we see that `"not more"` is being passed in as one whole argument. This emulates exactly how it was listed in the `"arguments"` for the step.

## Adding argpacks
Imagine we now want to add some additional generalized arguments to both our steps. We have the ability to add these higher-defined arguments as <ins>argpacks</ins> from any level of `"submit_options"` that appears in a step's <ins>ancestry</ins>. For the sake of demonstrating this, we will not add an <ins>argpack</ins> at the highest level, and instead show how it can be inherited from the <ins>test</ins> level


```bash
 %%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "our-test" : 
  { 
    "submit_options" :
    {
      "arguments" :
      {
        "our-default-argpack" : [ "foobar" ]
      }
    },
    "steps" : 
    { 
      "our-step0" : 
      { 
        "command" : "./tests/scripts/echo_normal.sh",
        "arguments" : [ "foobar" ]
      },
      "our-step1" : 
      { 
        "command" : "./tests/scripts/echo_normal.sh",
        "arguments" : [ "why", "not more", "args?" ],
        "dependencies" : { "our-step0" : "afterany" }
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
     "our-test" : 
     { 
       "submit_options" :
       {
         "arguments" :
         {
           "our-default-argpack" : [ "foobar" ]
         }
       },
       "steps" : 
       { 
         "our-step0" : 
         { 
           "command" : "./tests/scripts/echo_normal.sh",
           "arguments" : [ "foobar" ]
         },
         "our-step1" : 
         { 
           "command" : "./tests/scripts/echo_normal.sh",
           "arguments" : [ "why", "not more", "args?" ],
           "dependencies" : { "our-step0" : "afterany" }
         }
       }
     }
    }



```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t our-test -fc -i # using shorthand options

# Clean up all generated logs and files
rm $1/../our-config.json $1/../*.log
```

    Using Python version : 
    3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0]
    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]  Preparing working directory
    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Preparing working directory
    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-test]    Checking if results wait is required
    [test::our-test]      No HPC submissions, no results job added
    [step::our-step0]   Preparing working directory
    [step::our-step0]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step0]   Submitting step our-step0...
    [step::our-step0]     From our-test adding arguments pack 'our-default-argpack' : ['foobar']
    [step::our-step0]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step0]     Running command:
    [step::our-step0]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows foobar foobar
    [step::our-step0]     ***************START our-step0***************
    
    foobar foobar
    TEST echo_normal.sh PASS
    
    [step::our-step0]     ***************STOP our-step0 ***************
    [step::our-step0]     Notifying children...
    [step::our-step0]   Finished submitting step our-step0
    
    [step::our-step1]   Preparing working directory
    [step::our-step1]     Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step1]     Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-step1]   Submitting step our-step1...
    [step::our-step1]     From our-test adding arguments pack 'our-default-argpack' : ['foobar']
    [step::our-step1]     Script : ./tests/scripts/echo_normal.sh
    [step::our-step1]     Running command:
    [step::our-step1]       /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows why "not more" args? foobar
    [step::our-step1]     ***************START our-step1***************
    
    why not more args? foobar
    TEST echo_normal.sh PASS
    
    [step::our-step1]     ***************STOP our-step1 ***************
    [step::our-step1]   Finished submitting step our-step1
    
    [test::our-test]    Checking remaining steps...
    [test::our-test]    No remaining steps, test submission complete
    [test::our-test]    Outputting results...
    [step::our-step0]   Results for our-step0
    [step::our-step0]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0.log
    [step::our-step0]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step0]     [SUCCESS]
    [step::our-step1]   Results for our-step1
    [step::our-step1]     Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step1.log
    [step::our-step1]     Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-step1]     [SUCCESS]
    [test::our-test]    Writing relevant logfiles to view in master log file : 
    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log
    [test::our-test]    [SUCCESS] : Test our-test completed successfully


Now notice how in the step preparation phase between `Submitting step ...` and `Running command` for each respective step we now have a new output of `From our-test adding argument pack 'our-default-argpack'...`. This line tells us both the origin of the <ins>argpack</ins> (which level in our step's <ins>ancestry</ins> provided the defintion) and the effective values of the arguments to be added. Any additional lines of the format `From <origin> adding argument pack '<argpack>'...` would also be listed in the order applied to the step's run command, where `<argpack>` is determining that order.

This <ins>argpack</ins> is always listed after our steps' <ins>arguments</ins> in the step's final command listed - this is important to note!

This concludes our simplest example of a test config that gives enough of an overview to provide users with enough understanding to put together a sufficiently capabale test <ins>suite</ins>
