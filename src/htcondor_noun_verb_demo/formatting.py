"""
Shared output-formatting helpers for the demo CLI.

Provides consistent, polished terminal output across all commands.
"""

import re
import sys


# ---------------------------------------------------------------------------
# ANSI colour helpers (disabled when output is not a terminal)
# ---------------------------------------------------------------------------

_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _sgr(code):
    """Return an ANSI SGR escape if colour is enabled, else empty string."""
    return f"\033[{code}m" if _USE_COLOR else ""


BOLD = _sgr("1")
DIM = _sgr("2")
GREEN = _sgr("32")
YELLOW = _sgr("33")
RED = _sgr("31")
CYAN = _sgr("36")
RESET = _sgr("0")


# ---------------------------------------------------------------------------
# Table printing
# ---------------------------------------------------------------------------

_ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*m")


def _display_len(text):
    """Return the visible display length of a string, ignoring ANSI escape codes."""
    return len(_ANSI_ESCAPE.sub("", str(text)))


def _pad(text, width, right_align=False):
    """Pad *text* to *width* visible characters, accounting for ANSI codes."""
    text = str(text)
    pad = width - _display_len(text)
    if pad <= 0:
        return text
    if right_align:
        return " " * pad + text
    return text + " " * pad


def print_table(headers, rows, right_align=None):
    """
    Print a simple aligned text table.

    Parameters
    ----------
    headers : list[str]
        Column header labels.
    rows : list[list[str]]
        Row data (each inner list is one row, same length as *headers*).
    right_align : set[int] | None
        Column indices (0-based) that should be right-aligned.
    """
    if right_align is None:
        right_align = set()

    # Compute column widths using visible (ANSI-stripped) lengths
    col_widths = [_display_len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], _display_len(cell))

    def _fmt_row(cells):
        parts = []
        for i, cell in enumerate(cells):
            width = col_widths[i]
            parts.append(_pad(cell, width, right_align=(i in right_align)))
        return "  ".join(parts)

    # Header
    print(f"{BOLD}{_fmt_row(headers)}{RESET}")

    # Separator (not needed for some views, but aids readability)

    # Rows
    for row in rows:
        print(_fmt_row(row))


# ---------------------------------------------------------------------------
# Confirmation and hint helpers
# ---------------------------------------------------------------------------

def print_confirmation(action, job_id, extra=""):
    """Print a standardised action-confirmation message."""
    msg = f"{GREEN}✓{RESET} Job {BOLD}{job_id}{RESET} {action}."
    if extra:
        msg += f"  {extra}"
    print(msg)


def print_hint(text):
    """Print a 'next step' hint for the user."""
    print(f"\n{DIM}Hint: {text}{RESET}")


def print_error(text):
    """Print an error message to stderr."""
    print(f"{RED}Error:{RESET} {text}", file=sys.stderr)


def print_section(title):
    """Print a section heading."""
    print(f"\n{BOLD}{title}{RESET}")
    print("─" * max(len(title), 40))


def format_duration(td):
    """Format a timedelta as a compact duration string, e.g. '1h 45m'."""
    total_seconds = int(td.total_seconds())
    if total_seconds < 0:
        return "—"
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes:02d}m")
    return " ".join(parts)


def format_memory(mb):
    """Format memory in MB as a human-friendly string (e.g. '4 GB')."""
    if mb >= 1024:
        return f"{mb / 1024:.0f} GB"
    return f"{mb} MB"
