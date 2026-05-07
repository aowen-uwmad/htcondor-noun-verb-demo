"""
Handlers for the ``htcondor jobs`` noun.

Each public function in this module is wired up as the ``command``
default for the corresponding argparse sub-parser created in ``main.py``.
"""

import os
import re
import sys

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

    Raises ``SystemExit`` with a friendly error message for invalid input.
    """
    try:
        if "." in raw:
            parts = raw.split(".", 1)
            return int(parts[0]), int(parts[1])
        return int(raw), None
    except ValueError:
        print_error(f"Invalid job ID '{raw}'. Expected format: <cluster> or <cluster>.<proc> (e.g. 1042 or 1042.0).")
        sys.exit(1)


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
# Attribute/value parsing helpers for ``jobs edit``
# ---------------------------------------------------------------------------

# Mapping from submit-file style attribute names to their ClassAd equivalents.
# Keys are lower-case; values are the canonical ClassAd attribute names.
_SUBMIT_TO_CLASSAD = {
    "request_memory": "RequestMemory",
    "request_cpus": "RequestCpus",
    "request_disk": "RequestDisk",
    "request_gpus": "RequestGpus",
    "priority": "JobPrio",
    "job_prio": "JobPrio",
}

# Attributes that store a quantity in MB (convert human-friendly size strings).
_MEMORY_MB_ATTRS = {"RequestMemory"}

# Attributes that store a quantity in KB (convert human-friendly size strings).
_DISK_KB_ATTRS = {"RequestDisk"}


def _parse_size(value_str, *, unit="MB"):
    """
    Parse a human-friendly size string and return an integer in *unit*.

    Examples::

        _parse_size("30GB")    -> 30720  (MB)
        _parse_size("4 GB")    -> 4096   (MB)
        _parse_size("512")     -> 512    (MB)  # bare number keeps unit
        _parse_size("50GB", unit="KB") -> 52428800  (KB)

    Returns ``None`` if the string cannot be parsed.
    """
    m = re.match(
        r"^\s*(\d+(?:\.\d+)?)\s*(TB|GB|MB|KB|B)?\s*$",
        value_str,
        re.IGNORECASE,
    )
    if not m:
        return None
    amount = float(m.group(1))
    suffix = (m.group(2) or unit).upper()
    # Convert to bytes first, then to the requested unit.
    to_bytes = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    from_bytes = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    return int(amount * to_bytes[suffix] / from_bytes[unit])


def _normalize_attribute(key):
    """
    Normalize an attribute key to its canonical ClassAd name.

    Accepts both submit-file style (``request_memory``) and direct ClassAd
    names (``RequestMemory``).  Unknown keys are returned as-is.
    """
    return _SUBMIT_TO_CLASSAD.get(key.lower(), key)


def _parse_assignment(assignment):
    """
    Parse a ``key=value`` assignment string.

    Returns ``(classad_attr, raw_value, display_value)`` where:
    - *classad_attr* is the canonical ClassAd attribute name
    - *raw_value* is the value to store internally (converted for memory/disk)
    - *display_value* is a human-friendly string for output (e.g. ``"30 GB"``)

    Raises ``SystemExit`` with a friendly error for invalid input.
    """
    if "=" not in assignment:
        print_error(
            f"Invalid assignment '{assignment}'. "
            "Expected format: key=value (e.g. request_memory=30GB)."
        )
        sys.exit(1)

    key, _, value_str = assignment.partition("=")
    key = key.strip()
    value_str = value_str.strip()

    if not key or not value_str:
        print_error(
            f"Invalid assignment '{assignment}'. "
            "Both a key and a value are required (e.g. request_memory=30GB)."
        )
        sys.exit(1)

    classad_attr = _normalize_attribute(key)

    # Convert memory values (stored in MB).
    if classad_attr in _MEMORY_MB_ATTRS:
        mb = _parse_size(value_str, unit="MB")
        if mb is None:
            print_error(
                f"Could not parse memory value '{value_str}'. "
                "Use a number optionally followed by MB, GB, or TB (e.g. 30GB, 2048MB)."
            )
            sys.exit(1)
        raw_value = mb
        display_value = format_memory(mb)
        return classad_attr, raw_value, display_value

    # Convert disk values (stored in KB).
    if classad_attr in _DISK_KB_ATTRS:
        kb = _parse_size(value_str, unit="KB")
        if kb is None:
            print_error(
                f"Could not parse disk value '{value_str}'. "
                "Use a number optionally followed by KB, MB, GB, or TB (e.g. 50GB, 10000000)."
            )
            sys.exit(1)
        raw_value = kb
        display_value = format_memory(kb // 1024) if kb >= 1024 else f"{kb} KB"
        return classad_attr, raw_value, display_value

    # For all other attributes, pass the value through.
    return classad_attr, value_str, value_str


# ---------------------------------------------------------------------------
# Verb handlers
# ---------------------------------------------------------------------------

def jobs_submit(args):
    """Handle ``htcondor jobs submit <submit_file>``."""
    submit_file = args.submit_file
    cluster_id = 1046
    num_procs = 3

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
        cluster_id = 1047
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
        line = f"\n  {DIM}JobStatus changed: Running → Held"
        if reason:
            line += f"\n  HoldReason set: \"{reason}\""
        print(line + RESET)

    print_hint(f"Use `htcondor jobs release {label}` to release this job when ready.")


def jobs_release(args):
    """Handle ``htcondor jobs release <job_id>``."""
    job_id_raw = args.job_id
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    print_confirmation("released", label)

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}JobStatus changed: Held → Idle")
        print(f"  HoldReason cleared.{RESET}")

    print_hint(f"Use `htcondor jobs status {label}` to monitor this job.")


def jobs_remove(args):
    """Handle ``htcondor jobs remove <job_id>``."""
    job_id_raw = args.job_id
    force = getattr(args, "force", False)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    action = "forcefully removed" if force else "removed"
    print_confirmation(action, label)

    if getattr(args, "verbose", False):
        line = f"\n  {DIM}JobStatus changed: → Removed"
        if force:
            line += "\n  Force-remove: job will not run cleanup hooks."
        print(line + RESET)

    print_hint("Use `htcondor jobs report` to see remaining jobs.")


def jobs_edit(args):
    """Handle ``htcondor jobs edit <job_id> <key>=<value>``."""
    job_id_raw = args.job_id
    assignment = args.assignment
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    classad_attr, raw_value, display_value = _parse_assignment(assignment)

    print(f"{GREEN}✓{RESET} Job {BOLD}{label}{RESET}: set {BOLD}{classad_attr}{RESET} = {display_value}")

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}Attribute '{classad_attr}' updated to {raw_value} for job {label}.{RESET}")

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
