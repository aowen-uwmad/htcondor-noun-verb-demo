"""
Handlers for the ``htcondor jobs`` noun.

Each public function in this module is wired up as the ``command``
default for the corresponding argparse sub-parser created in ``main.py``.
"""

import os
import sys
import random

from htcondor_noun_verb_demo.mock_data import MOCK_JOBS, _NOW
from htcondor_noun_verb_demo.formatting import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    format_duration,
    format_memory,
    print_confirmation,
    print_error,
    print_hint,
    print_section,
    print_table,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_job_id(raw):
    """
    Parse a user-supplied job identifier.

    Accepts ``"1042.0"`` or ``"1042"`` (bare cluster id).
    Returns ``(cluster_id, proc_id)`` where *proc_id* is ``None``
    when the user supplied only a cluster id (meaning "all procs").
    """
    if "." in raw:
        parts = raw.split(".", 1)
        return int(parts[0]), int(parts[1])
    return int(raw), None


def _filter_jobs(job_id_raw=None):
    """Return the subset of MOCK_JOBS matching the optional *job_id_raw*."""
    if job_id_raw is None:
        return list(MOCK_JOBS)
    cluster, proc = _parse_job_id(job_id_raw)
    matches = [
        j for j in MOCK_JOBS
        if j["ClusterId"] == cluster and (proc is None or j["ProcId"] == proc)
    ]
    return matches


def _job_label(cluster, proc=None):
    """Return a human-friendly job label like ``1042.0`` or ``1042.*``."""
    if proc is not None:
        return f"{cluster}.{proc}"
    return f"{cluster}.*"


def _status_colour(status_str):
    """Return an ANSI-coloured status string."""
    colours = {
        "Idle": YELLOW,
        "Running": GREEN,
        "Held": RED,
        "Completed": CYAN,
    }
    colour = colours.get(status_str, "")
    return f"{colour}{status_str}{RESET}"


# ---------------------------------------------------------------------------
# Verb handlers
# ---------------------------------------------------------------------------

def jobs_submit(args):
    """Handle ``htcondor jobs submit <submit_file>``."""
    submit_file = args.submit_file
    cluster_id = random.randint(1050, 1200)
    num_procs = random.randint(1, 5)

    print(f"Submitting job(s) from: {BOLD}{submit_file}{RESET}")
    print(f"  {GREEN}✓{RESET} {num_procs} job(s) submitted to cluster {BOLD}{cluster_id}{RESET}.")
    print()
    print(f"  Cluster ID : {cluster_id}")
    print(f"  Procs      : {num_procs}  ({cluster_id}.0 – {cluster_id}.{num_procs - 1})")
    print(f"  Submit host: ap2001.chtc.wisc.edu")

    print_hint(
        f"Use `htcondor jobs status {cluster_id}` to monitor your jobs, "
        f"or `htcondor jobs report` for a summary."
    )


def jobs_status(args):
    """Handle ``htcondor jobs status [job_id]``."""
    job_id_raw = getattr(args, "job_id", None)
    jobs = _filter_jobs(job_id_raw)

    if not jobs:
        print_error(f"No jobs found matching '{job_id_raw}'.")
        print_hint("Use `htcondor jobs status` (without an ID) to see all your jobs.")
        return

    owner = jobs[0]["Owner"]

    if job_id_raw:
        print(f"Jobs matching {BOLD}{job_id_raw}{RESET} for owner {BOLD}{owner}{RESET}:")
    else:
        print(f"All jobs for owner {BOLD}{owner}{RESET}:")
    print()

    headers = ["JOB_ID", "STATUS", "CPUS", "MEMORY", "RUN TIME", "CMD"]
    rows = []
    for j in jobs:
        jid = f"{j['ClusterId']}.{j['ProcId']}"
        status = _status_colour(j["JobStatusStr"])
        cpus = str(j["RequestCpus"])
        mem = format_memory(j["RequestMemory"])
        if j["JobStartDate"]:
            runtime = format_duration(_NOW - j["JobStartDate"])
        else:
            runtime = "—"
        cmd = os.path.basename(j["Cmd"])
        rows.append([jid, status, cpus, mem, runtime, cmd])

    print_table(headers, rows, right_align={2, 3})

    # Summary line
    status_counts = {}
    for j in jobs:
        s = j["JobStatusStr"]
        status_counts[s] = status_counts.get(s, 0) + 1
    summary_parts = [f"{count} {status}" for status, count in status_counts.items()]
    print(f"\n{DIM}Total: {len(jobs)} job(s)  ({', '.join(summary_parts)}){RESET}")

    print_hint(
        "Use `htcondor jobs status <job_id>` for a specific job, "
        "or `htcondor jobs report` for an aggregate summary."
    )


def jobs_report(args):
    """Handle ``htcondor jobs report``."""
    owner = MOCK_JOBS[0]["Owner"]

    # Tally by status
    status_counts = {}
    for j in MOCK_JOBS:
        s = j["JobStatusStr"]
        status_counts[s] = status_counts.get(s, 0) + 1

    total = len(MOCK_JOBS)
    clusters = len({j["ClusterId"] for j in MOCK_JOBS})

    print_section(f"Job Report for {owner}")
    print()
    print(f"  Owner      : {owner}")
    print(f"  Clusters   : {clusters}")
    print(f"  Total jobs : {total}")
    print()

    # Status breakdown
    order = ["Idle", "Running", "Held", "Completed", "Removed"]
    for status in order:
        count = status_counts.get(status, 0)
        if count == 0:
            continue
        bar_len = int((count / total) * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        pct = count / total * 100
        print(f"  {_status_colour(status):>20s}  {bar}  {count:>2d} ({pct:4.1f}%)")

    # Held-job details
    held = [j for j in MOCK_JOBS if j["JobStatusStr"] == "Held"]
    if held:
        print(f"\n  {RED}⚠  {len(held)} job(s) are held:{RESET}")
        for j in held:
            jid = f"{j['ClusterId']}.{j['ProcId']}"
            reason = j.get("HoldReason", "Unknown")
            print(f"     {jid}: {reason}")

    print_hint(
        "Use `htcondor jobs status <job_id>` to inspect a specific job, "
        "or `htcondor jobs release <job_id>` to release held jobs."
    )


def jobs_interact(args):
    """Handle ``htcondor jobs interact``."""
    submit_file = getattr(args, "submit_file", None)
    job_id = getattr(args, "job_id", None)

    if submit_file and job_id:
        print_error("Provide either a submit file or a job ID, not both.")
        print_hint(
            "Use `htcondor jobs interact <submit_file>` to start a new interactive job,\n"
            "       or `htcondor jobs interact --job-id <id>` to SSH into an existing job."
        )
        sys.exit(1)

    if job_id:
        # condor_ssh_to_job path
        cluster, proc = _parse_job_id(job_id)
        if proc is None:
            proc = 0
        print(f"Connecting to running job {BOLD}{cluster}.{proc}{RESET}…")
        print(f"  → Establishing SSH tunnel to slot1@e1001.chtc.wisc.edu")
        print(f"  → Connection established.")
        print()
        print(f"  {GREEN}You are now logged in to the execute node for job {cluster}.{proc}.{RESET}")
        print(f"  Working directory: /var/lib/condor/execute/dir_29501")
        print(f"  Type 'exit' to disconnect.")
        print_hint(
            f"When finished, use `htcondor jobs status {cluster}.{proc}` to verify the job is still running."
        )
    elif submit_file:
        # condor_submit -i path
        cluster_id = random.randint(1050, 1200)
        print(f"Submitting interactive job from: {BOLD}{submit_file}{RESET}")
        print(f"  → Job {cluster_id}.0 submitted.")
        print(f"  → Waiting for job {cluster_id}.0 to start…")
        print(f"  → Job started on slot1@e1003.chtc.wisc.edu")
        print(f"  → Connecting…")
        print()
        print(f"  {GREEN}You are now logged in to the execute node for job {cluster_id}.0.{RESET}")
        print(f"  Working directory: /var/lib/condor/execute/dir_31045")
        print(f"  Type 'exit' to disconnect and remove the job.")
        print_hint(
            f"While connected, use another terminal to run "
            f"`htcondor jobs status {cluster_id}.0` to verify job details."
        )
    else:
        print_error("Provide a submit file or a --job-id to connect to.")
        print_hint(
            "Use `htcondor jobs interact <submit_file>` to start a new interactive job,\n"
            "       or `htcondor jobs interact --job-id <id>` to SSH into an existing job."
        )
        sys.exit(1)


def jobs_hold(args):
    """Handle ``htcondor jobs hold <job_id>``."""
    job_id_raw = args.job_id
    reason = getattr(args, "reason", None)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    extra = ""
    if reason:
        extra = f'Reason: "{reason}"'

    print_confirmation("held", label, extra)

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}JobStatus changed: 2 (Running) → 5 (Held)")
        if reason:
            print(f"  HoldReason set: \"{reason}\"{RESET}")

    print_hint(f"Use `htcondor jobs release {label}` to release this job when ready.")


def jobs_release(args):
    """Handle ``htcondor jobs release <job_id>``."""
    job_id_raw = args.job_id
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    print_confirmation("released", label)

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}JobStatus changed: 5 (Held) → 1 (Idle)")
        print(f"  HoldReason cleared.{RESET}")

    print_hint(f"Use `htcondor jobs status {label}` to monitor this job.")


def jobs_remove(args):
    """Handle ``htcondor jobs remove <job_id>``."""
    job_id_raw = args.job_id
    force = getattr(args, "force_x", False)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    action = "forcefully removed" if force else "removed"
    print_confirmation(action, label)

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}JobStatus changed: → 3 (Removed)")
        if force:
            print(f"  Force-remove: job will not run cleanup hooks.{RESET}")

    print_hint("Use `htcondor jobs report` to see remaining jobs.")


def jobs_edit(args):
    """Handle ``htcondor jobs edit <job_id> --attribute <attr> --value <val>``."""
    job_id_raw = args.job_id
    attribute = args.attribute
    value = args.value
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    print(f"{GREEN}✓{RESET} Job {BOLD}{label}{RESET}: set {BOLD}{attribute}{RESET} = {value}")

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}Attribute '{attribute}' updated for job {label}.{RESET}")

    print_hint(
        f"Use `htcondor jobs status {label}` to verify the change."
    )


def jobs_help(args):
    """Handle ``htcondor jobs help``."""
    # Retrieve the parent parser and print its help.
    # The parser is stashed on the args namespace by main.py.
    parser = getattr(args, "_jobs_parser", None)
    if parser:
        parser.print_help()
    else:
        print("Use `htcondor jobs --help` for more information.")
