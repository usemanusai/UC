# Voyager's Journal

## Critical Learnings

- **Integration Gap Discovered**: The project uses an SQLite database `discovery_results.db` and `checked_accounts.db` to store history and results, but there is no built-in way to export this data into a more universally readable format like CSV.
- **Proposed Feature**: SQLite Log-to-CSV Report Generator. This completes the workflow (as mentioned in Voyager's favorite features) and provides a highly requested way to review validation results offline or in Excel/Google Sheets.
- **Integration Gap Discovered**: Zombie Chrome processes and stale temporary session directories were piling up without an active cleanup mechanism, risking disk space exhaustion and memory leaks.
- **Proposed Feature**: Automated Session Integrity & Cleanup Daemon. I implemented `CleanupDaemon` (`engine/core/cleanup_daemon.py`) which acts as a background thread to garbage collect older `temp_sessions` and use `psutil` to forcefully terminate any orphaned Chrome processes.

- **Integration Gap Discovered**: The project routes numerous captcha requests through `CaptchaDispatcher` to 3rd party providers, but lacks any visibility into total requests, success rates, or fail rates, making it difficult to gauge API usage or provider reliability locally.
- **Proposed Feature**: Local-first Captcha Solver stats dashboard. I implemented a thread-safe `CaptchaStatsManager` to persist stats locally and a Tkinter `CaptchaStatsDashboard` allowing users to quickly see overall metrics and per-provider breakdown of solves.

- **Integration Gap Discovered**: Dead or blocked proxies inside the `ProxyRotator` were delaying validation runs by waiting for full browser timeouts to occur before being skipped.
- **Proposed Feature**: Automated Proxy Health Checker. I implemented `ProxyHealthDaemon` (`engine/core/proxy_health.py`) which periodically pings proxies in the background via TCP and reports failures to the rotator, skipping dead nodes before connection attempts.
