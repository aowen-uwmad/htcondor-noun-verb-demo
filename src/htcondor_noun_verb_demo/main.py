"""
Main argument parser for the HTCondor noun-verb CLI demo.

Sets up the top-level parser, registers all nouns and their verbs,
attaches arguments/options, and delegates to handler functions.
"""

import argparse
import logging
import sys
from typing import Optional

from htcondor_noun_verb_demo.formatting import print_error, print_hint

from htcondor_noun_verb_demo.handlers.jobs import (
    jobs_edit,
    jobs_help,
    jobs_hold,
    jobs_interact,
    jobs_release,
    jobs_remove,
    jobs_report,
    jobs_status,
    jobs_submit,
)
from htcondor_noun_verb_demo.handlers.pool import (
    pool_help,
    pool_status,
)


# ---------------------------------------------------------------------------
# Debug logging setup
# ---------------------------------------------------------------------------

_LOG_FORMAT = "[%(levelname)s:%(name)s] %(message)s"

# Module-level loggers used throughout the package:
#   htcondor_noun_verb_demo.htcondor – HTCondor-internals messages (level 1, -d)
#   htcondor_noun_verb_demo.cli      – CLI / argparse messages     (level 2, -dd)


def configure_logging(debug_level: int) -> None:
    """Enable debug loggers based on the number of ``-d`` flags supplied.

    Parameters
    ----------
    debug_level:
        0  – no debug output (default)
        1  – HTCondor-internals messages: ClassAd attributes, status codes, etc.
             (``-d`` / ``--debug``)
        2+ – additionally, CLI messages: argument parsing, handler dispatch, etc.
             (``-dd`` / ``--debug --debug``)
    """
    if debug_level <= 0:
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    # Level 1: HTCondor-internals logger
    htcondor_logger = logging.getLogger("htcondor_noun_verb_demo.htcondor")
    htcondor_logger.setLevel(logging.DEBUG)
    htcondor_logger.addHandler(handler)
    htcondor_logger.propagate = False

    if debug_level >= 2:
        # Level 2: CLI logger
        cli_logger = logging.getLogger("htcondor_noun_verb_demo.cli")
        cli_logger.setLevel(logging.DEBUG)
        cli_logger.addHandler(handler)
        cli_logger.propagate = False


# ---------------------------------------------------------------------------
# Custom ArgumentParser for friendly error messages
# ---------------------------------------------------------------------------

class FriendlyArgumentParser(argparse.ArgumentParser):
    """ArgumentParser subclass that replaces terse argparse errors with
    the same ``Error:`` / ``Hint:`` style used by the rest of the CLI."""

    _friendly_error: Optional[str] = None
    _friendly_hint: Optional[str] = None

    def error(self, message):
        """Override to produce user-friendly error output."""
        if self._friendly_error:
            print_error(self._friendly_error)
            if self._friendly_hint:
                print_hint(self._friendly_hint)
        else:
            # Fallback: still friendlier than raw argparse
            print_error(message)
            print_hint(f"Use `{self.prog} --help` for usage information.")

        sys.exit(1)


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

def get_parser():
    parser = FriendlyArgumentParser(
        prog="htcondor",
        description="The HTCondor command-line interface.",
    )
    parser._friendly_error = "Provide a noun."
    parser._friendly_hint = (
        "Use `htcondor <noun>`. "
        "Available nouns: jobs, dag, project, template, log, pool.\n"
        "       Use `htcondor --help` for details."
    )

    # Global arguments
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print extra output"
    )
    parser.add_argument(
        "-d", "--debug", action="count", default=0,
        help=(
            "Enable debug output. "
            "Use once (-d) for HTCondor-internals detail (ClassAd attributes, "
            "status codes, etc.). "
            "Use twice (-dd) to also include CLI-level debug (argument parsing, "
            "handler dispatch, etc.)."
        ),
    )

    # Initialize noun level subparsers
    nouns = parser.add_subparsers(
        title="nouns",
        description="Use 'htcondor <noun> --help' for more information on a noun.",
        dest="noun",
        required=True,
        parser_class=FriendlyArgumentParser,
    )

    # -----------------------------------------------------------------
    # Nouns
    # -----------------------------------------------------------------
    jobs_parser = nouns.add_parser(
        "jobs", help="Create and interact with HTCondor job(s)"
    )
    jobs_parser._friendly_error = "Provide a verb for 'jobs'."
    jobs_parser._friendly_hint = (
        "Use `htcondor jobs <verb>`. "
        "Available verbs: submit, status, report, interact, hold, release, remove, edit.\n"
        "       Use `htcondor jobs --help` for details."
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
    pool_parser._friendly_error = "Provide a verb for 'pool'."
    pool_parser._friendly_hint = (
        "Use `htcondor pool <verb>`. "
        "Available verbs: status.\n"
        "       Use `htcondor pool --help` for details."
    )

    # =================================================================
    # jobs verbs
    # =================================================================
    jobs_verbs = jobs_parser.add_subparsers(
        title="verbs",
        description="Use 'htcondor jobs <verb> --help' for details.",
        dest="verb",
        required=True,
        parser_class=FriendlyArgumentParser,
    )

    # --- jobs submit ---
    p = jobs_verbs.add_parser("submit", help="Submit HTCondor job(s)")
    p._friendly_error = "Provide a submit description file."
    p._friendly_hint = (
        "Use `htcondor jobs submit <submit_file>` to submit jobs.\n"
        "       Example: `htcondor jobs submit analysis.sub`"
    )
    p.add_argument("submit_file", help="Path to the submit description file")
    p.set_defaults(command=jobs_submit)

    # --- jobs status ---
    p = jobs_verbs.add_parser(
        "status", help="Print details about HTCondor job(s)"
    )
    p.add_argument(
        "job_id", nargs="?", default=None,
        help="Job ID (e.g. 1042.0 or 1042); omit to see all your jobs",
    )
    p.set_defaults(command=jobs_status)

    # --- jobs report ---
    p = jobs_verbs.add_parser(
        "report", help="Print summary report of HTCondor job(s)"
    )
    p.set_defaults(command=jobs_report)

    # --- jobs interact ---
    p = jobs_verbs.add_parser(
        "interact", help="Log in to or start an interactive HTCondor job"
    )
    p.add_argument(
        "submit_file", nargs="?", default=None,
        help="Path to submit file (starts a new interactive job)",
    )
    p.add_argument(
        "--job-id", dest="job_id", default=None,
        help="ID of a running job to SSH into (e.g. 1042.0)",
    )
    p.set_defaults(command=jobs_interact)

    # --- jobs hold ---
    p = jobs_verbs.add_parser(
        "hold", help="Interrupt and prevent HTCondor job(s) from running"
    )
    p._friendly_error = "Provide a job ID to hold."
    p._friendly_hint = (
        "Use `htcondor jobs hold <job_id>` to hold a job.\n"
        "       Example: `htcondor jobs hold 1042.0`"
    )
    p.add_argument("job_id", help="Job ID to hold (e.g. 1042.0 or 1042)")
    p.add_argument(
        "-r", "--reason", default=None,
        help="A reason for holding the job(s)",
    )
    p.set_defaults(command=jobs_hold)

    # --- jobs release ---
    p = jobs_verbs.add_parser(
        "release",
        help="Remove a 'hold' and allow HTCondor job(s) to run again",
    )
    p._friendly_error = "Provide a job ID to release."
    p._friendly_hint = (
        "Use `htcondor jobs release <job_id>` to release a held job.\n"
        "       Example: `htcondor jobs release 1042.0`"
    )
    p.add_argument("job_id", help="Job ID to release (e.g. 1042.0 or 1042)")
    p.set_defaults(command=jobs_release)

    # --- jobs remove ---
    p = jobs_verbs.add_parser(
        "remove", help="Remove HTCondor job(s) permanently"
    )
    p._friendly_error = "Provide a job ID to remove."
    p._friendly_hint = (
        "Use `htcondor jobs remove <job_id>` to remove a job.\n"
        "       Example: `htcondor jobs remove 1042.0`"
    )
    p.add_argument("job_id", help="Job ID to remove (e.g. 1042.0 or 1042)")
    p.add_argument(
        "-f", "--force", action="store_true",
        help="Force-remove: skip cleanup hooks",
    )
    p.set_defaults(command=jobs_remove)

    # --- jobs edit ---
    p = jobs_verbs.add_parser("edit", help="Edit properties of a job")
    p._friendly_error = "Provide a job ID and an assignment (e.g. request_memory=30GB)."
    p._friendly_hint = (
        "Use `htcondor jobs edit <job_id> <key>=<value>`.\n"
        "       Example: `htcondor jobs edit 1042.0 request_memory=30GB`"
    )
    p.add_argument("job_id", help="Job ID to edit (e.g. 1042.0)")
    p.add_argument(
        "assignment",
        help="Attribute assignment in key=value format (e.g. request_memory=30GB, request_cpus=4)",
    )
    p.set_defaults(command=jobs_edit)

    # --- jobs help ---
    p = jobs_verbs.add_parser("help", help="Print this help text")
    p.set_defaults(command=jobs_help, _jobs_parser=jobs_parser)

    # =================================================================
    # pool verbs
    # =================================================================
    pool_verbs = pool_parser.add_subparsers(
        title="verbs",
        description="Use 'htcondor pool <verb> --help' for details.",
        dest="verb",
        required=True,
        parser_class=FriendlyArgumentParser,
    )

    # --- pool status ---
    p = pool_verbs.add_parser(
        "status",
        help="Show machines available for your jobs",
    )
    p.add_argument(
        "-f", "--filter", dest="filter", default=None,
        help="Filter machines by keyword or attribute (e.g. 'gpu' or 'Arch=X86_64')",
    )
    p.add_argument(
        "--all", action="store_true",
        help="Include machines you cannot currently access",
    )
    p.set_defaults(command=pool_status)

    # --- pool help ---
    p = pool_verbs.add_parser("help", help="Print this help text")
    p.set_defaults(command=pool_help, _pool_parser=pool_parser)

    # =================================================================
    # Placeholder nouns  (dag, project, template, log)
    # Verbs will be added in later development stages.
    # =================================================================
    for placeholder_parser in (dag_parser, project_parser, template_parser, log_parser):
        placeholder_parser.set_defaults(
            command=lambda args, _p=placeholder_parser: _p.print_help()
        )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args(parser):
    # Parse arguments
    args = parser.parse_args()
    return args


def main():
    parser = get_parser()
    args = parse_args(parser)

    configure_logging(args.debug)

    _cli_log = logging.getLogger("htcondor_noun_verb_demo.cli")
    _cli_log.debug("Parsed args: %s", args)

    if hasattr(args, "command"):
        _cli_log.debug("Dispatching to handler: %s", args.command.__name__)
        args.command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
