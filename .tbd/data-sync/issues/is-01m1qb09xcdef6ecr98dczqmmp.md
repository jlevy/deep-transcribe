---
type: is
id: is-01m1qb09xcdef6ecr98dczqmmp
title: Add a flag to show tracebacks on the console
kind: task
status: open
priority: 3
version: 1
labels: []
dependencies: []
parent_id: is-01m1n3knrvxt38paq147xp42s3
created_at: 2026-09-04T23:10:33.387Z
updated_at: 2026-09-04T23:10:33.387Z
---
There is no --verbose/--debug/log-level flag: cli_main.py hardcodes console_log_level=LogLevel.warning, so KASH_LOG_LEVEL cannot reach it. Since dt-ljkg, recognised media failures print one line and the traceback goes only to the log file (whose path the message prints). That is right by default; a real console-traceback switch is a separate change threading a flag into that kash_setup call.
