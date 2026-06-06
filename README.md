# UC — Undetected Checker

> **Production-grade multi-account credential validator** powered by Undetected ChromeDriver, rektCaptcha auto-solve, and a rich Tkinter GUI.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [GUI Reference](#gui-reference)
- [Extensions](#extensions)
- [Stealth & Anti-Detection](#stealth--anti-detection)
- [Session Modes](#session-modes)
- [CAPTCHA Handling](#captcha-handling)
- [Proxy Support](#proxy-support)
- [Results & Output](#results--output)
- [Configuration Files](#configuration-files)
- [Engine Architecture](#engine-architecture)
- [Known Limitations](#known-limitations)
- [Changelog](#changelog)

---

## Overview

UC is a fully automated account-checking tool that:

1. Reads a list of `email:password` credentials
2. Launches an **undetected Chrome browser** (bypasses Cloudflare, DataDome, and standard bot-detection)
3. Navigates to any configured login URL
4. Fills in credentials with **human-like typing jitter** and realistic mouse movements
5. Detects valid/invalid/captcha outcomes using configurable CSS selectors
6. Saves results to timestamped folders with screenshots and a SQLite database
7. Optionally solves CAPTCHAs via the **rektCaptcha** extension (auto-open + auto-solve)

---

## Features

| Category | Feature |
|---|---|
| **Browser** | Undetected ChromeDriver (UC mode), physical Chrome attachment, dynamic port allocation |
| **Anti-Detection** | Randomized user-agent rotation, human jitter typing (WPM variance), stealth Chrome flags |
| **CAPTCHA** | rektCaptcha extension (auto-open/auto-solve patched on load), Moodle + Shaparak solvers |
| **Session** | Same-session reuse across accounts, isolated per-account sessions, profile locking/cleanup |
| **Proxy** | HTTP/SOCKS4/SOCKS5, per-account rotation, round-robin and random modes |
| **Results** | CSV export, SQLite DB, per-account screenshots, timestamped result folders |
| **GUI** | Full Tkinter GUI with live action log, progress tracking, tabbed settings |
| **Stealth** | CDP cookie injection, network fingerprint masking, JavaScript stealth patches |
| **Log Ingestion** | Map per-account cookie files via database for pre-authenticated sessions |
| **AI Discovery** | OpenRouter-powered CSS selector auto-discovery for new login forms |

---

## Architecture

```
accounts_checker_builder-main/
├── validator_pro_v2.py          # Main entry point — GUI + orchestration
├── chrome_extensions/           # CRX extension files loaded into every session
│   ├── Reviews-rektCaptcha-reCaptcha-Solver.crx
│   ├── Moodle-Eacads-Captcha-Solver-Chrome-Web-Store.crx
│   └── Shaparak-Captcha-Solver-Chrome-Web-Store.crx
├── engine/
│   ├── kernel/
│   │   ├── browser_factory.py   # Chrome launch, retry logic, zombie cleanup
│   │   ├── cleaner.py           # Browser close + profile cleanup
│   │   ├── processor_v2.py      # Account processing pipeline
│   │   ├── selector_discoverer.py  # AI-powered CSS selector discovery
│   │   └── toolkit.py           # Shared utilities
│   ├── core/
│   │   ├── discovery_manager.py # Selector discovery orchestration
│   │   └── openrouter_integration.py  # OpenRouter AI client
│   ├── integrations/
│   │   ├── app_config.py        # Application configuration layer
│   │   ├── db_pool.py           # SQLite connection pooling
│   │   ├── discovery_bridge.py  # Bridge between discovery + kernel
│   │   ├── event_bus.py         # Internal event pub/sub
│   │   └── discovery_schema.py  # DB schema definitions
│   ├── registry/
│   │   ├── settings_manager.py  # Persistent settings load/save
│   │   ├── modern_settings.py   # Settings data model
│   │   ├── legacy_settings.py   # Backwards-compatible settings reader
│   │   ├── ai_config.json       # AI model configuration
│   │   └── captcha_settings.json  # CAPTCHA solver configuration
│   └── utils/
│       ├── driver_config.py     # ChromeDriver configuration helpers
│       ├── driver_updater.py    # Auto-update chromedriver binary
│       ├── profile_editor.py    # Chrome profile manipulation
│       └── web_updater.py       # Remote update checks
├── browser_reinstaller.py       # One-click Chrome reinstall utility
├── extension_configurator.py    # CDP-based extension runtime configurator
├── human_jitter.py              # Keystroke timing humanizer
├── locator.py                   # Cross-platform path resolver
├── network_stealth.py           # Network fingerprint stealth patches
├── openrouter_client.py         # OpenRouter API wrapper
├── session_isolation.py         # Per-account Chrome profile isolation
└── requirements.txt             # Python dependencies
```

---

## Requirements

- **OS:** Windows 10/11 (x64)
- **Python:** 3.10 – 3.13
- **Google Chrome:** Version 120+ (matching chromedriver auto-downloaded)
- **RAM:** 4 GB minimum, 8 GB recommended (each Chrome instance uses ~300 MB)

### Python Dependencies

```
selenium
undetected-chromedriver
colorama
requests
chromedriver-autoinstaller
Pillow
pyautogui
```

Install with:

```bash
pip install -r requirements.txt
```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/usemanusai/UC.git
cd UC

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
python validator_pro_v2.py
```

> **No global installs required.** All dependencies are local to the project virtualenv.

---

## Quick Start

1. **Run** `python validator_pro_v2.py`
2. In the GUI, set **Website URL** → the login page URL
3. Set **Valid URL** → a URL fragment that only appears after successful login
4. Paste your `email:password` list (one per line) into the accounts box
5. Configure CSS selectors for **email field**, **password field**, and **submit button**
6. Click **Check Accounts**

Results appear in a new `results_YYYYMMDD_HHMMSS/` folder.

---

## GUI Reference

### Main Tabs

| Tab | Purpose |
|---|---|
| **Accounts** | Paste credential list, set target URL, valid/invalid URL patterns |
| **Selectors** | CSS selectors for email, password, submit, next buttons |
| **Capture** | Screenshot settings, speed percentage, sleep durations |
| **Stealth** | User-agent rotation, cookie injection, CDP stealth flags |
| **Proxy** | Enable/disable proxy, proxy list, rotation mode |
| **Extensions** | Toggle Developer Mode auto-enable, view loaded extensions |
| **Session** | Same-session vs. isolated session mode, profile management |
| **AI Discovery** | Auto-discover CSS selectors using OpenRouter AI |

### Key Controls

| Control | Description |
|---|---|
| **Check Accounts** | Start the account validation run |
| **Stop** | Gracefully halt after current account completes |
| **Developer Mode** | Auto-enables Chrome Developer Mode after each launch |
| **Load Extensions** | Toggle loading of CRX extensions into the browser |
| **Same Session** | Reuse the same browser across all accounts (faster) |
| **Isolated Sessions** | Separate Chrome profile per account (more stealthy) |

---

## Extensions

Extensions are loaded from `chrome_extensions/` as CRX files. They are **automatically unpacked** into `_ext_unpacked/` on first run.

| Extension | Purpose |
|---|---|
| `Reviews-rektCaptcha-reCaptcha-Solver.crx` | Auto-opens and auto-solves reCAPTCHA v2/v3 |
| `Moodle-Eacads-Captcha-Solver-Chrome-Web-Store.crx` | Moodle-specific captcha solver |
| `Shaparak-Captcha-Solver-Chrome-Web-Store.crx` | Shaparak payment gateway captcha |

### rektCaptcha Auto-Patching

On every run, the tool **patches `background.js`** inside the rektCaptcha extension to force:
- `recaptcha_auto_open = true`
- `recaptcha_auto_solve = true`

This ensures CAPTCHA solving is always active regardless of user settings saved inside the extension.

---

## Stealth & Anti-Detection

### Browser Launch
- Uses `undetected-chromedriver` to patch ChromeDriver signatures
- Launches physical Chrome (not embedded), attaches via CDP debug port
- Randomized debug port per session
- 5-attempt retry with zombie Chrome cleanup between attempts

### Human Jitter Typing
- `human_jitter.py` simulates realistic WPM variation (40–80 WPM)
- Random inter-keystroke delays matching human typing patterns
- Occasional "typo + backspace" simulation

### CDP Tab Sweeper
- Background thread monitors Chrome tabs via CDP every 300ms
- Closes any non-main tabs that aren't `chrome-extension://` URLs
- Prevents memory exhaustion from extension popups accumulating

### User-Agent Rotation
- Configurable list of real Chrome user-agents
- Rotated per-account in round-robin or random mode

---

## Session Modes

### Same Session (Default)
- One browser is launched and reused for all accounts
- Faster (no Chrome restart per account)
- Less stealthy (shared cookies/fingerprint across accounts)

### Isolated Sessions
- Separate `temp_sessions/session_XXXXXXXXXXXX/` profile per account
- Each account gets a fresh Chrome identity
- Extension CRX files are re-injected into each isolated profile
- Profile directories are cleaned up after each run

---

## CAPTCHA Handling

The tool uses a **passive solving approach** — rektCaptcha runs in the browser extension layer and solves CAPTCHAs automatically without any code intervention:

```
Page loads → reCAPTCHA appears
  → rektCaptcha extension detects it (auto-open)
  → rektCaptcha solves it (auto-solve)
  → Submit button becomes available
  → Tool clicks submit and continues
```

If the submit button is not found within 30 seconds → account is **aborted** (not retried), moving to the next account.

---

## Proxy Support

### Proxy Formats
```
host:port
host:port:username:password
socks5://host:port
socks4://host:port:username:password
```

### Modes
| Mode | Behaviour |
|---|---|
| **Round-Robin** | Cycles through proxy list in order |
| **Random** | Picks a random proxy for each account |
| **Single** | Uses one fixed proxy for all accounts |

---

## Results & Output

Each run creates a `results_YYYYMMDD_HHMMSS/` folder:

```
results_20260528_170041/
├── valid.txt          # Confirmed valid accounts
├── invalid.txt        # Confirmed invalid accounts
├── unknown.txt        # Inconclusive (CAPTCHA, timeout, etc.)
├── checked.db         # SQLite database with full run history
└── screenshots/       # Per-account screenshots (if enabled)
    ├── account1@example.com_valid.png
    └── account2@example.com_invalid.png
```

---

## Configuration Files

| File | Purpose |
|---|---|
| `engine/registry/ai_config.json` | OpenRouter model selection, API key |
| `engine/registry/captcha_settings.json` | CAPTCHA solver preferences |
| `engine/registry/settings.pkl` | Persisted GUI settings (auto-saved) |
| `engine/registry/configs/` | Per-site selector configuration presets |

### Pre-built Selector Presets
The `engine/registry/configs/` directory ships with ready-to-use presets for:
- `my_digiseller_com.txt` — Digiseller login
- `gmail_config.txt` — Gmail login
- `honey_config.txt` — Honey extension login
- `pastebin_config.txt` — Pastebin login

---

## Engine Architecture

### Browser Factory (`engine/kernel/browser_factory.py`)
- Manages Chrome lifecycle: launch → attach → prune tabs → stamp CDP port → return driver
- 5-attempt retry loop with exponential backoff
- Zombie Chrome process cleanup between retries (`_kill_chrome_processes_for_profile`)
- Profile directory unlock (`_unlock_profile`) between retries
- Tab pruning: removes duplicate handles, keeps `handles[0]` (original tab)

### Session Isolation (`session_isolation.py`)
- Creates isolated Chrome user-data directories per account
- Copies extension unpacked directories into each isolated profile
- Cleans up stale sessions on startup

### Human Jitter (`human_jitter.py`)
- Injects random delays between keystrokes using a Gaussian distribution
- Logs WPM for each typing session

### Selector Discoverer (`engine/kernel/selector_discoverer.py`)
- Uses OpenRouter AI to analyze page DOM
- Auto-discovers CSS selectors for login forms on new websites
- Persists discovered selectors to `engine/registry/discovery_results.db`

---

## Known Limitations

- **Windows only** — Chrome profile paths and registry operations are Windows-specific
- **Chrome 120+** — Older Chrome versions may not be compatible with the UC chromedriver
- **reCAPTCHA v3** — Invisible v3 challenges may not be solved by rektCaptcha on all sites
- **Rate limiting** — Sites with IP-based rate limiting require proxy rotation enabled
- **Profile locking** — If Chrome crashes hard, run the tool again and it will auto-clean zombie processes

---

## Changelog

### 2026-06-06 — Auto-Save Inputs & Rust Browser Discovery Stabilized
- **Auto-Save on Keystroke**: Bound `<KeyRelease>` and `<FocusOut>` events to all Tkinter Entry and Text widgets (including target/valid URLs, CSS selectors, sleep durations, and accounts list) to auto-save settings debounced (1.5 seconds) so that no input values are lost on restart or crash.
- **Rust Agent-Browser Fix**: Solved the hang on the target website by dividing the discovery loop into three clean phases (Phase A: action commands execution, Phase B: JSON-formatted snapshot retrieval via `snapshot -i`, and Phase C: DOM element extraction using JS query evaluation). Replaced inline command structures with the standard chained commands `&&` execution and added proper timeouts (120s/30s) to subprocess calls to prevent infinite hangs.

### 2026-05-28 — Buster Removed, rektCaptcha Stabilized
- **REMOVED** Buster extension entirely (caused 20-30s hangs on every CAPTCHA, never worked reliably)
- **KEPT** rektCaptcha, Moodle, Shaparak solvers
- rektCaptcha `background.js` patched on every CRX unpack: `auto_open=ON`, `auto_solve=ON`
- CDPSweep: never closes `chrome-extension://` URLs (protects solver extension tabs)

### 2026-05-28 — Browser Crash & Subprocess Fix
- **FIXED** `UnboundLocalError: cannot access free variable 'subprocess'` in `browser_factory.py`
- **FIXED** zombie Chrome processes locking profiles across retry attempts
- Added `_kill_chrome_processes_for_profile()` + `_unlock_profile()` between retry attempts

### 2026-05-27 — Extension Loading & Toolbar Pinning
- Extensions now auto-unpack CRX → `_ext_unpacked/` on first run
- Developer Mode auto-enable via shadow DOM JS after each browser launch
- rektCaptcha source-patch approach replacing unreliable CDP runtime injection

---

## License

Private repository — all rights reserved.
