"""
Handlers for the ``htcondor jobs`` noun.

Each public function in this module is wired up as the ``command``
default for the corresponding argparse sub-parser created in ``main.py``.
"""

import logging
import os
import re
import sys

from htcondor_noun_verb_demo.mock_data import MOCK_JOBS, JOB_STATUS_MAP, _NOW
from htcondor_noun_verb_demo.formatting import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    format_duration,
    format_memory,
    print_confirmation,
    print_detail_block,
    print_detail_header,
    print_error,
    print_hint,
    print_section,
    print_table,
)


# ---------------------------------------------------------------------------
# Module-level loggers  (only activated at debug level 3 / -ddd)
# ---------------------------------------------------------------------------

_htcondor_log = logging.getLogger("htcondor_noun_verb_demo.htcondor")
_cli_log = logging.getLogger("htcondor_noun_verb_demo.cli")


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
    _cli_log.debug("Parsing job ID from input: %r", raw)
    try:
        if "." in raw:
            parts = raw.split(".", 1)
            cluster, proc = int(parts[0]), int(parts[1])
            _cli_log.debug("Parsed job ID → ClusterId=%d, ProcId=%d", cluster, proc)
            return cluster, proc
        cluster = int(raw)
        _cli_log.debug("Parsed job ID → ClusterId=%d, ProcId=<all>", cluster)
        return cluster, None
    except ValueError:
        print_error(f"Invalid job ID '{raw}'. Expected format: <cluster> or <cluster>.<proc> (e.g. 1042 or 1042.0).")
        sys.exit(1)


def _filter_jobs(job_id_raw=None):
    """Return the subset of MOCK_JOBS matching the optional *job_id_raw*."""
    if job_id_raw is None:
        _cli_log.debug("No job ID filter supplied; returning all %d jobs", len(MOCK_JOBS))
        return list(MOCK_JOBS)
    cluster, proc = _parse_job_id(job_id_raw)
    matches = [
        j for j in MOCK_JOBS
        if j["ClusterId"] == cluster and (proc is None or j["ProcId"] == proc)
    ]
    _cli_log.debug(
        "Filter ClusterId=%d ProcId=%s matched %d job(s)",
        cluster, proc if proc is not None else "<all>", len(matches),
    )
    for j in matches:
        status_code = j["JobStatus"]
        _htcondor_log.debug(
            "Matched job ClassAd: ClusterId=%d ProcId=%d "
            "JobStatus=%d (%s) Owner=%s",
            j["ClusterId"], j["ProcId"],
            status_code, JOB_STATUS_MAP.get(status_code, "Unknown"),
            j["Owner"],
        )
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

    Returns ``(classad_attr, raw_value, display_value, original_key)`` where:
    - *classad_attr* is the canonical ClassAd attribute name
    - *raw_value* is the value to store internally (converted for memory/disk)
    - *display_value* is a human-friendly string for output (e.g. ``"30 GB"``)
    - *original_key* is the key as the user typed it (before normalization)

    Raises ``SystemExit`` with a friendly error for invalid input.
    """
    _cli_log.debug("Parsing assignment string: %r", assignment)
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

    original_key = key
    classad_attr = _normalize_attribute(key)
    _htcondor_log.debug(
        "Attribute key %r normalized to ClassAd name %r", key, classad_attr
    )

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
        _htcondor_log.debug(
            "ClassAd %s: value %r converted to %d MB (%s)",
            classad_attr, value_str, raw_value, display_value,
        )
        return classad_attr, raw_value, display_value, original_key

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
        _htcondor_log.debug(
            "ClassAd %s: value %r converted to %d KB (%s)",
            classad_attr, value_str, raw_value, display_value,
        )
        return classad_attr, raw_value, display_value, original_key

    # For all other attributes, pass the value through.
    _htcondor_log.debug("ClassAd %s: value %r passed through as-is", classad_attr, value_str)
    return classad_attr, value_str, value_str, original_key


# ---------------------------------------------------------------------------
# Verb handlers
# ---------------------------------------------------------------------------

def jobs_submit(args):
    """Handle ``htcondor jobs submit <submit_file>``."""
    debug = getattr(args, "debug", 0)
    submit_file = args.submit_file
    _cli_log.debug("jobs_submit called with submit_file=%r", submit_file)
    cluster_id = 1046
    num_procs = 3
    submit_host = "ap2001.chtc.wisc.edu"
    iwd = os.path.dirname(os.path.abspath(submit_file))

    print(f"Submitting job(s) from: {BOLD}{submit_file}{RESET}")
    print(f"  {GREEN}✓{RESET} {num_procs} job(s) submitted to cluster {BOLD}{cluster_id}{RESET}.")

    if 0 < debug < 3:
        print_detail_block([
            ("Cluster ID",  str(cluster_id)),
            ("Procs",       f"{num_procs}  ({cluster_id}.0 – {cluster_id}.{num_procs - 1})"),
            ("Submit host", submit_host),
            ("IWD",         iwd),
        ])

    if debug == 2:
        print_detail_header("CLI detail")
        print_detail_block([
            ("submit_file", submit_file),
            ("condor_submit", "htcondor_noun_verb_demo.handlers.jobs.jobs_submit"),
        ], label_color=YELLOW)

    print_hint(
        f"Use `htcondor jobs status {cluster_id}` to monitor your jobs, "
        f"or `htcondor jobs report` for a summary."
    )


def jobs_status(args):
    """Handle ``htcondor jobs status [job_id]``."""
    debug = getattr(args, "debug", 0)
    job_id_raw = getattr(args, "job_id", None)
    _cli_log.debug("jobs_status called with job_id=%r", job_id_raw)

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

        status_code = j["JobStatus"]
        _htcondor_log.debug(
            "Job ClassAd %s: JobStatus=%d (%s) "
            "RequestCpus=%d RequestMemory=%d MB RequestDisk=%d KB "
            "RemoteHost=%r ImageSize=%d",
            jid, status_code, JOB_STATUS_MAP.get(status_code, "Unknown"),
            j["RequestCpus"], j["RequestMemory"], j["RequestDisk"],
            j["RemoteHost"], j["ImageSize"],
        )

    print_table(headers, rows, right_align={2, 3})

    # Summary line
    status_counts = {}
    for j in jobs:
        s = j["JobStatusStr"]
        status_counts[s] = status_counts.get(s, 0) + 1
    summary_parts = [f"{count} {status}" for status, count in status_counts.items()]
    print(f"\n{DIM}Total: {len(jobs)} job(s)  ({', '.join(summary_parts)}){RESET}")

    # Level 1: per-job ClassAd detail blocks
    if 0 < debug < 3:
        for j in jobs:
            jid = f"{j['ClusterId']}.{j['ProcId']}"
            status_str = j["JobStatusStr"]
            queue_ago = format_duration(_NOW - j["QDate"]) if j["QDate"] else "—"
            run_time = (
                format_duration(_NOW - j["JobStartDate"]) if j["JobStartDate"] else "—"
            )
            disk_display = (
                format_memory(j["RequestDisk"] // 1024)
                if j["RequestDisk"] >= 1024
                else f"{j['RequestDisk']} KB"
            )
            img_display = (
                format_memory(j["ImageSize"] // 1024)
                if j["ImageSize"] >= 1024
                else (f"{j['ImageSize']} KB" if j["ImageSize"] else "—")
            )
            pairs = [
                ("Job ID",       jid),
                ("Status",       _status_colour(status_str)),
                ("Owner",        j["Owner"]),
                ("Executable",   j["Cmd"]),
                ("Arguments",    j["Args"] or "—"),
                ("CPUs",         str(j["RequestCpus"])),
                ("Memory",       format_memory(j["RequestMemory"])),
                ("Disk",         disk_display),
            ]
            if j["RemoteHost"]:
                pairs.append(("Execute host", j["RemoteHost"]))
            if j["ImageSize"]:
                pairs.append(("Image size", img_display))
            pairs.append(("Queued", f"{queue_ago} ago"))
            if j["JobStartDate"]:
                pairs.append(("Run time", run_time))
            if j.get("HoldReason"):
                pairs.append(("Hold reason", j["HoldReason"]))
            print_detail_header(f"Job {jid}")
            print_detail_block(pairs)

    # Level 2: filter / parsing detail
    if debug == 2:
        print_detail_header("CLI detail")
        if job_id_raw:
            # Derive the parsed result from the matched jobs (avoids a duplicate
            # _parse_job_id call that would re-emit log messages at level 3).
            parsed_cluster = jobs[0]["ClusterId"]
            proc_ids = {j["ProcId"] for j in jobs}
            proc_str = (
                str(next(iter(proc_ids))) if "." in job_id_raw else "all procs"
            )
            print_detail_block([
                ("Job ID input",  job_id_raw),
                ("Parsed",        f"ClusterId={parsed_cluster}, ProcId={proc_str}"),
                ("Filter result", f"{len(jobs)} job(s) matched"),
            ], label_color=YELLOW)
        else:
            print_detail_block([
                ("Job ID input",  "(none — all jobs)"),
                ("Filter result", f"{len(jobs)} job(s) matched"),
            ], label_color=YELLOW)

    print_hint(
        "Use `htcondor jobs status <job_id>` for a specific job, "
        "or `htcondor jobs report` for an aggregate summary."
    )


def jobs_report(args):
    """Handle ``htcondor jobs report``."""
    debug = getattr(args, "debug", 0)
    _cli_log.debug("jobs_report called")
    owner = MOCK_JOBS[0]["Owner"]

    # Tally by status
    status_counts = {}
    cluster_info = {}
    for j in MOCK_JOBS:
        s = j["JobStatusStr"]
        status_counts[s] = status_counts.get(s, 0) + 1
        _htcondor_log.debug(
            "Job ClassAd %d.%d: JobStatus=%d (%s)",
            j["ClusterId"], j["ProcId"], j["JobStatus"],
            JOB_STATUS_MAP.get(j["JobStatus"], "Unknown"),
        )
        cid = j["ClusterId"]
        if cid not in cluster_info:
            cluster_info[cid] = {"procs": 0, "cpus": 0, "memory": 0, "statuses": {}}
        cluster_info[cid]["procs"] += 1
        cluster_info[cid]["cpus"] += j["RequestCpus"]
        cluster_info[cid]["memory"] += j["RequestMemory"]
        cluster_info[cid]["statuses"][s] = cluster_info[cid]["statuses"].get(s, 0) + 1

    total = len(MOCK_JOBS)
    clusters = len(cluster_info)

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

    # Level 1: per-cluster resource breakdown
    if 0 < debug < 3:
        print_detail_header("Per-cluster breakdown")
        for cid, info in sorted(cluster_info.items()):
            procs = info["procs"]
            proc_range = f"{cid}.0 – {cid}.{procs - 1}" if procs > 1 else f"{cid}.0"
            status_summary = ", ".join(
                f"{cnt} {st}" for st, cnt in info["statuses"].items()
            )
            print_detail_block([
                ("Cluster",  str(cid)),
                ("Procs",    f"{procs}  ({proc_range})"),
                ("CPUs",     str(info["cpus"])),
                ("Memory",   format_memory(info["memory"])),
                ("Status",   status_summary),
            ])

    # Level 2: scan detail
    if debug == 2:
        print_detail_header("CLI detail")
        print_detail_block([
            ("Jobs scanned",    str(total)),
            ("Clusters found",  str(clusters)),
            ("Status counters", str(status_counts)),
        ], label_color=YELLOW)

    print_hint(
        "Use `htcondor jobs status <job_id>` to inspect a specific job, "
        "or `htcondor jobs release <job_id>` to release held jobs."
    )


def jobs_interact(args):
    """Handle ``htcondor jobs interact``."""
    debug = getattr(args, "debug", 0)
    submit_file = getattr(args, "submit_file", None)
    job_id = getattr(args, "job_id", None)
    _cli_log.debug("jobs_interact called with submit_file=%r job_id=%r", submit_file, job_id)

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
        exec_host = "slot1@e1001.chtc.wisc.edu"
        sandbox = "/var/lib/condor/execute/dir_29501"
        print(f"Connecting to running job {BOLD}{cluster}.{proc}{RESET}…")
        print(f"  → Establishing SSH tunnel to {exec_host}")
        print(f"  → Connection established.")
        print()
        print(f"  {GREEN}You are now logged in to the execute node for job {cluster}.{proc}.{RESET}")
        print(f"  Working directory: {sandbox}")
        print(f"  Type 'exit' to disconnect.")

        if 0 < debug < 3:
            print_detail_block([
                ("Job ID",       f"{cluster}.{proc}"),
                ("Execute host", exec_host),
                ("Sandbox",      sandbox),
                ("SSH hook",     "condor_ssh_to_job"),
            ])

        if debug == 2:
            print_detail_header("CLI detail")
            print_detail_block([
                ("job_id input", job_id),
                ("Parsed",       f"ClusterId={cluster}, ProcId={proc}"),
            ], label_color=YELLOW)

        print_hint(
            f"When finished, use `htcondor jobs status {cluster}.{proc}` to verify the job is still running."
        )
    elif submit_file:
        # condor_submit -i path
        cluster_id = 1047
        exec_host = "slot1@e1003.chtc.wisc.edu"
        sandbox = "/var/lib/condor/execute/dir_31045"
        print(f"Submitting interactive job from: {BOLD}{submit_file}{RESET}")
        print(f"  → Job {cluster_id}.0 submitted.")
        print(f"  → Waiting for job {cluster_id}.0 to start…")
        print(f"  → Job started on {exec_host}")
        print(f"  → Connecting…")
        print()
        print(f"  {GREEN}You are now logged in to the execute node for job {cluster_id}.0.{RESET}")
        print(f"  Working directory: {sandbox}")
        print(f"  Type 'exit' to disconnect and remove the job.")

        if 0 < debug < 3:
            print_detail_block([
                ("Cluster ID",   str(cluster_id)),
                ("Job ID",       f"{cluster_id}.0"),
                ("Execute host", exec_host),
                ("Sandbox",      sandbox),
                ("Submit hook",  "condor_submit -i"),
            ])

        if debug == 2:
            print_detail_header("CLI detail")
            print_detail_block([
                ("submit_file", submit_file),
                ("mode",        "interactive (-i)"),
            ], label_color=YELLOW)

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
    debug = getattr(args, "debug", 0)
    job_id_raw = args.job_id
    reason = getattr(args, "reason", None)
    _cli_log.debug("jobs_hold called with job_id=%r reason=%r", job_id_raw, reason)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    # Determine previous status from mock data for detail block
    matched = [
        j for j in MOCK_JOBS
        if j["ClusterId"] == cluster and (proc is None or j["ProcId"] == proc)
    ]
    prev_status = matched[0]["JobStatusStr"] if matched else "Unknown"

    extra = ""
    if reason:
        extra = f'Reason: "{reason}"'

    print_confirmation("held", label, extra)

    _htcondor_log.debug(
        "ClassAd update for job %s: JobStatus → %d (%s)%s",
        label, 5, JOB_STATUS_MAP[5],
        f", HoldReason={reason!r}" if reason else "",
    )

    if 0 < debug < 3:
        pairs = [
            ("Job ID",        label),
            ("Status change", f"{prev_status} → {_status_colour('Held')}"),
        ]
        if reason:
            pairs.append(("Hold reason", reason))
        pairs.append(("ClassAd attr", f"JobStatus = 5  (HoldReason {'set' if reason else 'left empty'})"))
        print_detail_block(pairs)

    if debug == 2:
        print_detail_header("CLI detail")
        print_detail_block([
            ("job_id input", job_id_raw),
            ("Parsed",       f"ClusterId={cluster}, ProcId={proc if proc is not None else 'all'}"),
            ("reason",       reason or "(none)"),
        ], label_color=YELLOW)

    if getattr(args, "verbose", False):
        line = f"\n  {DIM}JobStatus changed: Running → Held"
        if reason:
            line += f"\n  HoldReason set: \"{reason}\""
        print(line + RESET)

    print_hint(f"Use `htcondor jobs release {label}` to release this job when ready.")


def jobs_release(args):
    """Handle ``htcondor jobs release <job_id>``."""
    debug = getattr(args, "debug", 0)
    job_id_raw = args.job_id
    _cli_log.debug("jobs_release called with job_id=%r", job_id_raw)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    matched = [
        j for j in MOCK_JOBS
        if j["ClusterId"] == cluster and (proc is None or j["ProcId"] == proc)
    ]
    prev_status = matched[0]["JobStatusStr"] if matched else "Unknown"
    prev_reason = matched[0].get("HoldReason", "") if matched else ""

    print_confirmation("released", label)

    _htcondor_log.debug(
        "ClassAd update for job %s: JobStatus → %d (%s), HoldReason cleared",
        label, 1, JOB_STATUS_MAP[1],
    )

    if 0 < debug < 3:
        pairs = [
            ("Job ID",        label),
            ("Status change", f"{prev_status} → {_status_colour('Idle')}"),
            ("ClassAd attr",  "JobStatus = 1  (HoldReason cleared)"),
        ]
        if prev_reason:
            pairs.insert(2, ("Previous reason", prev_reason))
        print_detail_block(pairs)

    if debug == 2:
        print_detail_header("CLI detail")
        print_detail_block([
            ("job_id input", job_id_raw),
            ("Parsed",       f"ClusterId={cluster}, ProcId={proc if proc is not None else 'all'}"),
        ], label_color=YELLOW)

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}JobStatus changed: Held → Idle")
        print(f"  HoldReason cleared.{RESET}")

    print_hint(f"Use `htcondor jobs status {label}` to monitor this job.")


def jobs_remove(args):
    """Handle ``htcondor jobs remove <job_id>``."""
    debug = getattr(args, "debug", 0)
    job_id_raw = args.job_id
    force = getattr(args, "force", False)
    _cli_log.debug("jobs_remove called with job_id=%r force=%r", job_id_raw, force)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    matched = [
        j for j in MOCK_JOBS
        if j["ClusterId"] == cluster and (proc is None or j["ProcId"] == proc)
    ]
    prev_status = matched[0]["JobStatusStr"] if matched else "Unknown"

    action = "forcefully removed" if force else "removed"
    print_confirmation(action, label)

    _htcondor_log.debug(
        "ClassAd update for job %s: JobStatus → %d (%s)%s",
        label, 3, JOB_STATUS_MAP[3],
        " (force-remove: cleanup hooks skipped)" if force else "",
    )

    if 0 < debug < 3:
        pairs = [
            ("Job ID",        label),
            ("Status change", f"{prev_status} → {_status_colour('Removed')}"),
            ("ClassAd attr",  "JobStatus = 3"),
        ]
        if force:
            pairs.append(("Cleanup hooks", "skipped  (--force)"))
        else:
            pairs.append(("Cleanup hooks", "will run"))
        print_detail_block(pairs)

    if debug == 2:
        print_detail_header("CLI detail")
        print_detail_block([
            ("job_id input", job_id_raw),
            ("Parsed",       f"ClusterId={cluster}, ProcId={proc if proc is not None else 'all'}"),
            ("force",        str(force)),
        ], label_color=YELLOW)

    if getattr(args, "verbose", False):
        line = f"\n  {DIM}JobStatus changed: → Removed"
        if force:
            line += "\n  Force-remove: job will not run cleanup hooks."
        print(line + RESET)

    print_hint("Use `htcondor jobs report` to see remaining jobs.")


def jobs_edit(args):
    """Handle ``htcondor jobs edit <job_id> <key>=<value>``."""
    debug = getattr(args, "debug", 0)
    job_id_raw = args.job_id
    assignment = args.assignment
    _cli_log.debug("jobs_edit called with job_id=%r assignment=%r", job_id_raw, assignment)
    cluster, proc = _parse_job_id(job_id_raw)
    label = _job_label(cluster, proc)

    classad_attr, raw_value, display_value, original_key = _parse_assignment(assignment)

    print(f"{GREEN}✓{RESET} Job {BOLD}{label}{RESET}: set {BOLD}{classad_attr}{RESET} = {display_value}")

    _htcondor_log.debug(
        "ClassAd update for job %s: %s = %r (display: %s)",
        label, classad_attr, raw_value, display_value,
    )

    if 0 < debug < 3:
        pairs = [
            ("Job ID",       label),
            ("Attribute",    classad_attr),
        ]
        if original_key.lower() != classad_attr.lower():
            pairs.append(("Key input",   f"{original_key}  →  {classad_attr}  (normalized)"))
        # Show the user-supplied raw string; if the key was normalized (e.g.
        # request_memory → RequestMemory) the raw string is the right-hand side
        # of the assignment, otherwise it is the already-converted raw_value.
        input_display = (
            assignment.split("=", 1)[1].strip()
            if original_key.lower() != classad_attr.lower()
            else str(raw_value)
        )
        pairs.append(("Input value",  input_display))
        if str(raw_value) != display_value:
            pairs.append(("Stored value", str(raw_value)))
            pairs.append(("Display value", display_value))
        print_detail_block(pairs)

    if debug == 2:
        print_detail_header("CLI detail")
        print_detail_block([
            ("job_id input",  job_id_raw),
            ("Parsed",        f"ClusterId={cluster}, ProcId={proc if proc is not None else 'all'}"),
            ("assignment",    assignment),
            ("ClassAd attr",  classad_attr),
            ("raw_value",     str(raw_value)),
        ], label_color=YELLOW)

    if getattr(args, "verbose", False):
        print(f"\n  {DIM}Attribute '{classad_attr}' updated to {display_value} for job {label}.{RESET}")

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
