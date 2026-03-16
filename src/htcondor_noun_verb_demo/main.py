"""
Main argument parser for demo.
"""

import argparse


def get_parser():
    parser_desc = "Interact with the HTCondor system"
    parser_epilog = "HTCondor is a job and resource management system designed for large scale (and particularly, high throughput) computing. For more information, see htcondor.org"

    # Nouns help text
    jobs_parser_desc = "Create and interact with HTCondor job(s)"
    jobs_parser_epilog = "Work to be executed on an HTCondor system needs to be described by a 'jobs file' and submitted to the system. Once the job(s) are in the system, you can monitor their progress as well as control their behavior."

    dag_parser_desc = "Create and interact with HTCondor DAGMan workflows"
    dag_parser_epilog = "DAGMan is used to execute a series of HTCondor jobs as described by the DAG input file. Once in the system, you can monitor the progress as well as control the behavior."

    project_parser_desc = "Create and interact with a 'project' directory"
    project_parser_epilog = "The 'project' directory is used to store settings and organize work across multiple job submissions."

    template_parser_desc = (
        "Generate job descriptions from templates, interact with templates list"
    )
    template_parser_epilog = "It can be difficult to set-up an HTCondor workflow from scratch. The templates provide a source of inspiration for organizing and executing your work."

    log_parser_desc = "Query and interact with your HTCondor logbook"
    log_parser_epilog = "The logbook tracks the history of the work you've submitted to the system. See the work you've sent through the system and use the provided tools to analyze and optimize your work."

    pool_parser_desc = "Query and interact with your pool of resources"
    pool_parser_epilog = "Your 'pool' is where the work gets done. Use these tools to check the status of the resources, incorporate or exclude resources, and investigate job matchmaking."

    # Verbs help text

    # jobs verbs
    jobs_submit_desc = "Submit HTCondor job(s)"
    jobs_submit_epilog = ""

    jobs_status_desc = "Print details about HTCondor job(s)"
    jobs_status_epilog = ""

    jobs_report_desc = "Print summary report of HTCondor job(s)"
    jobs_report_epilog = ""

    jobs_interact_desc = "Log in to a currently running HTCondor job"
    jobs_interact_epilog = ""

    jobs_hold_desc = "Interrupt and prevent HTCondor job(s) from running"
    jobs_hold_epilog = ""

    jobs_release_desc = "Remove a 'hold' and allow HTCondor job(s) to run again"
    jobs_release_epilog = ""

    jobs_remove_desc = "Irreversibly interrupt and prevent job(s) from running"
    jobs_remove_epilog = ""

    jobs_edit_desc = "Edit properties of the job"
    jobs_edit_epilog = ""

    jobs_help_desc = "Get more help"
    jobs_help_epilog = ""

    # Setting up parsers

    parser = argparse.ArgumentParser(
        prog="htcondor", description=parser_desc, epilog=parser_epilog
    )

    # Global arguments
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print extra output"
    )
    parser.add_argument(
        "--version", action="store_true", help="Print version information"
    )

    # Initialize noun level subparsers
    nouns = parser.add_subparsers(required=True)

    # Nouns
    jobs_parser = nouns.add_parser(
        "jobs",
        help=jobs_parser_desc,
        description=jobs_parser_desc,
        epilog=jobs_parser_epilog,
    )

    dag_parser = nouns.add_parser(
        "dag",
        help=dag_parser_desc,
        description=dag_parser_desc,
        epilog=dag_parser_epilog,
    )

    project_parser = nouns.add_parser(
        "project",
        help=project_parser_desc,
        description=project_parser_desc,
        epilog=project_parser_epilog,
    )

    template_parser = nouns.add_parser(
        "template",
        help=template_parser_desc,
        description=template_parser_desc,
        epilog=template_parser_epilog,
    )

    log_parser = nouns.add_parser(
        "log",
        help=log_parser_desc,
        description=log_parser_desc,
        epilog=log_parser_epilog,
    )

    pool_parser = nouns.add_parser(
        "pool",
        help=pool_parser_desc,
        description=pool_parser_desc,
        epilog=pool_parser_epilog,
    )

    # Job verbs
    jobs_verbs = jobs_parser.add_subparsers(required=True)

    # jobs submit
    jobs_submit_parser = jobs_verbs.add_parser(
        "submit",
        help=jobs_submit_desc,
        description=jobs_submit_desc,
        epilog=jobs_submit_epilog,
        usage="%(prog)s [options] jobs_file",
    )
    jobs_submit_parser.set_defaults(command=jobs_submit)

    # jobs submit arguments
    jobs_submit_parser.add_argument(
        "submit_file", type=str, help="Name of jobs file describing job(s)"
    )
    jobs_submit_parser.add_argument(
        "-i", "--interactive", action="store_true", help="Start an interactive job"
    )
    jobs_submit_parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Do everything except actually submit the job(s)",
    )
    jobs_submit_parser.add_argument(
        "-p",
        "--prepend-command",
        type=str,
        metavar="COMMAND",
        help="Additional command to include at START of jobs file parsing",
    )
    jobs_submit_parser.add_argument(
        "-a",
        "--append-command",
        type=str,
        metavar="COMMAND",
        help="Additional command to include at END of jobs file parsing",
    )

    # jobs status
    jobs_status_parser = jobs_verbs.add_parser(
        "status",
        help=jobs_status_desc,
        description=jobs_status_desc,
        epilog=jobs_status_epilog,
        usage="%(prog)s [options] [-A | -a | -i] identifier",
    )
    jobs_status_parser.set_defaults(command=jobs_status)

    # jobs status arguments
    jobs_status_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute (defaults to $USER)",
        default="$USER",
        nargs="?",
    )
    jobs_status_parser.add_argument(
        "-nob",
        "--no-batch",
        help="Do not automatically group jobs in output",
        action="store_true",
    )
    jobs_status_parser.add_argument(
        "-f",
        "--filter",
        metavar="EXPR",
        type=str,
        help="Further filter results based on expression",
    )
    jobs_status_parser.add_argument(
        "-o",
        "--output",
        metavar="EXPR",
        type=str,
        help="Print output based on expression",
    )

    job_status_job_type = jobs_status_parser.add_mutually_exclusive_group()
    job_status_job_type.add_argument(
        "-A",
        "--all",
        action="store_true",
        help="Query both active and inactive jobs (history) [default]",
    )
    job_status_job_type.add_argument(
        "-a",
        "--active",
        action="store_true",
        help="Only query the list of active jobs",
    )
    job_status_job_type.add_argument(
        "-i",
        "--inactive",
        action="store_true",
        help="Only query the list of inactive jobs (history)",
    )

    jobs_status_parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="Limit results to the first N hits",
    )
    jobs_status_parser.add_argument(
        "--state",
        choices=["all", "idle", "in", "run", "out", "held", "done"],
        default="all",
        help="Show jobs in the specified state; for complex combinations, use '--filter' (default=all)",
    )
    jobs_status_parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        help="Watch the progress of the job through the system; not compatible with some options.",
    )

    # jobs report
    jobs_report_parser = jobs_verbs.add_parser(
        "report",
        help=jobs_report_desc,
        description=jobs_report_desc,
        epilog=jobs_report_epilog,
        usage="%(prog)s [options] [-A | -a | -i] identifier",
    )
    jobs_report_parser.set_defaults(command=jobs_report)

    # jobs report arguments
    jobs_report_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute (defaults to $USER)",
        default="$USER",
        nargs="?",
    )
    jobs_report_parser.add_argument(
        "-t",
        "--type",
        choices=["full", "short", "resources"],
        default="full",
        help="Select the details generated by report (default=full)",
    )
    jobs_report_parser.add_argument(
        "-u",
        "--update",
        choices=["yes", "no", "refresh"],
        help="Whether or not to update cached data, or remove and refresh (default=yes)",
        default="yes",
    )
    jobs_report_parser.add_argument(
        "-f",
        "--filter",
        metavar="EXPR",
        type=str,
        help="Further filter results based on expression",
    )
    jobs_report_parser.add_argument(
        "-d",
        "--deep",
        action="store_true",
        help='Do a "deep" search for job data - requires ElasticSearch is enabled',
    )
    jobs_report_parser.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help="Disable advanced formatting features - simple ASCII text only",
    )

    job_report_job_type = jobs_report_parser.add_mutually_exclusive_group()
    job_report_job_type.add_argument(
        "-A",
        "--all",
        action="store_true",
        help="Query both active and inactive jobs (history) [default]",
    )
    job_report_job_type.add_argument(
        "-a",
        "--active",
        action="store_true",
        help="Only query the list of active jobs",
    )
    job_report_job_type.add_argument(
        "-i",
        "--inactive",
        action="store_true",
        help="Only query the list of inactive jobs (history)",
    )

    # jobs interact
    jobs_interact_parser = jobs_verbs.add_parser(
        "interact",
        help=jobs_interact_desc,
        description=jobs_interact_desc,
        epilog=jobs_interact_epilog,
        usage="%(prog)s [options] identifier",
    )
    jobs_interact_parser.set_defaults(command=jobs_interact)

    # jobs interact arguments
    jobs_interact_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute",
    )
    jobs_interact_parser.add_argument(
        "-f",
        "--filter",
        type=str,
        metavar="EXPR",
        help="Further filter results based on expression",
    )
    jobs_interact_parser.add_argument(
        "-r",
        "--retry",
        action="store_true",
        help="If first attempt fails, keep retrying to connect to job",
    )
    jobs_interact_parser.add_argument(
        "--shell",
        type=str,
        default="bash",
        help="What shell to use when logging into job (default=bash)",
    )

    # jobs hold
    jobs_hold_parser = jobs_verbs.add_parser(
        "hold",
        help=jobs_hold_desc,
        description=jobs_hold_desc,
        epilog=jobs_hold_epilog,
        usage="%(prog)s [options] identifier",
    )
    jobs_hold_parser.set_defaults(command=jobs_hold)

    # jobs hold arguments
    jobs_hold_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute",
    )
    jobs_hold_parser.add_argument(
        "-f",
        "--filter",
        type=str,
        metavar="EXPR",
        help="Further filter results based on expression",
    )
    jobs_hold_parser.add_argument(
        "-r",
        "--reason",
        type=str,
        help="Message to use for hold reason",
    )
    jobs_hold_parser.add_argument(
        "-c",
        "--code",
        type=int,
        metavar="N",
        help="Code to use for hold reason subcode",
    )
    jobs_hold_parser.add_argument(
        "-a",
        "--autorelease",
        type=int,
        metavar="N",
        help="Automatically release job(s) after N seconds",
    )

    # jobs release
    jobs_release_parser = jobs_verbs.add_parser(
        "release",
        help=jobs_release_desc,
        description=jobs_release_desc,
        epilog=jobs_release_epilog,
        usage="%(prog)s [options] identifier",
    )
    jobs_release_parser.set_defaults(command=jobs_release)

    # jobs release arguments
    jobs_release_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute",
    )
    jobs_release_parser.add_argument(
        "-f",
        "--filter",
        type=str,
        metavar="EXPR",
        help="Further filter results based on expression",
    )
    jobs_release_parser.add_argument(
        "-d",
        "--delay",
        type=int,
        metavar="N",
        help="Wait N seconds before releasing job(s)",
    )

    # jobs remove
    jobs_remove_parser = jobs_verbs.add_parser(
        "remove",
        help=jobs_remove_desc,
        description=jobs_remove_desc,
        epilog=jobs_remove_epilog,
        usage="%(prog)s [options] identifier",
    )
    jobs_remove_parser.set_defaults(command=jobs_remove)

    # jobs remove arguments
    jobs_remove_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute",
    )
    jobs_remove_parser.add_argument(
        "-f",
        "--filter",
        type=str,
        metavar="EXPR",
        help="Further filter results based on expression",
    )
    jobs_remove_parser.add_argument(
        "-r",
        "--reason",
        type=str,
        help="Message to use as the reason for removing the job(s)",
    )

    # jobs edit
    jobs_edit_parser = jobs_verbs.add_parser(
        "edit",
        help=jobs_edit_desc,
        description=jobs_edit_desc,
        epilog=jobs_edit_epilog,
        usage="%(prog)s [options] identifier key value",
    )
    jobs_edit_parser.set_defaults(command=jobs_edit)

    # jobs edit arguments
    jobs_edit_parser.add_argument(
        "identifier",
        help="Select for jobs with this attribute",
    )
    jobs_edit_parser.add_argument(
        "key",
        choices=[
            "cpus",
            "memory",
            "disk",
            "gpus",
            "requirements",
            "require_gpus",
            "batchname",
        ],
        help="Property of the job(s) to modify",
    )
    jobs_edit_parser.add_argument(
        "value",
        type=str,
        help="Desired value of said property",
    )
    jobs_edit_parser.add_argument(
        "-f",
        "--filter",
        type=str,
        metavar="EXPR",
        help="Further filter results based on expression",
    )

    # jobs help
    jobs_help_parser = jobs_verbs.add_parser(
        "help",
        help=jobs_help_desc,
        description=jobs_help_desc,
        epilog=jobs_help_epilog,
    )
    jobs_help_parser.set_defaults(command=jobs_help)

    # DAG verbs
    # Skipping for now..

    # Project verbs
    # Skipping for now..

    # Template verbs
    # Skipping for now..

    # Log verbs
    # Skipping for now..

    # Pool verbs
    pool_verbs = pool_parser.add_subparsers(required=True)

    # pool status
    pool_status_parser = pool_verbs.add_parser(
        "status",
        help="Check the status of resources in the pool",
        usage="%(prog)s [options] identifier",
    )
    pool_status_parser.set_defaults(command=pool_status)

    # pool status arguments
    pool_status_parser.add_argument(
        "identifier",
        help="Select for resources with this attribute (default is all resources)",
        nargs="?",
    )
    pool_status_parser.add_argument(
        "-c",
        "--compact",
        action="store_true",
        help="Output is condensed",
    )
    pool_status_parser.add_argument(
        "-p",
        "--pool",
        metavar="ADDRESS",
        help="Query the pool (Central Manager) located at ADDRESS",
    )
    pool_status_parser.add_argument(
        "-f",
        "--filter",
        metavar="EXPR",
        type=str,
        help="Further filter results based on expression",
    )
    pool_status_parser.add_argument(
        "-j",
        "--job",
        metavar="JobID",
        help="Show the status of the slot/machine for the specified job",
    )
    pool_status_parser.add_argument(
        "-J",
        "--filter-by-job",
        metavar="JobID",
        help="Filter results to those that meet the requirements of JobID",
    )
    pool_status_parser.add_argument(
        "-M",
        "--filter-by-match",
        metavar="JobID",
        help="Further filter '--filter-by-job' results to those where JobID also satisfies the resource's requirements",
    )
    pool_status_parser.add_argument(
        "-C",
        "--computing-capacity",
        nargs=4,
        type=int,
        metavar="N",
        help="Filter results to those with >N resources, in order of CPU, MEM (GB), DISK (GB), GPU",
    )

    return parser


def jobs_submit(args):
    print("You've submitted a job using these arguments:", args)


def jobs_status(args):
    print("You've requested the status of a job.")


def jobs_report(args):
    print("You've requested a report of the jobs.")


def jobs_interact(args):
    print("You've requested to interact with a running job.")


def jobs_hold(args):
    print("You've requested to hold a job.")


def jobs_release(args):
    print("You've requested to release a held job.")


def jobs_remove(args):
    print("You've requested to remove a job from the queue.")


def jobs_edit(args):
    print("You've requested to edit the properties of job(s).")


def jobs_help(args):
    print(
        "This should be the help text you get when you run 'htcondor jobs --help', but I can't figure out how to do that."
    )


def pool_status(args):
    print("You've requested the status of resources in the pool.")


def parse_args(parser):
    # Parse arguments
    args = parser.parse_args()

    return args


def main():
    parser = get_parser()
    args = parse_args(parser)

    if hasattr(args, "command"):
        args.command(args)
    else:
        raise RuntimeError("Oops, the developer messed up!!")


if __name__ == "__main__":
    main()
