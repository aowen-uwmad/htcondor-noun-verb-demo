# HTCondor Noun-Verb CLI Style Guide

This guide captures the command-line style used by the demo so new nouns/verbs
stay consistent.

## Command and option style

- Use the command shape `htcondor <noun> <verb> [options] [args]`.
- Prefer long options (`--option-name`) for clarity; add short aliases only for
  common, high-frequency flags.
- Use **kebab-case** for user-facing argument placeholders
  (for example `job-id`, `submit-file`).
- Keep global flags available everywhere:
  - `-h, --help`
  - `-v, --verbose`
  - `-d, --debug` (repeatable)
- For required identifiers, use positional arguments (for example `job-id` on
  `hold`, `release`, `remove`, `edit`).
- Keep help text action-oriented and concise (start with a verb).

## Output style

- Use section headers for report/table views.
- Use aligned uppercase column headers for tables (`JOB_ID`, `STATUS`, ...).
- Use the standard confirmation/error/hint patterns:
  - success: `✓ Job <id> ...`
  - error: `Error: ...`
  - follow-up guidance: `Hint: ...`
- End command output with a practical next-step hint where possible.
- Keep units human-readable (`4 GB`, compact durations like `1h 45m`).
