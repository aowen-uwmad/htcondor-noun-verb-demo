"""
Main argument parser for demo.
"""

import argparse


def get_parser():
    parser = argparse.ArgumentParser(prog="htcondor")

    # Global arguments
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print extra output"
    )

    # Initialize noun level subparsers
    nouns = parser.add_subparsers(required=True)

    # Nouns
    jobs_parser = nouns.add_parser(
        "jobs", help="Create and interact with HTCondor job(s)"
    )
    dag_parser = nouns.add_parser(
        "dag", help="Create and interact with HTCondor DAGMan workflows"
    )
    project_parser = nouns.add_parser(
        "project", help="Create and interact with a 'project' directory"
    )
    template_parser = nouns.add_parser(
        "template",
        help="Generate job descriptions from templates, interact with templates list",
    )
    log_parser = nouns.add_parser(
        "log", help="Query and interact with your HTCondor logbook"
    )
    pool_parser = nouns.add_parser(
        "pool", help="Query and interact with your pool of resources"
    )

    # Job verbs
    jobs_verbs = jobs_parser.add_subparsers(required=True)

    jobs_submit_parser = jobs_verbs.add_parser("submit", help="Submit HTCondor job(s)")
    jobs_status_parser = jobs_verbs.add_parser(
        "status", help="Print details about HTCondor job(s)"
    )
    jobs_report_parser = jobs_verbs.add_parser(
        "report", help="Print summary report of HTCondor job(s)"
    )
    jobs_interact_parser = jobs_verbs.add_parser(
        "interact", help="Log in to a currently running HTCondor job"
    )
    jobs_hold_parser = jobs_verbs.add_parser(
        "hold", help="Interrupt and prevent HTCondor job(s) from running"
    )
    jobs_release_parser = jobs_verbs.add_parser(
        "release", help="Remove a 'hold' and allow HTCondor job(s) to run again"
    )
    jobs_remove_parser = jobs_verbs.add_parser(
        "remove", help="Remove HTCondor job(s) permanently"
    )
    jobs_help_parser = jobs_verbs.add_parser("help", help="Print this help text")

    jobs_submit_parser.set_defaults(command=jobs_submit)
    return parser


def jobs_submit(args):
    print("You've submitted a job using these arguments:", args)


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
