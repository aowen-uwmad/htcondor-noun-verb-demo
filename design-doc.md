# Facilitation noun-verb proposal

## Goals

Provide an HTCondor CLI for the **researcher** that is 

1. Easy & intuitive to (re)learn  
2. Provides most (if not all) functionality for using HTCondor for large scale HTC

We believe a noun-verb syntax supports goal one, as most researchers have been exposed to the noun-verb syntax for other CLI programs. In our outline below, we identify the required toolset to ensure we address goal 2\. 

The initial rollout of the CLI should be targeted for use by *researchers* (not *admins*), who are less computer literate and will benefit from a more intuitive CLI interface.

## Constraints

The number of "chunks" at any layer should be limited to 7 or fewer to account for the [capacity of human working memory](https://en.wikipedia.org/wiki/Working_memory#Capacity). That is, 

* 7 or fewer "nouns" total  
* 7 or fewer "verbs" for a given noun  
* 7 or fewer arguments/options for a given noun+verb combination

## Functionality

The set of noun-verb tools should provide most (if not all) of the functionality necessary for the researcher to use HTCondor for large-scale high-throughput computing. Therefore, we need to answer this question: "What does a researcher need to know/do to run a large scale HTC workload using HTCondor?"

### HTC Lifecycle

Here are the steps to completing a computational project using HTC

1. Create directory for project  
2. Organize: create files/directories for scripts, input data, submit files, results, etc.  
3. Create submit file (& executable)  
4. Place test jobs (short list)  
5. Check if test jobs were successful  
   1. Requires knowing when jobs are complete  
   2. May require troubleshooting/testing  
6. Place full job list  
7. Monitor jobs  
8. Check the results  
9. Troubleshoot and resubmit failed jobs  
10. Clean up, summarize results, backup, etc.  
11. Repeat, export, replicate project

There may be several iterative loops in this process, namely 5 → 2, 9 → 6, and 9 → 2\. This lifecycle may also represent a DAG workflow, though in practice that will likely look more like several of these cycles chained in succession.

On the first examination of the list, two items stand out. First, there is the organizational concept. In other CLI tools, the noun used for managing this organization is usually "project". If this idea is pursued, it would require further discussion regarding the name and its design. Second, creating the submit file is usually the biggest conceptual barrier to job submission. A "template" tool would fit in nicely here as a way to easily generate new submit files.

## The Nouns and Their Verbs

Table 1 summarizes the nouns we believe are necessary for a user to conduct the above HTC lifecycle. The rest of this document discusses the functionality represented by the nouns and corresponding verbs.

**Table 1\.** Proposed nouns for the new HTCondor CLI

| Noun | Description |
| :---- | :---- |
| `jobs` | Submit, control HTCondor jobs and interact with HTCondor job records. |
| `dag` | Submit, control HTCondor "DAG" workflows and corresponding records. |
| `project` | Organize working directory and HTCondor settings. |
| `template` | Interact with templates used for submitting new HTCondor jobs. |
| `log` | Interact with local log documenting job lifecycle and properties. |
| `pool` | Interact with a pool of resources and the machines contained therein. |

### The jobs and dag nouns

The `jobs` noun is the primary way for the user to interact with HTCondor, since submitting and controlling HTCondor jobs represents the majority of time spent using HTCondor. Since `dag` is a way of managing jobs, it needs similar actions to the `jobs` noun though with less need for granularity.

**Table 2**. Proposed verbs for the `jobs` and `dag` nouns.

| Verb | Description |
| :---- | :---- |
| `submit` OR `place` | Create new jobs to be managed by HTCondor |
| `status`\* | Granular check of job status |
| `report` | Summary check of jobs status |
| `interact` | Log in to an already-running job |
| `hold` | Interrupt or prevent a job from running, but keep the job record active |
| `release` | Return a held job to active matchmaking |
| `remove` | Remove a job from matchmaking and make its record inactive |
| `edit` | Change a job's attributes in the queue |

\* Not provided for the `dag` noun.

Table 2 summarizes the proposed verbs for use with the `jobs` and `dag` nouns. Most of these actions are not anything "new", with the exception of the `report` verb. The `report` verb provides an at-a-glance summary of the status of a user's jobs, including job records that have been archived. (This is intended to build on the work of CHTC Fellow Kashika Mahajan.) The word `interact` may seem new, but this is simply a re-naming of the `condor_ssh_to_job` command. For the `dag` noun, there is little difference between a "status" check and a "report" in terms of granularity, so the `status` verb may be excluded from the `dag` action set. The rest of the commands are familiar.

	There are two outstanding questions that should be addressed in this section: (a) whether to use `job` or `jobs` and (b) whether to have `dag` commands separate from the `job`/`s` command. Regarding (a), the former is more grammatically correct, while the latter is more reflective of the nature of HTC. For example, `htcondor job submit` is easier to pronounce than `htcondor jobs submit`, but at the cost of implying that a single job is being submitted \- when in most cases there are multiple jobs being submitted. Regarding (b), there has been a push to consolidate all "submit" commands into a single command, and similarly for other related commands. So instead of `htcondor jobs submit test.sub` for jobs and `htcondor dag submit test.dag` for DAGs, the same command could be used for both: `htcondor jobs submit test.sub` and `htcondor jobs submit test.dag`. The advantage of this consolidation is that it reduces the number of commands that a user needs to learn for interacting with HTCondor. The disadvantage, I argue, is that DAGMan is a sufficiently distinct concept from regular jobs that DAGMan jobs and the commands to interact with them should be treated separately from regular jobs. 

### The project noun

The `project` noun has the least precedence in terms of existing HTCondor commands. However, this noun provides a mechanism for several proposed tools that have not been implemented due to a lack of a proper home. The main thrust of these ideas is to provide users ways of organizing their working directory for submitting HTC workloads, informed by the best practices and recommendations that have accumulated over the years. The goal of the `project` noun is to provide structure and organization to the user's working directory. Different project structures could be deployed depending on whether the user is submitting a single job list, multiple job lists, or even DAG workflows. Another function is to provide configuration and hidden files that affect commands submitted within that directory, which is useful for the `log` and `pool` commands discussed below.

	As an aside, the choice of "project" for the name of this noun will need to be discussed in detail. The word "project" is overloaded by several other concepts within the HTC software and deployment spheres. Whatever word is chosen for this noun should communicate the idea of "a group of one or multiple job lists (and related files) that have a shared research aim". 

**Table 3**. Proposed verbs for the `project` noun.

| Verb | Description |
| :---- | :---- |
| `init` OR `create` | Initialize a new project directory structure for an HTC workload |
| `configure` OR `update` | Change project-specific settings |
| `report` | Report on the status of the HTC workload |
| `export` | Save the settings and structure of the project directory for sharing with others |
| `copy` OR `replicate` | Copy the project directory including scripts, etc, but excluding outputs |
| `reset` | Remove outputs |

	Table 3 summarizes the proposed verbs for the `project` noun. The primary interaction with this noun is via the `init` (or `create`, TBD) verb. This verb provides a simple interface to 

* generate a standard directory structure  
* configure project-wide HTCondor settings, including a shared (hidden?) log file  
* set defaults, such as .out, .err naming schemes

While organizing a directory may seem like the user's responsibility (and ultimately, it is), there are certain strategies that can improve the user experience. By providing a tool for generating and interacting with this structure, users can easily leverage the experience of expert users to simplify their own work and avoid common pitfalls, without having to figure out the details themselves \- thus reducing the cognitive load for learning HTC and reducing the time-to-start for new research computing projects.

The other verbs for the `project` noun are mostly focused around interacting with this structured working directory. The `report` verb is the least connected with this concept. Instead, the idea is to enable the user to declare what a project's "success" condition is, and the `report` verb reports on the progress towards that success condition. For example, if a user is trying to process a dataset, the success condition could be to have a `.csv` file in the `outputs` directory for every `.jpg` in the `inputs` directory. Arguably this functionality is the biggest reach of the current proposal, but it illustrates part of the utility of the `project` noun.

### The template noun

The `template` noun provides a way for users to easily generate the necessary files for submitting particular job lists. This lowers the barrier to getting started with HTC, which in turn makes it more likely that the user will continue to use HTC for their research computing needs. This tool is already in development.

	In principle, this noun could be used to encapsulate the project-directory generation described for the `project` noun. The question of whether to extract that functionality into the `template` noun and remove it from the `project` noun comes down to answering this question: what is a template? Is a template a 

* single submit file?   
* a submit file and matching executable file?   
* a larger set of files, and if so, how are those files structured? 

My proposal is that a "template" is a set of files necessary for running a specific job list or DAG workflow, while a "project" can contain multiple (different) job lists and thus involve multiple executions of the `template` commands to generate the different job lists. A standard directory structure across the multiple job lists will still be helpful, but is not necessarily tied to any specific job list and so has different considerations, so the functionality should remain in the `project` noun as is.

**Table 4**. Proposed verbs for the `template` noun.

| Verb | Description |
| :---- | :---- |
| `generate` OR `copy` | Create the files using the specified template |
| `show` OR `list` | Show the templates that can be used  |
| `create` | Create a new template to be added to the list of available templates |
| `modify` | Change a user-created template in the list of available templates |
| `export` | Create a single standalone file to share a template with others |
| `import` | Add a template to the list that was previously exported using the tool |

	Table 4 summarizes the proposed verbs for the `template` noun. The primary interaction with this noun is via the `generate` (or `copy`, TBD) verb. This verb is used to create the files for the selected template in the current directory. Simple templates will be shipped with HTCondor itself, to demonstrate fundamental concepts in job submission and DAGMan workflows. The administrator of the access point can supplement the list with their own templates, including the ability to override or disable the templates shipped with HTCondor. Finally, the user can create their own templates in their local directory for use with the tool. The other verbs in the table support these actions. The `import` verb functionality may instead be an option for the `create` verb, i.e., `htcondor template create --from-file <filename>`.

### The log noun

The `log` noun provides the user a way to interact with HTCondor log files in a convenient way. While the log files are intended to be human-readable, the fact that entries are appended to the log means it is difficult to parse the "narrative" structure of the log. That is, if you want to see the log entries for a single job, you have to extract its entries from a myriad of other entries that were generated alongside them. Organizing and viewing these entries is currently a manual process by the user. The `log` noun will instead provide such functionality for the user.

	The `log` noun is of particular importance for interacting with the hidden, project-based log file that is proposed as part of the configuration done by the `project init` command described above. In that case, the user would not have to be responsible for managing log files, but all of the entries for jobs in a project would be combined in a single log file. Instead of having the user view that file directly, they can use the `log` noun and its verbs. 

**Table 5**. Proposed verbs for the `log` noun.

| Verb | Description |
| :---- | :---- |
| `view` | View the desired (sub)set of log entries |
| `analyze` | Generate statistics about jobs using the log entries |
| `export` | Print or save to file the desired (sub)set of entries for easy sharing |
| `remove` | Delete existing log entries |

	Table 5 summarizes the proposed verbs for the `log` noun. The `view` verb is effectively an alias of `less <path_to_log_file>`, though fancier implementations could be considered. Cluster or job ids could be provided in order to see only a particular subset of entries. The `export` verb would have the same filtering controls, but save to file with the intent of keeping for future reference or sharing with others. Additional options provide control for how to organize such an export. The `remove` verb provides the option to remove specific entries or all entries from the project log file, which is useful for cleaning up "bad" runs that you don't want considered in your project metrics. (This, of course, has nothing to do with any of the system's tracking of job metrics.) The `analyze` verb provides summary statistics about jobs based on the entries in the log file. Behind the scenes, the `project report` command uses the `log analyze` command to provide some of the information it is reporting. 

### The pool noun

The `pool` noun provides users a way to inspect and interact with the pool of resources that are available to them for running their jobs. For the average user, this noun provides a friendlier replacement of the `condor_status` command. For the "advanced" user, this noun provides commands for manipulating the list of resources they have access to, e.g., annexes or OCUs (owned capacity units). 

	It is important to note that the `pool` commands listed below are conceived from the perspective of the user. This is perhaps best illustrated by examples. By default, a regular CHTC user can only run jobs on the "general access" nodes in the pool. Yet a `condor_status` command will return information about *all* nodes in the pool, including prioritized nodes that they cannot access nor opt-in to access. On the other hand, this same user can opt-in to have their jobs flock to the OSPool, expanding the set of machines their jobs can match with. In this case, the `condor_status` command returns no information about this expanded list \- the command has to be modified to connect with the corresponding central manager, but then will only show the results of that pool and not the CHTC pool. The envisaged `pool` commands would merge these different views into one. 

**Table 6**. Proposed verbs for the `pool` noun.

| Verb | Description |
| :---- | :---- |
| `status` | Granular list of machines the user has access to and their statuses |
| `report` | Summary of resources available  |
| `analyze` | Given some resource constraints, analyze pool to estimate throughput |
| `add` | Add additional resources for a user's jobs to match with |
| `remove` | Remove resources that a user's jobs can match with |

	Table 6 summarizes the proposed verbs for the `pool` noun. The `status` verb is the most familiar of current commands as it is effectively a wrapper for the `condor_status` command, defaulting to the `-compact` view and only for machines/primary slots that the user can run jobs on. Options are available for more granularity and to expand the list of machines to include machines that the user can't access, but HTCondor (via the AP(s) that the user has access to) can communicate with. The `report` verb is effectively a summary of the status, but focused more on the capacity of the pool. That is, it summarizes how many machines (and/or slots?) have greater than X amount of CPUs, Y amount of memory, and so on, to help the user build intuition about the resources available to them. The `analyze` verb provides a mechanism for more practical applications of the information provided by `status` or `report`. The user can provide the shape of the slots that they are interested in and the command returns information about the potential throughput of the pool based on that shape. In a way, this is similar to the `condor_q -better-analyze` option, but without requiring a job in the queue in order to work. It's different, though, in that the results are focused more on the number of jobs that could run at a time. Ideally, this analysis is practical \- incorporating some understanding of other users and their jobs, average job pressure, priority, etc. Initially, a simple, theoretical value could be used to provide the upper limit: given the slot shape and assuming no one else was submitting jobs, how many jobs could the user have running at one time? 

	The `add` and `remove` verbs provide the user the ability to modify their pool, or more accurately, the machines/pools that their jobs will match with by default. The information necessary to affect their jobs' matchmaking is contained in the configuration created by the `project init` command discussed earlier. Jobs the user submits from that project will inherit the requirements and additional commands from the config necessary to match with the desired machines/pools. Similarly, the `status`, `report`, and `analyze` verbs will inherit that same information by default. The `add` and `remove` verbs would encompass the functionalities of the "annex" commands, the user-facing commands for the in-development Owned Capacity Units, and perhaps an integration of the remote placement commands.

## Development Milestones

This section discusses the milestones for the development of the proposed commands. 

### Progression

The stages of the development are, in order:

1. Minimum Viable Product  
2. Preferred Minimum Viable Product  
3. Without project functionality  
4. With project functionality

where Stage 4 may be considered optional. The timeline for completing the development depends on the previous development status. 

The proposed progression as well as the current status is tabulated in [andrew's proposal milestones](https://docs.google.com/spreadsheets/d/1AHVfEpnbUAu4JtNM-nU1Y0twM9khL29EFBOslqunCjw/edit?usp=sharing). 

### Stage 1 development

The items missing from the current state of the noun-verb CLI are:

* `htcondor jobs interact`  
* `htcondor jobs hold`  
* `htcondor jobs release`  
* `htcondor jobs remove`  
* `htcondor pool status` 

The `hold`, `release`, and `remove` commands are readily deployed using the existing Python bindings (specifically, the `htcondor.Schedd.act` method) and should be trivial to complete.

	The `htcondor jobs interact` command is effectively an alias for the `condor_submit -i` command. The Python bindings do not currently support interactive job submission and there seems little reason to develop that support, given the purpose of the Python bindings. It is simple, however, to write a Python script that executes the necessary shell command. That being said, there may be other concerns that need to be addressed, given the hacky nature of the interactive submission method.

	The initial version of the `htcondor pool status` command should be readily deployed using the existing Python bindings, specifically the `htcondor.Collector.query` method. The main question is what projection to use and how to present the information to the user. For an easy "get it done" target, the output could try to replicate the output of the existing `condor_status` command, but not put too much effort into making it identical. Then in a later stage, a more deliberate (re)consideration of the output can be completed. 