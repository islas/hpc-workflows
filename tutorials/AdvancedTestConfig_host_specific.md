# Utilizing advanced features - Host-specific `"submit_options"`
In this tutorial we will be exploring how to use advanced features of the framework. We will be using common terminology found in the repo's README.md - refer to that for any underlined terms that need clarification. Additionally, we will be building upon the material covered in the [Basic Test Config](./BasicTestConfig.ipynb); please review that tutorial if you haven't already. Anything in `"code-quoted"` format refers specifically to the test config, and anything in <ins>underlined</ins> format refers to specific terminology that can be found in the [README.md](../README.md).



```python
# Get notebook location
shellReturn = !pwd
notebookDirectory = shellReturn[0]
print( "Working from " + notebookDirectory )
```

    Working from /home/runner/work/hpc-workflows/hpc-workflows/tutorials


Advanced usage of the json config options `"<match-fqdn>"` under `"submit_options"` will be the focus of this tutorial :



```python
# Output template file documenting options
from IPython.display import Markdown as md
md( "```jsonc\n" + open( notebookDirectory + "/../.ci/template.json", "r" )
                        .read()
                        .split( "]\n    }," )[1]
                        .split( "\"<may-match-other-host>\"" )[0] + 
   "\n```" )
```




```jsonc

    // NO MORE KEYWORDS AT THIS LEVEL, ANYTHING ELSE IS CONSIDERED A HOST-SPECIFIC SUBSET
    // subset will be applied if key is found inside host FQDN
    // NOT REGEX - this is just python `if key in fqdn`, first one found is applied
    "<match-fqdn>" :      
    {
      // Any of the "submit_options" KEYWORDS - host-specific subsets cannot be nested
      // When steps are resolved if a host-specific subset matches it will be applied
      // AFTER all generic submit_options have been applied
    },
    // No limit on number of host-specific subsets as long as they are unique
    
```



## Host-Specific `"submit_options"`

One can conditionally control whether `"submit_options"` are applied based on the FQDN ([fully qualified domain name](https://en.wikipedia.org/wiki/Fully_qualified_domain_name)) of the host running the step. The logic to do so is simple but provides incredible flexibility and power in writing <ins>test configs</ins>. 




```python
# Output template file documenting options
from IPython.display import Markdown as md
md( "```python\n  def selectHostSpecificSubmitOptions" + 
     open( notebookDirectory + "/../.ci/SubmitOptions.py", "r" )
                        .read()
                        .split( "def selectHostSpecificSubmitOptions" )[1]
                        .split( "def format" )[0] + 
   "\n```" )
```




```python
  def selectHostSpecificSubmitOptions( self, forceFQDN=None, print=print ) :
    # Must be valid for this specific host or generically
    fqdn = forceFQDN if forceFQDN else socket.getfqdn() 

    # Have to do string matching rather than in dict
    hostSpecificOptKey = next( ( hostOpt for hostOpt in self.hostSpecificOptions_ if hostOpt in fqdn ), None )

    # Quickly generate a stand-in SubmitOptions in spitting image
    currentSubmitOptions = copy.deepcopy( self )

    if hostSpecificOptKey is not None :
      # Update with host-specifics
      currentSubmitOptions.update( self.hostSpecificOptions_[ hostSpecificOptKey ], print )

    return currentSubmitOptions


  
```



All we do is look at the accummulated `"submit_options"` and override any defaults with the first one that matches our FQDN. You might also notice that we have the ability to force it to appear as if we are a different host. This has some powerful implications that we will cover later, but for now we will us that to show how this all works. As there is no way to predict the hostname of where you might be running this notebook, instead we will say we are running on `tutorials.hpc-workflows.foobar.com`. We'll use the `--forceFQDN/-ff` flag to set our own "hostname" :





```bash
%%bash -s "$notebookDirectory"
$1/../.ci/runner.py $1/../our-config.json -h | \
  tr $'\n' '@' | \
  sed -e 's/[ ]\+-h.*\?directly to stdout/.../g' | \
  sed -e 's/[ ]\+-fs.*/.../g' | \
  tr '@' $'\n'
```

    Using Python version : 


    3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0]


    usage: runner.py [-h] [-t TESTS [TESTS ...]] [-s {PBS,SLURM,LOCAL}]


                     [-a ACCOUNT] [-d DIROFFSET] [-j [JOINHPC]]


                     [-alt [ALTDIRS ...]] [-l LABELLENGTH] [-g GLOBALPREFIX]


                     [-dry] [-nf] [-nw] [-np] [-k KEY] [-p POOL] [-tp THREADPOOL]


                     [-r REDIRECT] [-i] [-ff FORCEFQDN] [-fs]


                     testsConfig


    


    positional arguments:


      testsConfig           JSON file defining set of tests


    


    options:


    ...


      -ff FORCEFQDN, --forceFQDN FORCEFQDN


                            Force the selection of host-specific "submit_options" to use input as the assumed FQDN


    ...

Let's start with a small set of `"submit_options"` that will be our defaults :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "LOCAL",
    "timelimit"  : "00:01:00",
    "arguments"  :
    {
      "data_path" : [ "-p", "/some/local/path/" ]
    }
  },
  "our-test" :
  {
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -ff tutorials.hpc-workflows.foobar.com
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :


    {


      "submit_options" :


      {


        "submission" : "LOCAL",


        "timelimit"  : "00:01:00",


        "arguments"  :


        {


          "data_path" : [ "-p", "/some/local/path/" ]


        }


      },


      "our-test" :


      {


        "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }


      }


    }


    Using Python version : 


    3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0]


    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)


    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows


    [file::our-config]  Preparing working directory


    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [test::our-test]    Preparing working directory


    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [test::our-test]    Checking if results wait is required...


    [test::our-test]      No HPC submissions, no results waiting required


    [step::our-step0-less-nodes] Preparing working directory


    [step::our-step0-less-nodes]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [step::our-step0-less-nodes]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows


    [step::our-step0-less-nodes] Submitting step our-step0-less-nodes...


    [step::our-step0-less-nodes]   Gathering argument packs...


    [step::our-step0-less-nodes]     From our-config adding arguments pack 'data_path' : ['-p', '/some/local/path/']


    [step::our-step0-less-nodes]   Script : ./tests/scripts/echo_normal.sh


    [step::our-step0-less-nodes]   Running command:


    [step::our-step0-less-nodes]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows -p /some/local/path/


    [step::our-step0-less-nodes]   ***************START our-step0-less-nodes***************


    


    -p /some/local/path/


    TEST echo_normal.sh PASS


    


    [step::our-step0-less-nodes]   ***************STOP our-step0-less-nodes***************


    [step::our-step0-less-nodes] Finished submitting step our-step0-less-nodes


    


    [test::our-test]    Checking remaining steps...


    [test::our-test]    No remaining steps, test submission complete


    [test::our-test]    Outputting results...


    [step::our-step0-less-nodes] Results for our-step0-less-nodes


    [step::our-step0-less-nodes]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0-less-nodes.log


    [step::our-step0-less-nodes]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'


    [step::our-step0-less-nodes]   [SUCCESS]


    [test::our-test]    Writing relevant logfiles to view in master log file : 


    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log


    [test::our-test]    [SUCCESS] : Test our-test completed successfully


Looks good, let's start overriding our `"data_path"` <ins>argpack</ins>. Recall that we _could_ override it by providing an appropriate `"submit_options"` at the test or step level, but say we have many steps and tests that will make use of this data path. Likewise, on our `tutorials.hpc-workflows.foobar.com` we have the path set to something specific like `/opt/data/path/`. Instead we want to supply a host-specific designation at the top to be our new default :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "LOCAL",
    "timelimit"  : "00:01:00",
    "arguments"  :
    {
      "data_path" : [ "-p", "/some/local/path/" ]
    },
    "tutorials" :
    {
      "arguments" :
      {
        "data_path" : [ "-p", "/opt/data/path" ]
      }
    }
  },
  "our-test" :
  {
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -ff tutorials.hpc-workflows.foobar.com
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :


    {


      "submit_options" :


      {


        "submission" : "LOCAL",


        "timelimit"  : "00:01:00",


        "arguments"  :


        {


          "data_path" : [ "-p", "/some/local/path/" ]


        },


        "tutorials" :


        {


          "arguments" :


          {


            "data_path" : [ "-p", "/opt/data/path" ]


          }


        }


      },


      "our-test" :


      {


        "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }


      }


    }


    Using Python version : 


    3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0]


    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)


    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows


    [file::our-config]  Preparing working directory


    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [test::our-test]    Preparing working directory


    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [test::our-test]    Checking if results wait is required...


    [test::our-test]      No HPC submissions, no results waiting required


    [step::our-step0-less-nodes] Preparing working directory


    [step::our-step0-less-nodes]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [step::our-step0-less-nodes]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows


    [step::our-step0-less-nodes] Submitting step our-step0-less-nodes...


    [step::our-step0-less-nodes]   Gathering argument packs...


    [step::our-step0-less-nodes]     From our-config adding arguments pack 'data_path' : ['-p', '/opt/data/path']


    [step::our-step0-less-nodes]   Script : ./tests/scripts/echo_normal.sh


    [step::our-step0-less-nodes]   Running command:


    [step::our-step0-less-nodes]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows -p /opt/data/path


    [step::our-step0-less-nodes]   ***************START our-step0-less-nodes***************


    


    -p /opt/data/path


    TEST echo_normal.sh PASS


    


    [step::our-step0-less-nodes]   ***************STOP our-step0-less-nodes***************


    [step::our-step0-less-nodes] Finished submitting step our-step0-less-nodes


    


    [test::our-test]    Checking remaining steps...


    [test::our-test]    No remaining steps, test submission complete


    [test::our-test]    Outputting results...


    [step::our-step0-less-nodes] Results for our-step0-less-nodes


    [step::our-step0-less-nodes]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0-less-nodes.log


    [step::our-step0-less-nodes]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'


    [step::our-step0-less-nodes]   [SUCCESS]


    [test::our-test]    Writing relevant logfiles to view in master log file : 


    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log


    [test::our-test]    [SUCCESS] : Test our-test completed successfully


Notice that our input to the command script is now our host-specific `"arguments"`? Also, we need only match the name with python string [operator `in`](https://docs.python.org/3/reference/expressions.html#membership-test-details). If we then want to override this default for this host at the test level we need to match the previous string verbatim :


```bash
%%bash -s "$notebookDirectory" 
cat << EOF > $1/../our-config.json
{
  "submit_options" :
  {
    "submission" : "LOCAL",
    "timelimit"  : "00:01:00",
    "arguments"  :
    {
      "data_path" : [ "-p", "/some/local/path/" ]
    },
    "tutorials" :
    {
      "arguments" :
      {
        "data_path" : [ "-p", "/opt/data/path" ]
      }
    }
  },
  "our-test" :
  {
    "submit_options" :
    {
      "tutorials" :
      {
        "arguments" :
        {
          "data_path" : [ "-p", "/home/user/data/path" ]
        }
      }
    },
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
EOF

echo "$( realpath $1/../our-config.json ) :"
cat $1/../our-config.json

$1/../.ci/runner.py $1/../our-config.json -t our-test -fs -i -ff tutorials.hpc-workflows.foobar.com
```

    /home/runner/work/hpc-workflows/hpc-workflows/our-config.json :


    {


      "submit_options" :


      {


        "submission" : "LOCAL",


        "timelimit"  : "00:01:00",


        "arguments"  :


        {


          "data_path" : [ "-p", "/some/local/path/" ]


        },


        "tutorials" :


        {


          "arguments" :


          {


            "data_path" : [ "-p", "/opt/data/path" ]


          }


        }


      },


      "our-test" :


      {


        "submit_options" :


        {


          "tutorials" :


          {


            "arguments" :


            {


              "data_path" : [ "-p", "/home/user/data/path" ]


            }


          }


        },


        "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }


      }


    }


    Using Python version : 


    3.10.12 (main, Nov 20 2023, 15:14:05) [GCC 11.4.0]


    Inline stdout for steps requested, but steps' threadpool is greater than 1 - forcing threadpool to size 1 (serial)


    [file::our-config]  Root directory is : /home/runner/work/hpc-workflows/hpc-workflows


    [file::our-config]  Preparing working directory


    [file::our-config]    Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [test::our-test]    Preparing working directory


    [test::our-test]      Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [test::our-test]    Checking if results wait is required...


    [test::our-test]      No HPC submissions, no results waiting required


    [step::our-step0-less-nodes] Preparing working directory


    [step::our-step0-less-nodes]   Running from root directory /home/runner/work/hpc-workflows/hpc-workflows


    [step::our-step0-less-nodes]   Current directory : /home/runner/work/hpc-workflows/hpc-workflows


    [step::our-step0-less-nodes] Submitting step our-step0-less-nodes...


    [step::our-step0-less-nodes]   Gathering argument packs...


    [step::our-step0-less-nodes]     From our-config.our-test adding arguments pack 'data_path' : ['-p', '/home/user/data/path']


    [step::our-step0-less-nodes]   Script : ./tests/scripts/echo_normal.sh


    [step::our-step0-less-nodes]   Running command:


    [step::our-step0-less-nodes]     /home/runner/work/hpc-workflows/hpc-workflows/tests/scripts/echo_normal.sh /home/runner/work/hpc-workflows/hpc-workflows -p /home/user/data/path


    [step::our-step0-less-nodes]   ***************START our-step0-less-nodes***************


    


    -p /home/user/data/path


    TEST echo_normal.sh PASS


    


    [step::our-step0-less-nodes]   ***************STOP our-step0-less-nodes***************


    [step::our-step0-less-nodes] Finished submitting step our-step0-less-nodes


    


    [test::our-test]    Checking remaining steps...


    [test::our-test]    No remaining steps, test submission complete


    [test::our-test]    Outputting results...


    [step::our-step0-less-nodes] Results for our-step0-less-nodes


    [step::our-step0-less-nodes]   Opening log file /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.our-step0-less-nodes.log


    [step::our-step0-less-nodes]   Checking last line for success <KEY PHRASE> of format 'TEST ((?:\w+|[.-])+) PASS'


    [step::our-step0-less-nodes]   [SUCCESS]


    [test::our-test]    Writing relevant logfiles to view in master log file : 


    [test::our-test]      /home/runner/work/hpc-workflows/hpc-workflows/our-config.our-test.log


    [test::our-test]    [SUCCESS] : Test our-test completed successfully


As shown in the .ci/template.json, host-specific `"submit_options"` must first appear in a parent `"submit_options"` entry but do not need the keyword themselves as their unique name counts as that. 

All the rules of `"submit_options"` (inheritance, overriding, etc.) apply here as well to their respective unique name entry. Thus, if we were to have written `"hpc-workflows"` as our host-specific name match for trying to override at the test level it would count as a separate entry. And since the selection process only takes the first one found that matches (entry names are preserved in the order they appear in the config) we would not get the expected results. 

If this doesn't make sense try running the following config and seeing what the data path is set to when `"tutorials"` host-specifics exists as well as when it is removed :
```json
{
  "submit_options" :
  {
    "submission" : "LOCAL",
    "timelimit"  : "00:01:00",
    "arguments"  :
    {
      "data_path" : [ "-p", "/some/local/path/" ]
    },
    "tutorials" :
    {
      "arguments" :
      {
        "data_path" : [ "-p", "/opt/data/path" ]
      }
    }
  },
  "our-test" :
  {
    "submit_options" :
    {
      "hpc-workflows" :
      {
        "arguments" :
        {
          "data_path" : [ "-p", "/home/user/data/path" ]
        }
      }
    },
    "steps" : { "our-step0-less-nodes" : { "command" : "./tests/scripts/echo_normal.sh" } }
  }
}
```

Since we can actually force-set the pressumed FQDN, we can technically use these host-specific `"submit_options"` to act more like selectable configurations, essentially. This is by design and is encouraged if used appropriately. The selection based on FQDN is more of a convenience to be the default selection criteria.
