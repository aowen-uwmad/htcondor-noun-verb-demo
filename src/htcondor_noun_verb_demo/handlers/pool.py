"""
Handlers for the ``htcondor pool`` noun.

Each public function in this module is wired up as the ``command``
default for the corresponding argparse sub-parser created in ``main.py``.
"""

import logging

from htcondor_noun_verb_demo.mock_data import MOCK_MACHINES
from htcondor_noun_verb_demo.formatting import (
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    format_memory,
    print_hint,
    print_section,
    print_table,
)


# ---------------------------------------------------------------------------
# Module-level loggers
# ---------------------------------------------------------------------------

# Level 1 (-d): HTCondor-internals detail (machine ClassAd attributes, …)
_htcondor_log = logging.getLogger("htcondor_noun_verb_demo.htcondor")

# Level 2 (-dd): CLI / argument-parsing detail
_cli_log = logging.getLogger("htcondor_noun_verb_demo.cli")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_colour(state):
    """Return an ANSI-coloured state string."""
    colours = {
        "Claimed": GREEN,
        "Unclaimed": YELLOW,
        "Owner": DIM,
        "Matched": CYAN,
    }
    colour = colours.get(state, "")
    return f"{colour}{state}{RESET}"


def _activity_colour(activity):
    """Return an ANSI-coloured activity string."""
    colours = {
        "Busy": GREEN,
        "Idle": DIM,
        "Retiring": YELLOW,
        "Suspended": RED,
    }
    colour = colours.get(activity, "")
    return f"{colour}{activity}{RESET}"


# ---------------------------------------------------------------------------
# Verb handlers
# ---------------------------------------------------------------------------

def pool_status(args):
    """Handle ``htcondor pool status``."""
    show_all = getattr(args, "all", False)
    filter_expr = getattr(args, "filter", None)
    _cli_log.debug(
        "pool_status called with show_all=%r filter_expr=%r", show_all, filter_expr
    )

    machines = list(MOCK_MACHINES)

    if not show_all:
        # Filter out "Owner" state machines (user "can't access" them)
        machines = [m for m in machines if m["State"] != "Owner"]

    if filter_expr:
        _cli_log.debug("Filter expression supplied: %r (demo ignores filters)", filter_expr)
        print(f"{DIM}(Filter '{filter_expr}' noted — demo ignores filters){RESET}\n")

    print_section("Pool Status")
    print()

    headers = ["NAME", "OPSYS", "ARCH", "STATE", "ACTIVITY", "LOAD", "CPUS", "MEMORY"]
    rows = []
    for m in machines:
        rows.append([
            m["Name"],
            m["OpSys"],
            m["Arch"],
            _state_colour(m["State"]),
            _activity_colour(m["Activity"]),
            f"{m['LoadAvg']:.2f}",
            str(m["TotalCpus"]),
            format_memory(m["TotalMemory"]),
        ])
        _htcondor_log.debug(
            "Machine ClassAd %s: OpSys=%s Arch=%s State=%s Activity=%s "
            "TotalCpus=%d TotalMemory=%d MB LoadAvg=%.2f",
            m["Name"], m["OpSys"], m["Arch"], m["State"], m["Activity"],
            m["TotalCpus"], m["TotalMemory"], m["LoadAvg"],
        )

    print_table(headers, rows, right_align={5, 6, 7})

    # Summary
    total_machines = len(machines)
    total_cpus = sum(m["TotalCpus"] for m in machines)
    total_mem = sum(m["TotalMemory"] for m in machines)
    claimed = sum(1 for m in machines if m["State"] == "Claimed")
    unclaimed = sum(1 for m in machines if m["State"] == "Unclaimed")

    print(f"\n{DIM}Total: {total_machines} machines, "
          f"{total_cpus} CPUs, {format_memory(total_mem)}  "
          f"({claimed} claimed, {unclaimed} unclaimed){RESET}")

    if not show_all:
        hidden = len(MOCK_MACHINES) - len(machines)
        if hidden > 0:
            print(f"{DIM}({hidden} machine(s) hidden — use --all to include machines you cannot access){RESET}")

    print_hint(
        "Use `htcondor pool status --all` to see all machines, "
        "or `htcondor jobs submit <file>` to submit jobs to the pool."
    )


def pool_help(args):
    """Handle ``htcondor pool help``."""
    parser = getattr(args, "_pool_parser", None)
    if parser:
        parser.print_help()
    else:
        print("Use `htcondor pool --help` for more information.")
