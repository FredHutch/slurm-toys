slurm-toys (aka awesome-slurm)
==============================

A collection of slurm command line tools and wrappers mostly found on github

why slurm-toys
--------------

The purpose of slurm-toys is to package useful SLURM helper tools written in Python 3 or Shell and
publish them into a single package on PyPI

currently integrated toys
-------------------------

slurm-limiter
~~~~~~~~~~~~~

HPC clusters are optimized to maximize utilization for batch jobs. FairShare helps to ensure that
all users get an appropriate amount of resources over time. However FairShare can only influence
jobs that have not started yet. If a cluster is used 100% by "large" users, "small" users become
unhappy because they may not be able to get a single node ad hoc. Currently the only solution to
this problem appears to be setting hard account limits. Unfortunatelty these limits are often set
too high when a cluster is busy and too low when it is idle. slurm-limiter addresses this problem by
dynamically adjusting the limits based on overal partition/ queue load.

If you want a responsive HPC cluster this should take no longer than 5 sec:

::

    ~$ time srun hostname 
    srun: job 61004624 queued and waiting for resources
    srun: job 61004624 has been allocated resources
    gizmof171

    real    0m1.668s
    user    0m0.044s
    sys 0m0.012s

example use in a cron job, running every 20 min:

::

    */20 * * * * root (  ml Python/3.6.4-foss-2016b-fh1; /app/bin/slurm-limiter -p campus \ 
                       --error-email=sysadmin\@institute.org --minaccountlimit=50 --maxaccountlimit=350 \ 
                       --slaaccountlimit=300 --changestep=50 --maxpercentuse=90 \
                       --minidlenodes=5 ) >>/var/tmp/slurm-limiter.log 2>&1

example output to syslog:

::

    ~$ grep slurm-limiter: /var/log/syslog
    Apr 15 09:40:03 gizmo-ctld slurm-limiter: INFO:slurm-limiter.85: Cores: running=689, pending=3299, total=1180, Usage=58 %, Limits: 350 / 370, Nodes: idle=101
    Apr 15 10:00:03 gizmo-ctld slurm-limiter: INFO:slurm-limiter.85: Cores: running=689, pending=3274, total=1180, Usage=58 %, Limits: 350 / 370, Nodes: idle=101
    Apr 15 10:20:03 gizmo-ctld slurm-limiter: INFO:slurm-limiter.85: Cores: running=680, pending=3241, total=1180, Usage=57 %, Limits: 350 / 370, Nodes: idle=102
    Apr 15 10:40:03 gizmo-ctld slurm-limiter: INFO:slurm-limiter.85: Cores: running=680, pending=3219, total=1180, Usage=57 %, Limits: 350 / 370, Nodes: idle=102

output of slurm-limiter --help

::

    ~$ slurm-limiter --help
    usage: slurm-limiter [-h] [--debug] [--error-email ERROREMAIL]
                         [--cluster CLUSTER] [--partition PARTITION]
                         [--feature FEATURE] [--qos QOS]
                         [--maxaccountlimit MAXLIMIT] [--minaccountlimit MINLIMIT]
                         [--slaaccountlimit SLALIMIT]
                         [--userlimitoffset USERLIMITOFFSET]
                         [--changestep CHANGESTEP] [--minpending MINPENDING]
                         [--maxpercentuse MAXPERCENTUSE]
                         [--minidlenodes MINIDLENODES]

    slurm-limiter checks the current util of a slurm cluster and adjusts the
    account and user limits dynamically within certain range

    optional arguments:
      -h, --help            show this help message and exit
      --debug, -d           verbose output for all commands
      --error-email ERROREMAIL, -e ERROREMAIL
                            send errors to this email address.
      --cluster CLUSTER, -M CLUSTER
                            name of the slurm cluster, (default: current cluster)
      --partition PARTITION, -p PARTITION
                            partition of the slurm cluster (default: entire
                            cluster)
      --feature FEATURE, -f FEATURE
                            filter for only this slurm feature
      --qos QOS, -q QOS     slurm QOS to use for changing account limits (default:
                            public)
      --maxaccountlimit MAXLIMIT, -x MAXLIMIT
                            maximum account limit, never go above this (default:
                            300)
      --minaccountlimit MINLIMIT, -n MINLIMIT
                            minimum account limit, never go below this (default:
                            100)
      --slaaccountlimit SLALIMIT, -t SLALIMIT
                            min SLA limit that has been committed to customers,
                            notify via email if breached (default: 150)
      --userlimitoffset USERLIMITOFFSET, -o USERLIMITOFFSET
                            offset of userlimit from account limit, set a negative
                            number for a userlimit lower than account limit
                            (default: 20)
      --changestep CHANGESTEP, -s CHANGESTEP
                            increase or decrease the limit by this # of cores
                            (default: 10)
      --minpending MINPENDING, -i MINPENDING
                            minimum number of jobs that have to be pending to take
                            action (default: 50)
      --maxpercentuse MAXPERCENTUSE, -u MAXPERCENTUSE
                            maximum allowed % usage in this cluster or partition
                            Throttle QOS down by --changestep if exceeded.
                            (default: 90)
      --minidlenodes MINIDLENODES, -w MINIDLENODES
                            critical minimum number of idle nodes. Throttle QOS
                            down to --minaccountlimit if exceeded. (default: 5)

future toys
-----------

in the future we can integrate other tools, predominantly stuff found on github

https://github.com/search?l=Python&p=1&q=slurm+&type=Repositories

https://github.com/search?l=Shell&q=slurm+&type=Repositories

new tool
~~~~~~~~
