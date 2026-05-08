# End-to-End Demonstration

This document walks through the Stage 1 HTCondor noun-verb CLI commands,
showing a realistic workflow from job submission through monitoring and cleanup.

---

## 1. Explore the CLI

```bash
$ htcondor --help
usage: htcondor [-h] [-v] {jobs,dag,project,template,log,pool} ...

The HTCondor command-line interface.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Print extra output

nouns:
  Use 'htcondor <noun> --help' for more information on a noun.

  {jobs,dag,project,template,log,pool}
    jobs                Create and interact with HTCondor job(s)
    dag                 Create and interact with HTCondor DAGMan workflows
    project             Create and interact with a 'project' directory
    template            Generate job descriptions from templates, interact with templates list
    log                 Query and interact with your HTCondor logbook
    pool                Query and interact with your pool of resources
```

```bash
$ htcondor jobs --help
usage: htcondor jobs [-h] {submit,status,report,interact,hold,release,remove,edit,help} ...

options:
  -h, --help            show this help message and exit

verbs:
  Use 'htcondor jobs <verb> --help' for details.

  {submit,status,report,interact,hold,release,remove,edit,help}
    submit              Submit HTCondor job(s)
    status              Print details about HTCondor job(s)
    report              Print summary report of HTCondor job(s)
    interact            Log in to or start an interactive HTCondor job
    hold                Interrupt and prevent HTCondor job(s) from running
    release             Remove a 'hold' and allow HTCondor job(s) to run again
    remove              Remove HTCondor job(s) permanently
    edit                Edit properties of a job
    help                Print this help text
```

---

## 2. Check available resources

```bash
$ htcondor pool status
Pool Status
────────────────────────────────────────

NAME                       OPSYS  ARCH    STATE      ACTIVITY  LOAD  CPUS  MEMORY
slot1@e1001.chtc.wisc.edu  LINUX  X86_64  Claimed    Busy      1.02     8   32 GB
slot1@e1002.chtc.wisc.edu  LINUX  X86_64  Claimed    Busy      0.98     8   32 GB
slot1@e1003.chtc.wisc.edu  LINUX  X86_64  Unclaimed  Idle      0.01     8   32 GB
slot1@e1004.chtc.wisc.edu  LINUX  X86_64  Unclaimed  Idle      0.00    16   64 GB
slot1@e1005.chtc.wisc.edu  LINUX  X86_64  Claimed    Busy      1.05     8   32 GB
slot1@e1006.chtc.wisc.edu  LINUX  X86_64  Unclaimed  Idle      0.02     8   32 GB
gpu01.chtc.wisc.edu        LINUX  X86_64  Claimed    Busy      4.20    32  128 GB

Total: 7 machines, 88 CPUs, 352 GB  (4 claimed, 3 unclaimed)
(1 machine(s) hidden — use --all to include machines you cannot access)

Hint: Use `htcondor pool status --all` to see all machines, or `htcondor jobs submit <file>` to submit jobs to the pool.
```

---

## 3. Submit jobs

```bash
$ htcondor jobs submit analysis.sub
Submitting job(s) from: analysis.sub
  ✓ 3 job(s) submitted to cluster 1042.

  Cluster ID : 1042
  Procs      : 3  (1042.0 – 1042.2)
  Submit host: ap2001.chtc.wisc.edu

Hint: Use `htcondor jobs status 1042` to monitor your jobs, or `htcondor jobs report` for a summary.
```

---

## 4. Monitor jobs

```bash
$ htcondor jobs status
All jobs for owner adesai:

JOB_ID  STATUS     CPUS  MEMORY  RUN TIME  CMD
1042.0  Running       1    4 GB  1h 45m    run_analysis.sh
1042.1  Running       1    4 GB  1h 30m    run_analysis.sh
1042.2  Idle          1    4 GB  —         run_analysis.sh
1043.0  Held          4   16 GB  1d 2h 00m train_model.py
1044.0  Completed     1    2 GB  1d 23h 55m clean_data.sh
1045.0  Idle          1    4 GB  —         run_analysis.sh

Total: 6 job(s)  (2 Running, 2 Idle, 1 Held, 1 Completed)

Hint: Use `htcondor jobs status <job-id>` for a specific job, or `htcondor jobs report` for an aggregate summary.
```

Filter by cluster ID:

```bash
$ htcondor jobs status 1042
Jobs matching 1042 for owner adesai:

JOB_ID  STATUS   CPUS  MEMORY  RUN TIME  CMD
1042.0  Running     1    4 GB  1h 45m    run_analysis.sh
1042.1  Running     1    4 GB  1h 30m    run_analysis.sh
1042.2  Idle        1    4 GB  —         run_analysis.sh

Total: 3 job(s)  (2 Running, 1 Idle)

Hint: Use `htcondor jobs status <job-id>` for a specific job, or `htcondor jobs report` for an aggregate summary.
```

Get a high-level summary:

```bash
$ htcondor jobs report
Job Report for adesai
────────────────────────────────────────

  Owner      : adesai
  Clusters   : 4
  Total jobs : 6

         Idle  ██████████░░░░░░░░░░░░░░░░░░░░   2 (33.3%)
      Running  ██████████░░░░░░░░░░░░░░░░░░░░   2 (33.3%)
         Held  █████░░░░░░░░░░░░░░░░░░░░░░░░░   1 (16.7%)
    Completed  █████░░░░░░░░░░░░░░░░░░░░░░░░░   1 (16.7%)

  ⚠  1 job(s) are held:
     1043.0: Job exceeded memory limit (request_memory = 16 GB)

Hint: Use `htcondor jobs status <job-id>` to inspect a specific job, or `htcondor jobs release <job-id>` to release held jobs.
```

---

## 5. Manage jobs

Hold a job (with a reason):

```bash
$ htcondor jobs hold 1042.0 -r "Waiting for input data"
✓ Job 1042.0 held.  Reason: "Waiting for input data"

Hint: Use `htcondor jobs release 1042.0` to release this job when ready.
```

Release held jobs:

```bash
$ htcondor jobs release 1042.0
✓ Job 1042.0 released.

Hint: Use `htcondor jobs status 1042.0` to monitor this job.
```

Remove a job:

```bash
$ htcondor jobs remove 1044.0
✓ Job 1044.0 removed.

Hint: Use `htcondor jobs report` to see remaining jobs.
```

Edit a job attribute:

```bash
$ htcondor jobs edit 1043.0 request_memory=30GB
✓ Job 1043.0: set RequestMemory = 30 GB

Hint: Use `htcondor jobs status 1043.0` to verify the change.
```

---

## 6. Interactive sessions

Start a new interactive job from a submit file:

```bash
$ htcondor jobs interact interactive.sub
Submitting interactive job from: interactive.sub
  → Job 1183.0 submitted.
  → Waiting for job 1183.0 to start…
  → Job started on slot1@e1003.chtc.wisc.edu
  → Connecting…

  You are now logged in to the execute node for job 1183.0.
  Working directory: /var/lib/condor/execute/dir_31045
  Type 'exit' to disconnect and remove the job.

Hint: While connected, use another terminal to run `htcondor jobs status 1183.0` to verify job details.
```

SSH into an already-running job:

```bash
$ htcondor jobs interact --job-id 1042.0
Connecting to running job 1042.0…
  → Establishing SSH tunnel to slot1@e1001.chtc.wisc.edu
  → Connection established.

  You are now logged in to the execute node for job 1042.0.
  Working directory: /var/lib/condor/execute/dir_29501
  Type 'exit' to disconnect.

Hint: When finished, use `htcondor jobs status 1042.0` to verify the job is still running.
```

---

## 7. Verbose mode

Add `-v` for extra details:

```bash
$ htcondor -v jobs hold 1042.0 -r "Testing verbose mode"
✓ Job 1042.0 held.  Reason: "Testing verbose mode"

  JobStatus changed: Running → Held
  HoldReason set: "Testing verbose mode"

Hint: Use `htcondor jobs release 1042.0` to release this job when ready.
```
