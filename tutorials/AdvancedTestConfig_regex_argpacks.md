# Utilizing advanced features - Regex <ins>argpacks</ins>
In this tutorial we will be exploring how to use advanced features of the framework. We will be using common terminology found in the repo's README.md - refer to that for any underlined terms that need clarification. Additionally, we will be building upon the material covered in the [Basic Test Config](./BasicTestConfig.ipynb); please review that tutorial if you haven't already. Anything in `"code-quoted"` format refers specifically to the test config, and anything in <ins>underlined</ins> format refers to specific terminology that can be found in the [README.md](../README.md).



```python
# Get notebook location
shellReturn = !pwd
notebookDirectory = shellReturn[0]
print( "Working from " + notebookDirectory )
```

    Working from /home/runner/work/hpc-workflows/hpc-workflows/tutorials


Advanced usage of the json config `"<regex>::<argpack>"` option under `"arguments"` will be the focus of this tutorial :



```python
# Output template file documenting options
from IPython.display import Markdown as md
md( "```jsonc\n" + open( notebookDirectory + "/../.ci/template.json", "r" )
                        .read()
                        .split( "// dict of argpacks" )[1]
                        .split( "// NO MORE KEYWORDS AT THIS LEVEL" )[0] + 
   "\n```" )
```




```jsonc

    "arguments"         :
    {
      // argpacks can be any valid string but all must be unique
      // Recommended to not contain spaces or periods, character pattern
      // '::' is reserved for regex-based argpacks
     
      // list of arguments to this specific <argpack>
      // They DO NOT undergo shell-expansion, so $ENV_VAR will be verbatim passed in
      // Single arguments with spaces should be entered as one string
      "<argpack>"          : [ "list", "of", "arguments" ],
     
      // <regex> should be a valid regex usable by python's re module
      // future definitions will only override the specific full unique match with <regex> included
      "<regex>::<argpack>" : [ "-f", "one whole arg", "-x" ]
    },
    
```



## Regex-based <ins>argpacks</ins>

The following section assumes you have a general understanding of regular expressions. For further reading please refer to :
* [the wikipedia article](https://en.wikipedia.org/wiki/Regular_expression#Basic_concepts)
* an excellent [open-source guide available in many languages](https://github.com/ziishaned/learn-regex)
* a python-specific [`re` introduction](https://docs.python.org/3/howto/regex.html#regex-howto)
* (something I personally find incredibly useful) an [online regex tester with in-depth explanations](https://regex101.com/)

When using the `"<regex>::"`-style <ins>argpack</ins>, it is important to note a few things : 
1. The regex flavor used is python's `re` module
2. The python if-check uses `re.match()` with no flags ([`re` flags](https://docs.python.org/3/library/re.html#flags))
3. __ALL__ inherited arguments are attempted to be applied only when steps begin execution
4. The regex is applied to the full <ins>ancestry</ins>
5. To override the regex-<ins>argpack</ins>, it must match wholly `"<regex>::<argpack>"`
6. The `"<argpack>"` portion of `"<regex>::<argpack>"` is what is used to sort order


For (1) and (2), please refer to the `re` reference links. Simply put, (1) gives wide flexibility on the types of regex constructs that may be used and (2) means the regex is interpreted as literal as possible, i.e. case-sensitive, `^` and `$` only apply to beginning and end of string, and `.` does not match newline.


The importance of (3) is that the cummulative set of arguments inherited in a <ins>step</ins>'s <ins>ancestry</ins> is always applied. When not using regex-<ins>argpack</ins>, one should be careful to only pass things down to appropriate steps. Thus, with the advantages of regex-based conditional application of <ins>argpacks</ins> it is possible to become lazy or sloppy in heavy reliance of this feature. This could be thought of akin to global variables in that solely relying on regexes to route arguments from the top-level `"arguments"` option pollutes the <ins>argpack</ins> namespace unnecessarily. Writing regexes is already complex enough, and having _all_ the regexes applied to _all_ <ins>steps</ins> but only needing them to apply to a few under a single specific <ins>test</ins> may be a disaster waiting to happen and easier solved by scoping the regex to just the <ins>test</ins>'s `"argument"` option.

Point (4) provides corollary to (3): because the regex is applied to the <ins>ancestry</ins>, to make maximal use of this greater flexibility in application of the arguments one should be mindful of test and step naming in conjunction with writing well-defined regexes. Keeping this in mind for a <ins>test config</ins>, one could devise specific naming conventions allowing for specific test or step filtering. 

For instance, if I have a series of steps across multiple tests but all require a specific set of arguments when executing the "build" step of each test, I can extract the common build arguments and place them under a `".*build.*::build_args"` <ins>argpack</ins> if my "build" steps are prefixed with `"build"`. Furthermore, if my build steps across tests slightly differ based on compiler I can name my steps `"build-gcc"`, `"build-icc"`, `"build-clang"` and so on writing other <ins>argpacks</ins> such as `".*-gcc.*::gcc_env"` to load a specific environment.


Finally, (5) and (6) are restatements from the [README.md](../README.md) "How it works"-><ins>Submit Options</ins> subsection. These matter when argument order or overriding an <ins>argpack</ins> is necessary. Generally speaking, if you find you need to often override an <ins>argpack</ins>, whether regex or not (but especially if regex) you are most likely overcomplicating things. Consider rescoping the arguments or moving them to specific `"arguments"` option inside a <ins>step</ins> (not the `"submit_options"`)

### Simple regex-<ins>argpack</ins> config

Let's start with something small : a test with two types of steps - a sender and receiver - with prefixes `send` and `recv`. We'd like for each to identify themselves with a defined string before output.



```bash
%%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "regex-test" : 
  {
    "submit_options" :
    {
      "arguments" :
      {
        ".*send.*::send_prefix" : [ "[send] " ],
        ".*recv.*::recv_prefix" : [ "[recv] " ]
      }
    },
    "steps" :
    {
      "send-step0" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Hello!" ] },
      "recv-step1" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Hello back!" ] },
      "send-step2" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Ping 1" ] },
      "send-step3" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Ping 2" ] },
      "recv-step4" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Pings received" ] }
    }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "regex-test" : 
      {
        "submit_options" :
        {
          "arguments" :
          {
            ".*send.*::send_prefix" : [ "[send] " ],
            ".*recv.*::recv_prefix" : [ "[recv] " ]
          }
        },
        "steps" :
        {
          "send-step0" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Hello!" ] },
          "recv-step1" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Hello back!" ] },
          "send-step2" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Ping 1" ] },
          "send-step3" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Ping 2" ] },
          "recv-step4" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "Pings received" ] }
        }
      }
    }


Let's run this config with `--forceSingle` to our <ins>run script</ins> to see the output easier. Likewise, we will use `--inlineLocal` to avoid the need to peek at log files.


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t regex-test --forceSingle --inlineLocal
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.regex-test]           Preparing working directory
    [test::our-config.regex-test]             Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.regex-test]           Checking if results wait is required...
    [test::our-config.regex-test]             No HPC submissions, no results waiting required
    [step::our-config.regex-test.send-step0] Preparing working directory
    [step::our-config.regex-test.send-step0]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.send-step0]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.send-step0] Submitting step send-step0...
    [step::our-config.regex-test.send-step0]   Gathering argument packs...
    [step::our-config.regex-test.send-step0]     From our-config.regex-test adding arguments pack '.*send.*::send_prefix' : ['[send] ']
    [step::our-config.regex-test.send-step0]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.send-step0]   Running command:
    [step::our-config.regex-test.send-step0]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows Hello! "[send] "
    [step::our-config.regex-test.send-step0]   ***************START send-step0***************
    
    Hello! [send]
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.send-step0]   ***************STOP send-step0***************
    [step::our-config.regex-test.send-step0] Finished submitting step send-step0
    
    [test::our-config.regex-test]           Checking remaining steps...
    [step::our-config.regex-test.recv-step1] Preparing working directory
    [step::our-config.regex-test.recv-step1]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.recv-step1]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.recv-step1] Submitting step recv-step1...
    [step::our-config.regex-test.recv-step1]   Gathering argument packs...
    [step::our-config.regex-test.recv-step1]     From our-config.regex-test adding arguments pack '.*recv.*::recv_prefix' : ['[recv] ']
    [step::our-config.regex-test.recv-step1]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.recv-step1]   Running command:
    [step::our-config.regex-test.recv-step1]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows "Hello back!" "[recv] "
    [step::our-config.regex-test.recv-step1]   ***************START recv-step1***************
    
    Hello back! [recv]
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.recv-step1]   ***************STOP recv-step1***************
    [step::our-config.regex-test.recv-step1] Finished submitting step recv-step1
    
    [step::our-config.regex-test.send-step2] Preparing working directory
    [step::our-config.regex-test.send-step2]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.send-step2]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.send-step2] Submitting step send-step2...
    [step::our-config.regex-test.send-step2]   Gathering argument packs...
    [step::our-config.regex-test.send-step2]     From our-config.regex-test adding arguments pack '.*send.*::send_prefix' : ['[send] ']
    [step::our-config.regex-test.send-step2]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.send-step2]   Running command:
    [step::our-config.regex-test.send-step2]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows "Ping 1" "[send] "
    [step::our-config.regex-test.send-step2]   ***************START send-step2***************
    
    Ping 1 [send]
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.send-step2]   ***************STOP send-step2***************
    [step::our-config.regex-test.send-step2] Finished submitting step send-step2
    
    [step::our-config.regex-test.send-step3] Preparing working directory
    [step::our-config.regex-test.send-step3]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.send-step3]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.send-step3] Submitting step send-step3...
    [step::our-config.regex-test.send-step3]   Gathering argument packs...
    [step::our-config.regex-test.send-step3]     From our-config.regex-test adding arguments pack '.*send.*::send_prefix' : ['[send] ']
    [step::our-config.regex-test.send-step3]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.send-step3]   Running command:
    [step::our-config.regex-test.send-step3]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows "Ping 2" "[send] "
    [step::our-config.regex-test.send-step3]   ***************START send-step3***************
    
    Ping 2 [send]
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.send-step3]   ***************STOP send-step3***************
    [step::our-config.regex-test.send-step3] Finished submitting step send-step3
    
    [step::our-config.regex-test.recv-step4] Preparing working directory
    [step::our-config.regex-test.recv-step4]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.recv-step4]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.recv-step4] Submitting step recv-step4...
    [step::our-config.regex-test.recv-step4]   Gathering argument packs...
    [step::our-config.regex-test.recv-step4]     From our-config.regex-test adding arguments pack '.*recv.*::recv_prefix' : ['[recv] ']
    [step::our-config.regex-test.recv-step4]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.recv-step4]   Running command:
    [step::our-config.regex-test.recv-step4]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows "Pings received" "[recv] "
    [step::our-config.regex-test.recv-step4]   ***************START recv-step4***************
    
    Pings received [recv]
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.recv-step4]   ***************STOP recv-step4***************
    [step::our-config.regex-test.recv-step4] Finished submitting step recv-step4
    
    [test::our-config.regex-test]           No remaining steps, test submission complete
    [test::our-config.regex-test]           Outputting results...
    [step::our-config.regex-test.send-step0] Results for send-step0
    [step::our-config.regex-test.send-step0]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.send-step0.log
    [step::our-config.regex-test.send-step0]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.send-step0]   [SUCCESS]
    [step::our-config.regex-test.recv-step1] Results for recv-step1
    [step::our-config.regex-test.recv-step1]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.recv-step1.log
    [step::our-config.regex-test.recv-step1]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.recv-step1]   [SUCCESS]
    [step::our-config.regex-test.send-step2] Results for send-step2
    [step::our-config.regex-test.send-step2]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.send-step2.log
    [step::our-config.regex-test.send-step2]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.send-step2]   [SUCCESS]
    [step::our-config.regex-test.send-step3] Results for send-step3
    [step::our-config.regex-test.send-step3]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.send-step3.log
    [step::our-config.regex-test.send-step3]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.send-step3]   [SUCCESS]
    [step::our-config.regex-test.recv-step4] Results for recv-step4
    [step::our-config.regex-test.recv-step4]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.recv-step4.log
    [step::our-config.regex-test.recv-step4]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.recv-step4]   [SUCCESS]
    [test::our-config.regex-test]           Writing relevant logfiles to view in master log file : 
    [test::our-config.regex-test]             /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.log
    [test::our-config.regex-test]           [SUCCESS] : Test regex-test completed successfully


When inspecting the output, we do see in the lines following `Submitting step <stepname>...` where <ins>argpacks</ins> are applied the appropriate prefix is selected, but our prefix is being applied as a suffix. Even more explicit, the line after `Running command:` verbatim outputs the command and arguments showing two argument strings being supplied with our "prefix" last. Not quite what we wanted...

<div class="alert alert-block alert-info">
<b>Recall:</b>
The order of <ins>arguments</ins> applied is step-specifics first, then all cummulative <ins>argpacks</ins> from <code>"submit_options"</code> in alphabetical order with conflicts resolved by order of first appearance.
</div>


When applied to a scipt in a manner that is expected, the regex-<ins>argpacks</ins> can become a very powerful feature. Let's further explore how one might apply this to a broader scope of procedures.

### Advanced regex-<ins>argpack</ins> config

To get a feel for how best the regex feature of <ins>argpacks</ins> may be used, we will "build" a more complex set of <ins>steps</ins> that wouldn't just echo out the arguments. The term "build" here should be taken figuratively, as actually developing the logic to be outlined is beyond the scope of this tutorial. We will still be using the `echo_normal.sh` script for ease of use.

First, assume we have a build system (CMake, Make, etc.) who can alternate build types based on flags or configuration inputs. Assuming builds can be run in parallel, we _could_ have each build test run as separate <ins>tests</ins> unto themselves. However, these could also be categorically one <ins>test</ins> -  a compilation test. Let's do just that with the following assumptions:
* `build.sh` can facilitate our flags into the corresponding build system
* `-o` determines the build output location
* `-d` sets debug mode
* `--mpi` sets build with MPI
* `--omp` sets build with OpenMP
* `--double` sets build with double precision
* `-a` enables feature A
* `-b` enables feature B
* `-c` enables feature C which is mutually exclusive with A

We don't want a combination of every option, just a select few for our most critical tests. 



```bash
%%bash -s "$notebookDirectory"
cat << EOF > $1/../our-config.json
{
  "regex-test" : 
  {
    "submit_options" :
    {
      "arguments" :
      {
        ".*dbg.*::dbg_flag" : [ "-d" ],
        ".*mpi.*::mpi_flag" : [ "--mpi" ],
        ".*omp.*::omp_flag" : [ "--omp" ],
        ".*fp64.*::fp64_flag" : [ "--double" ],
        ".*ft[^A]*A.*::feature_a" : [ "-a" ],
        ".*ft[^B]*B.*::feature_b" : [ "-b" ],
        ".*ft[^C]*C.*::feature_b" : [ "-c" ]
      }
    },
    "steps" :
    {
      "build-omp-fp32-dbg"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-dbg" ] },
      "build-omp-fp32-ftA"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-ftA" ] },
      "build-omp-fp32-ftAB" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-ftAB" ] },
      "build-omp-fp32-ftBC" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-ftBC" ] },
      "build-omp-fp64-ftB"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp64-ftB" ] },
      "build-mpi-fp32-dbg"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-mpi-fp32-dbg" ] },
      "build-mpi-fp32"      : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-mpi-fp32" ] },
      "build-mpi-fp64"      : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-mpi-fp64" ] }
    }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :
    {
      "regex-test" : 
      {
        "submit_options" :
        {
          "arguments" :
          {
            ".*dbg.*::dbg_flag" : [ "-d" ],
            ".*mpi.*::mpi_flag" : [ "--mpi" ],
            ".*omp.*::omp_flag" : [ "--omp" ],
            ".*fp64.*::fp64_flag" : [ "--double" ],
            ".*ft[^A]*A.*::feature_a" : [ "-a" ],
            ".*ft[^B]*B.*::feature_b" : [ "-b" ],
            ".*ft[^C]*C.*::feature_b" : [ "-c" ]
          }
        },
        "steps" :
        {
          "build-omp-fp32-dbg"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-dbg" ] },
          "build-omp-fp32-ftA"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-ftA" ] },
          "build-omp-fp32-ftAB" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-ftAB" ] },
          "build-omp-fp32-ftBC" : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp32-ftBC" ] },
          "build-omp-fp64-ftB"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-omp-fp64-ftB" ] },
          "build-mpi-fp32-dbg"  : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-mpi-fp32-dbg" ] },
          "build-mpi-fp32"      : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-mpi-fp32" ] },
          "build-mpi-fp64"      : { "command" : "./tests/scripts/echo_normal.sh", "arguments" : [ "-o", "build-mpi-fp64" ] }
        }
      }
    }


Let's run this code and see how flags are routed to the appropriate tests.


```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -t regex-test --forceSingle --inlineLocal
```

    Using Python version : 
    3.10.12 (main, Sep 11 2024, 15:47:36) [GCC 11.4.0]
    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)
    [file::our-config]                      Root directory is : /home/runner/work/hpc-workflows/hpc-workflows
    [file::our-config]                      Preparing working directory
    [file::our-config]                        Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.regex-test]           Preparing working directory
    [test::our-config.regex-test]             Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [test::our-config.regex-test]           Checking if results wait is required...
    [test::our-config.regex-test]             No HPC submissions, no results waiting required
    [step::our-config.regex-test.build-omp-fp32-dbg] Preparing working directory
    [step::our-config.regex-test.build-omp-fp32-dbg]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-dbg]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-dbg] Submitting step build-omp-fp32-dbg...
    [step::our-config.regex-test.build-omp-fp32-dbg]   Gathering argument packs...
    [step::our-config.regex-test.build-omp-fp32-dbg]     From our-config.regex-test adding arguments pack '.*dbg.*::dbg_flag' : ['-d']
    [step::our-config.regex-test.build-omp-fp32-dbg]     From our-config.regex-test adding arguments pack '.*omp.*::omp_flag' : ['--omp']
    [step::our-config.regex-test.build-omp-fp32-dbg]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-omp-fp32-dbg]   Running command:
    [step::our-config.regex-test.build-omp-fp32-dbg]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-omp-fp32-dbg -d --omp
    [step::our-config.regex-test.build-omp-fp32-dbg]   ***************START build-omp-fp32-dbg***************
    
    -o build-omp-fp32-dbg -d --omp
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-omp-fp32-dbg]   ***************STOP build-omp-fp32-dbg***************
    [step::our-config.regex-test.build-omp-fp32-dbg] Finished submitting step build-omp-fp32-dbg
    
    [test::our-config.regex-test]           Checking remaining steps...
    [step::our-config.regex-test.build-omp-fp32-ftA] Preparing working directory
    [step::our-config.regex-test.build-omp-fp32-ftA]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-ftA]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-ftA] Submitting step build-omp-fp32-ftA...
    [step::our-config.regex-test.build-omp-fp32-ftA]   Gathering argument packs...
    [step::our-config.regex-test.build-omp-fp32-ftA]     From our-config.regex-test adding arguments pack '.*ft[^A]*A.*::feature_a' : ['-a']
    [step::our-config.regex-test.build-omp-fp32-ftA]     From our-config.regex-test adding arguments pack '.*omp.*::omp_flag'       : ['--omp']
    [step::our-config.regex-test.build-omp-fp32-ftA]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-omp-fp32-ftA]   Running command:
    [step::our-config.regex-test.build-omp-fp32-ftA]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-omp-fp32-ftA -a --omp
    [step::our-config.regex-test.build-omp-fp32-ftA]   ***************START build-omp-fp32-ftA***************
    
    -o build-omp-fp32-ftA -a --omp
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-omp-fp32-ftA]   ***************STOP build-omp-fp32-ftA***************
    [step::our-config.regex-test.build-omp-fp32-ftA] Finished submitting step build-omp-fp32-ftA
    
    [step::our-config.regex-test.build-omp-fp32-ftAB] Preparing working directory
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-ftAB] Submitting step build-omp-fp32-ftAB...
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Gathering argument packs...
    [step::our-config.regex-test.build-omp-fp32-ftAB]     From our-config.regex-test adding arguments pack '.*ft[^A]*A.*::feature_a' : ['-a']
    [step::our-config.regex-test.build-omp-fp32-ftAB]     From our-config.regex-test adding arguments pack '.*ft[^B]*B.*::feature_b' : ['-b']
    [step::our-config.regex-test.build-omp-fp32-ftAB]     From our-config.regex-test adding arguments pack '.*omp.*::omp_flag'       : ['--omp']
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Running command:
    [step::our-config.regex-test.build-omp-fp32-ftAB]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-omp-fp32-ftAB -a -b --omp
    [step::our-config.regex-test.build-omp-fp32-ftAB]   ***************START build-omp-fp32-ftAB***************
    
    -o build-omp-fp32-ftAB -a -b --omp
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-omp-fp32-ftAB]   ***************STOP build-omp-fp32-ftAB***************
    [step::our-config.regex-test.build-omp-fp32-ftAB] Finished submitting step build-omp-fp32-ftAB
    
    [step::our-config.regex-test.build-omp-fp32-ftBC] Preparing working directory
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp32-ftBC] Submitting step build-omp-fp32-ftBC...
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Gathering argument packs...
    [step::our-config.regex-test.build-omp-fp32-ftBC]     From our-config.regex-test adding arguments pack '.*ft[^B]*B.*::feature_b' : ['-b']
    [step::our-config.regex-test.build-omp-fp32-ftBC]     From our-config.regex-test adding arguments pack '.*ft[^C]*C.*::feature_b' : ['-c']
    [step::our-config.regex-test.build-omp-fp32-ftBC]     From our-config.regex-test adding arguments pack '.*omp.*::omp_flag'       : ['--omp']
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Running command:
    [step::our-config.regex-test.build-omp-fp32-ftBC]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-omp-fp32-ftBC -b -c --omp
    [step::our-config.regex-test.build-omp-fp32-ftBC]   ***************START build-omp-fp32-ftBC***************
    
    -o build-omp-fp32-ftBC -b -c --omp
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-omp-fp32-ftBC]   ***************STOP build-omp-fp32-ftBC***************
    [step::our-config.regex-test.build-omp-fp32-ftBC] Finished submitting step build-omp-fp32-ftBC
    
    [step::our-config.regex-test.build-omp-fp64-ftB] Preparing working directory
    [step::our-config.regex-test.build-omp-fp64-ftB]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp64-ftB]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-omp-fp64-ftB] Submitting step build-omp-fp64-ftB...
    [step::our-config.regex-test.build-omp-fp64-ftB]   Gathering argument packs...
    [step::our-config.regex-test.build-omp-fp64-ftB]     From our-config.regex-test adding arguments pack '.*ft[^B]*B.*::feature_b' : ['-b']
    [step::our-config.regex-test.build-omp-fp64-ftB]     From our-config.regex-test adding arguments pack '.*fp64.*::fp64_flag'     : ['--double']
    [step::our-config.regex-test.build-omp-fp64-ftB]     From our-config.regex-test adding arguments pack '.*omp.*::omp_flag'       : ['--omp']
    [step::our-config.regex-test.build-omp-fp64-ftB]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-omp-fp64-ftB]   Running command:
    [step::our-config.regex-test.build-omp-fp64-ftB]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-omp-fp64-ftB -b --double --omp
    [step::our-config.regex-test.build-omp-fp64-ftB]   ***************START build-omp-fp64-ftB***************
    
    -o build-omp-fp64-ftB -b --double --omp
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-omp-fp64-ftB]   ***************STOP build-omp-fp64-ftB***************
    [step::our-config.regex-test.build-omp-fp64-ftB] Finished submitting step build-omp-fp64-ftB
    
    [step::our-config.regex-test.build-mpi-fp32-dbg] Preparing working directory
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-mpi-fp32-dbg] Submitting step build-mpi-fp32-dbg...
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Gathering argument packs...
    [step::our-config.regex-test.build-mpi-fp32-dbg]     From our-config.regex-test adding arguments pack '.*dbg.*::dbg_flag' : ['-d']
    [step::our-config.regex-test.build-mpi-fp32-dbg]     From our-config.regex-test adding arguments pack '.*mpi.*::mpi_flag' : ['--mpi']
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Running command:
    [step::our-config.regex-test.build-mpi-fp32-dbg]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-mpi-fp32-dbg -d --mpi
    [step::our-config.regex-test.build-mpi-fp32-dbg]   ***************START build-mpi-fp32-dbg***************
    
    -o build-mpi-fp32-dbg -d --mpi
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-mpi-fp32-dbg]   ***************STOP build-mpi-fp32-dbg***************
    [step::our-config.regex-test.build-mpi-fp32-dbg] Finished submitting step build-mpi-fp32-dbg
    
    [step::our-config.regex-test.build-mpi-fp32] Preparing working directory
    [step::our-config.regex-test.build-mpi-fp32]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-mpi-fp32]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-mpi-fp32] Submitting step build-mpi-fp32...
    [step::our-config.regex-test.build-mpi-fp32]   Gathering argument packs...
    [step::our-config.regex-test.build-mpi-fp32]     From our-config.regex-test adding arguments pack '.*mpi.*::mpi_flag' : ['--mpi']
    [step::our-config.regex-test.build-mpi-fp32]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-mpi-fp32]   Running command:
    [step::our-config.regex-test.build-mpi-fp32]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-mpi-fp32 --mpi
    [step::our-config.regex-test.build-mpi-fp32]   ***************START build-mpi-fp32***************
    
    -o build-mpi-fp32 --mpi
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-mpi-fp32]   ***************STOP build-mpi-fp32***************
    [step::our-config.regex-test.build-mpi-fp32] Finished submitting step build-mpi-fp32
    
    [step::our-config.regex-test.build-mpi-fp64] Preparing working directory
    [step::our-config.regex-test.build-mpi-fp64]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-mpi-fp64]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows
    [step::our-config.regex-test.build-mpi-fp64] Submitting step build-mpi-fp64...
    [step::our-config.regex-test.build-mpi-fp64]   Gathering argument packs...
    [step::our-config.regex-test.build-mpi-fp64]     From our-config.regex-test adding arguments pack '.*fp64.*::fp64_flag' : ['--double']
    [step::our-config.regex-test.build-mpi-fp64]     From our-config.regex-test adding arguments pack '.*mpi.*::mpi_flag'   : ['--mpi']
    [step::our-config.regex-test.build-mpi-fp64]   Script : ./tests/scripts/echo_normal.sh
    [step::our-config.regex-test.build-mpi-fp64]   Running command:
    [step::our-config.regex-test.build-mpi-fp64]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh fv-az883-167.sk5y2rh0qbtexpi1qont3x1wzb.ex.internal.cloudapp.net /home/runner/work/hpc-workflows/hpc-workflows -o build-mpi-fp64 --double --mpi
    [step::our-config.regex-test.build-mpi-fp64]   ***************START build-mpi-fp64***************
    
    -o build-mpi-fp64 --double --mpi
    TEST echo_normal.sh PASS
    
    [step::our-config.regex-test.build-mpi-fp64]   ***************STOP build-mpi-fp64***************
    [step::our-config.regex-test.build-mpi-fp64] Finished submitting step build-mpi-fp64
    
    [test::our-config.regex-test]           No remaining steps, test submission complete
    [test::our-config.regex-test]           Outputting results...
    [step::our-config.regex-test.build-omp-fp32-dbg] Results for build-omp-fp32-dbg
    [step::our-config.regex-test.build-omp-fp32-dbg]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-omp-fp32-dbg.log
    [step::our-config.regex-test.build-omp-fp32-dbg]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-omp-fp32-dbg]   [SUCCESS]
    [step::our-config.regex-test.build-omp-fp32-ftA] Results for build-omp-fp32-ftA
    [step::our-config.regex-test.build-omp-fp32-ftA]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-omp-fp32-ftA.log
    [step::our-config.regex-test.build-omp-fp32-ftA]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-omp-fp32-ftA]   [SUCCESS]
    [step::our-config.regex-test.build-omp-fp32-ftAB] Results for build-omp-fp32-ftAB
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-omp-fp32-ftAB.log
    [step::our-config.regex-test.build-omp-fp32-ftAB]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-omp-fp32-ftAB]   [SUCCESS]
    [step::our-config.regex-test.build-omp-fp32-ftBC] Results for build-omp-fp32-ftBC
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-omp-fp32-ftBC.log
    [step::our-config.regex-test.build-omp-fp32-ftBC]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-omp-fp32-ftBC]   [SUCCESS]
    [step::our-config.regex-test.build-omp-fp64-ftB] Results for build-omp-fp64-ftB
    [step::our-config.regex-test.build-omp-fp64-ftB]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-omp-fp64-ftB.log
    [step::our-config.regex-test.build-omp-fp64-ftB]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-omp-fp64-ftB]   [SUCCESS]
    [step::our-config.regex-test.build-mpi-fp32-dbg] Results for build-mpi-fp32-dbg
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-mpi-fp32-dbg.log
    [step::our-config.regex-test.build-mpi-fp32-dbg]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-mpi-fp32-dbg]   [SUCCESS]
    [step::our-config.regex-test.build-mpi-fp32] Results for build-mpi-fp32
    [step::our-config.regex-test.build-mpi-fp32]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-mpi-fp32.log
    [step::our-config.regex-test.build-mpi-fp32]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-mpi-fp32]   [SUCCESS]
    [step::our-config.regex-test.build-mpi-fp64] Results for build-mpi-fp64
    [step::our-config.regex-test.build-mpi-fp64]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.build-mpi-fp64.log
    [step::our-config.regex-test.build-mpi-fp64]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'
    [step::our-config.regex-test.build-mpi-fp64]   [SUCCESS]
    [test::our-config.regex-test]           Writing relevant logfiles to view in master log file : 
    [test::our-config.regex-test]             /home/runner/work/hpc-workflows/hpc-workflows/our-config.regex-test.log
    [test::our-config.regex-test]           [SUCCESS] : Test regex-test completed successfully


By solely controlling the apt naming of our steps we can get the correct flags applied to the respective step. This, of course, is a heavily simplified example.
