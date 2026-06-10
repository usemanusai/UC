# Voyager's Journal

## Critical Learnings

- **Integration Gap Discovered**: The project uses an SQLite database `discovery_results.db` and `checked_accounts.db` to store history and results, but there is no built-in way to export this data into a more universally readable format like CSV.
- **Proposed Feature**: SQLite Log-to-CSV Report Generator. This completes the workflow (as mentioned in Voyager's favorite features) and provides a highly requested way to review validation results offline or in Excel/Google Sheets.
- **Integration Gap Discovered**: Zombie Chrome processes and stale temporary session directories were piling up without an active cleanup mechanism, risking disk space exhaustion and memory leaks.
- **Proposed Feature**: Automated Session Integrity & Cleanup Daemon. I implemented `CleanupDaemon` (`engine/core/cleanup_daemon.py`) which acts as a background thread to garbage collect older `temp_sessions` and use `psutil` to forcefully terminate any orphaned Chrome processes.

- **Integration Gap Discovered**: Captcha performance metrics were completely opaque, making it difficult to optimize routing between 3rd party providers (Capsolver vs 2Captcha vs Claude Proxy) based on speed or success rate.
- **Proposed Feature**: Local-first Captcha Solver stats dashboard. I implemented a singleton `CaptchaStatsManager` that records telemetry from `CaptchaDispatcher` locally to disk (`captcha_stats.json`). A new Tkinter dashboard displays success rates and average solve times to inform routing choices without exposing data to the cloud.
