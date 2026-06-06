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
- [GUI Tab Parameter Index (Complete Catalog)](#gui-tab-parameter-index-complete-catalog)
- [Advanced Core Features Manual](#advanced-core-features-manual)
  - [1. The 3-Tier CSS Locator & Fallback Engine](#1-the-3-tier-css-locator--fallback-engine)
  - [2. Automated Selector Discovery Modes](#2-automated-selector-discovery-modes)
  - [3. Behavioral Jitter System](#3-behavioral-jitter-system)
  - [4. Session Profile Seeding & Isolation](#4-session-profile-seeding--isolation)
  - [5. Claude Proxy Fallback Integration](#5-claude-proxy-fallback-integration)
  - [6. Telegram Reporting Subsystem](#6-telegram-reporting-subsystem)
  - [7. Tab Monitoring & Port Scan Daemon](#7-tab-monitoring--port-scan-daemon)
- [Extensions & Solvers](#extensions--solvers)
- [Proxy Support](#proxy-support)
- [Results & Output](#results--output)
- [Configuration Files](#configuration-files)
- [Known Limitations](#known-limitations)
- [Changelog](#changelog)

---

## Overview

UC is a fully automated account-checking tool designed for modern, high-security login forms. It features:

1. **Undetected Chrome Integration**: Bypasses Cloudflare, DataDome, and advanced bot-detection systems by attaching to physical Chrome instances via randomized debug ports.
2. **Behavioral Human Jitter**: Simulates realistic mouse movements (Cubic Bézier curves) and keyboard input (Gaussian WPM models + cognitive hesitations).
3. **Robust Fallback Engine**: Uses a 3-tier selector matching hierarchy (Explicit -> Heuristic Dictionary -> CDP AI Self-Discovery).
4. **Isolated Sandbox Profiles**: Allocates fresh, locked directories and randomized ports per validation process, with pre-configured extensions and toolbar auto-pinning.
5. **Passive & Active Captcha Solvers**: Integrates `rektCaptcha` for browser-level captcha auto-solving, alongside custom models and a local Claude proxy bridge.

---

## Features

| Category | Feature |
|---|---|
| **Browser Kernel** | Undetected ChromeDriver (UC mode), physical headed/headless Chrome attachment, duplicate tab sweeping |
| **Stealth & Mimicry** | Parametric Bézier cursor drift, Gaussian typing WPM modeling, machine HWID rotation, custom user-agents |
| **Fallback Engine** | Explicit GUI configuration, native multithreaded heuristic dictionary, CDP-connected AI discovery |
| **Discovery Squads** | CrewAI explorer/analyst/verifier squads, persistentheaded Rust browser 3-phase exploration loop |
| **Session & Sandbox** | Same-session reuse, per-account temp profiles, Preferences file write-ahead seeding, toolbar pin synchronization |
| **Captcha Solvers** | rektCaptcha CRX auto-patching, Moodle and Shaparak resolvers, OCR cache database, local Claude completions proxy |
| **Proxy Routing** | HTTP/HTTPS/SOCKS5, round-robin, random, and single-proxy mapping |
| **Log Ingestion** | Bulk log importer matching password files with cookies, per-account SQLite ingestion |
| **Telemetry & Alerts** | Real-time entropy uniqueness monitor, Telegram bot messenger with 4000-char safety clamping, CDP tab scanner |

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
│   │   ├── discovery_bridge.py  # Bridge between discovery + kernel
│   │   └── discovery_schema.py  # Pydantic v2 schema definitions
│   ├── integrations/
│   └── registry/
│       └── discovery_results.db # SQLite database of discovered selectors
├── configs/                     # Pre-built site CSS selector presets (Gmail, Honey, Digiseller, Pastebin)
├── ai_captcha/                  # Claude AI-powered CAPTCHA solver and HTTP proxy bridge
│   ├── claude_proxy_bridge.py   # OCR-based CAPTCHA resolver API bridge
│   └── ocr_results.txt          # OCR cache file
├── agents/                      # CrewAI orchestration and agent workflows
│   └── free_browser_automation_enhancement_squad_v1_crewai-project/
├── discovery_squad/             # Autonomous element discovery agents
├── web-reader/                  # Web scanning and scraping skill module
├── web-search/                  # Google/DDG web search skill module
├── web-shader-extractor/        # Canvas and WebGL shader signature extractor
├── browser_reinstaller.py       # One-click Chrome reinstall utility
├── extension_configurator.py    # CDP-based extension runtime configurator
├── human_jitter.py              # Keystroke timing humanizer
├── locator.py                   # Cross-platform path resolver
├── network_stealth.py           # Network fingerprint stealth patches
├── openrouter_client.py         # OpenRouter API wrapper
├── session_isolation.py         # Per-account Chrome profile isolation
├── tab_monitor.py               # Brute-force port scan and active tab monitor
└── requirements.txt             # Python dependencies
```

---

## Requirements

- **OS:** Windows 10/11 (x64)
- **Python:** 3.10 – 3.13
- **Google Chrome:** Version 120+ (matching chromedriver auto-downloaded)
- **RAM:** 4 GB minimum, 8 GB recommended (each Chrome instance uses ~300 MB)

Install dependencies with:
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

---

## Quick Start

1. **Run** `python validator_pro_v2.py`.
2. Set **Website Target Link** (e.g., `https://example.com/login`) and **Website Valid Link** (e.g., `dashboard` or `welcome`).
3. Paste credentials in `email:password` format into the **Account Inputs** box at the bottom.
4. Set the selectors for email, password, and submit, or use the **✨ Auto-Discover** feature in the stealth tab.
5. Click **Check Accounts**.

---

## GUI Tab Parameter Index (Complete Catalog)

The Tkinter GUI is organized into 11 specialized configuration tabs:

### 1. REQUIRED: General Settings
- **Lock UI Toolbar**: Buttons to manage editing/dragging state.
  - `🔒 Lock`: Prevents dragging of sequence blocks and disables editing of the fields.
  - `🔓 Unlock`: Enables field editing and drag-and-drop block reordering.
  - `↺ Reset to Default`: Rebuilds the sequence back to the default 11 fields.
  - `🎨 Theme Colors`: Opens the color customizer dialog to modify the dark-theme UI palettes.
  - `➕ Add Workflow Rule`: Opens the custom workflow step builder:
    - **Step Types**: `Text Input` (maps to `custom_text`), `Click Element` (maps to `custom_click`), `Sleep Delay` (maps to `custom_sleep`).
    - **Step Label**: Customized name for the generated block.
- **Draggable Field Sequence Blocks**:
  - `Website Target Link (Required)`: The starting entrypoint login URL.
  - `Website Valid Link (Required)`: String fragment matching post-login URLs upon success.
  - `Redirect URL (Optional)`: Matches specific intermediate redirect paths.
  - `CSS Selector for Email / Username (Required)`: Selector for target input field.
  - `CSS Selector for Next Button (Optional)`: Multi-step transition click selector.
  - `Sleep Duration (Email)`: Time (0-100s) to wait for page to transition after inputting email.
  - `CSS Selector for Password (Required)`: Selector for password input.
  - `CSS Selector for Next Button Password (Optional)`: Click selector for intermediate password page.
  - `Sleep Duration (Password)`: Time (0-100s) to wait for transition after inputting password.
  - `CSS Selector for Submit / Login Button (Required)`: Selector for final submit.
  - `Sleep Duration (Submit)`: Time (0-100s) to wait after submit to confirm success or failure.

### 2. REQUIRED: Capture Settings
- **Enable Inner HTML Capture**: Checkbutton (boolean). Captures the raw inner text content of the page post-login.
- **Enable Outer HTML Capture**: Checkbutton (boolean). Captures the raw outer HTML string of the target page.
- **Capture Screenshot**: Checkbutton (boolean). Triggers a full-window screen capture upon finding a valid account.
- **CSS Selectors to Capture**: Input list and `+ Add CSS Selector` button. Dynamically appends input boxes to capture specific DOM texts (e.g., `span.account-balance`, `div.user-role`).
- **Redirect Link (Optional)**: Entry. Navigates the browser to this page (e.g., `/profile`) post-login before taking screenshots or capturing html.
- **Telegram Notifications**:
  - **Enable Telegram Notifications**: Checkbutton (boolean).
  - **Bot Token**: Entry. The unique Telegram bot API key.
  - **Chat ID**: Entry. Chat/channel ID for incoming messages.

### 3. REQUIRED: Invalid Account
- **Check this and Enable Invalid Account Checks**: Checkbutton (boolean). Must be checked to enable validation failure logic.
- **Redirect Detection URL**: Entry. Matches URL redirect paths indicating login failure.
- **Error/Alert Detection CSS Selector**: Entry. Target error alert alert container.
- **Inner HTML Text**: Entry. Case-insensitive error text patterns indicating failure.
- **Outer HTML Text**: Entry. Tag fragment structures indicating failure.

### 4. OPTIONAL: CAPTCHA Incorrect is Recheck
- **Enable CAPTCHA Incorrect Checks**: Checkbutton (boolean). Triggers a recheck/retry loop if login fails due to CAPTCHA issues.
- **Redirect Detection URL**: Entry. Match URL on CAPTCHA block redirects.
- **Error/Alert Detection CSS Selector**: Entry. Target CAPTCHA alert box.
- **Inner HTML Text**: Entry. Captcha error strings (e.g., "Verification failed", "invalid captcha").
- **Outer HTML Text**: Entry. Captcha outer container tags.

### 5. OPTIONAL: Proxy Settings
- **Enable Proxy**: Checkbutton (boolean).
- **Proxy Type**: Dropdown. Select `HTTP`, `HTTPS`, or `SOCKS5`.
- **Proxy Mode**: Dropdown. Select `Static Proxies` or `Rotating Proxies`.
- **Import Proxies from File**: Button. Loads newline-separated proxy files.

### 6. REQUIRED: Browser Settings
- **Clean Browser Data After Each Account Check**: Checkbutton (boolean). Clears local storage, cookies, and cache between accounts.
- **Use Same Browser Session for All Accounts**: Checkbutton (boolean). Keeps Chrome open across checks (speeds up process).
- **Run Browser in Incognito Mode**: Checkbutton (boolean). Appends `--incognito` flag.

### 7. OPTIONAL: Advanced Settings
- **Load Chrome Extensions**: Checkbutton (boolean). Unpacks and injects extensions from the `chrome_extensions/` folder.
- **Disable Browser Notifications**: Checkbutton (boolean). Appends `--disable-notifications`.
- **Disable Infobars**: Checkbutton (boolean). Appends `--disable-infobars`.
- **Start Browser Maximized**: Checkbutton (boolean). Appends `--start-maximized`.
- **Disable Browser Extensions**: Checkbutton (boolean). Blocks all extension loading.
- **Run Browser in Headless Mode**: Checkbutton (boolean). Runs Chrome without a visible window.
- **Use Custom User Agents**: Checkbutton (boolean). Enables user-agent rotation.
- **Select User Agents File**: Button. Loads list of user agents.
- **Use Databases**: Checkbutton (boolean). Saves history to SQLite databases.

### 8. OPTIONAL: Chromedriver Arguments
- **Add Chromedriver Argument**: Entry. User-supplied Chrome command-line switch.
- **Add Argument Button**: Appends switch to the active list.
- **Current Chromedriver Arguments Listbox**: Displays all loaded parameters.
- **Remove Selected Argument(s) Button**: Deletes arguments from execution.

### 9. OPTIONAL: Mouse Click Automation
- **Enable Mouse Click Automation**: Checkbutton (boolean).
- **Coordinate-based Clicks**: Table of `(X, Y)` coordinate buttons. Simulates native mouse clicks.
- **CSS Selector-based Clicks**: Table of CSS selectors. Clicks elements upon page loading.

### 10. VALIDATOR PRO: Stealth & AI
- **Enable Isolated Sessions (Unique Ports & Directories)**: Checkbutton (boolean). Assigns random high ports and sandboxed profile directories.
- **Enable Developer Mode for Extensions**: Checkbutton (boolean). Pre-authorizes unpacked extensions in `Preferences` to bypass security warnings.
- **Enable Kernel-Level Purge (AppData wiping)**: Checkbutton (boolean). Cleans all browser artifacts on major blocks.
- **Enable HWID Subsystem Spoofing**: Checkbutton (boolean). Alters registry/MachineGuid values.
- **Enable Persona Jitter (Bézier Mimicry)**: Checkbutton (boolean). Enables human-like movements and WPM typing intervals.
- **OpenRouter API Key(s)**: Entry. API key for selector auto-discovery and CAPTCHA solving.
- **AI Vision Model**: Combobox. Target OpenRouter LLM.
- **Claude Proxy Fallback**:
  - **Use Claude Proxy as fallback**: Checkbutton (boolean). Routes completions to localhost.
  - **Claude Proxy URL**: Entry. Local proxy API URL.
  - **Claude Proxy Model**: Entry. Proxy model definition.
- **Live Entropy Monitor**: Canvas showing browser fingerprint entropy graph.
- **Proxy List File**: Entry and `Browse...` button.
- **Cookie List File**: Entry and `Browse...` button. Inject cookies via CDP.
- **Automated Log Ingestion Engine**:
  - **Enable Automated Log Ingestion**: Checkbutton (boolean). Matches accounts to SQLite cookies.
  - **Auto-enable Session Isolation**: Checkbutton (boolean).
  - **Bulk Import from Logs Folder**: Button. Recursively scans stealer logs folders containing `Passwords.txt` and sibling `Cookies.json`.

### 11. Configuration Menu
- **Create New Config**: Setup new site presets.
- **Import Config**: Load preset `.txt` parameters.
- **Export Config**: Export current UI configuration.
- **Save Config State**: Persist GUI settings in settings registry.
- **Reset to Default**: Reset all GUI settings.

---

## Advanced Core Features Manual

### 1. The 3-Tier CSS Locator & Fallback Engine

To maximize success, UC does not rely solely on user-configured selectors. If an element is missing, it runs a 3-tier matching process:

```
[UI/Config Selector] (Tier 1)
       │
       ▼ (if fails)
[Native Heuristic Scan] (Tier 2) -> Scans 80+ common patterns and error phrases
       │
       ▼ (if fails)
[CDP AI Self-Discovery] (Tier 3) -> Connects to browser port, fetches DOM, queries LLM
```

#### Tier 1: Explicit Configuration
Runs a recursive frame-switching search (`_find_element_in_frames`) to locate elements inside any nested iframes.

#### Tier 2: Native Heuristic Scan (<2 seconds)
Directly searches for elements using a massive built-in dictionary:
- **Email Field**: 80+ CSS selectors including common ID variations, names, types, multi-language placeholder attributes (English, Russian, German, French, Chinese, Japanese, Korean, Arabic, etc.), aria-labels, and data-testids.
- **Password Field**: 80+ CSS selectors verifying `type="password"`, current-password autocompletes, and multi-language placeholders.
- **Submit / Next Buttons**: 100+ selectors targeting primary/login class names, action attributes, and value mappings.
- **Error Alerts**: Loops through `_ERROR_CSS_SELECTORS` and checks texts against `_ERROR_TEXT_PATTERNS` (covering 140+ expressions in over 30 languages). If found, it parses the DOM tree using a custom JavaScript `TreeWalker` to extract details and auto-saves the discovered selector back to the GUI.

#### Tier 3: CDP AI Self-Discovery (30–60 seconds)
Extracts the browser's active CDP port, connects via `agent-browser --cdp <port>`, takes an interactive accessibility tree snapshot, executes a custom JS evaluation query to gather up to 150 DOM elements, and queries OpenRouter/Claude proxy. The AI selects the target ref (e.g. `@e3`) or CSS selector and interacts with the page in real-time. The discovered selector is then synced back to the GUI.

---

### 2. Automated Selector Discovery Modes

Located in the **Stealth & AI** tab, this subsystem automatically discovers selectors for new websites:

#### A. Standard (AI Crew) Mode
- **Execution**: Runs in a background thread.
- **Orchestration**: Extracts the raw HTML, cleans and tokenizes it down to the most critical interactive elements (inputs, buttons, select, errors) capping at 150 tags.
- **Schema Validation**: Sends the clean DOM payload to OpenRouter or the Claude proxy. The response is parsed and validated using a Pydantic v2 `DiscoveryResult` model. This model verifies that no hallucinated markup (like URLs or code blocks) is present and ensures at least one primary login element exists.
- **Cache Database**: Discovered selectors are saved to `engine/registry/discovery_results.db`. The cache is valid for 7 days.

#### B. Rust Agent-Browser Mode
- **Interactive exploration**: Prompts the user for test credentials via a custom modal dialog.
- **Initialization**: Automatically cleans up zombie browser instances and loads required Chrome extensions (e.g., `rektCaptcha` solver) by reading paths from the `_ext_unpacked/` directory.
- **CDP Session Loop**: Spawns a headed/headless Chromium window under a persistent session name (`discovery_session`). It executes a 3-Phase Step Loop:
  - **Phase A (Action)**: Executes browser movement commands (`open`, `fill`, `click`, `wait`) chained with `&&` to keep the daemon session alive.
  - **Phase B (Snapshot)**: Takes a JSON accessibility tree snapshot using the custom Rust `snapshot -i` command.
  - **Phase C (Eval)**: Runs a custom JS query to gather detailed interactive element metadata.
- **Decision Engine**: Sends the current page state, accessibility tree, and execution history to the AI to determine the next logical action (e.g., waiting for captcha solver, filling fields, clicking buttons) until login completes or fails. The extracted selectors are then loaded into the GUI.

---

### 3. Behavioral Jitter System

Located in `human_jitter.py`, this module replaces standard Selenium macros with human-like interactions:

- **AI Personas**: Supported profiles include:
  - `systematic_researcher`: Typified by slow typing speeds (60 WPM), high cognitive hesitations, smooth cursor curves (low offsets), and careful scrolling.
  - `frustrated_user`: Fast typing speed (100 WPM), low hesitation, sharp cursor curves (high offsets), and fast, aggressive scrolling.
- **Cubic Bézier Cursor Paths**: Generates natural mouse paths between coordinate points `P0` and `P3` using two randomized control points `P1` and `P2` influenced by the active persona. Pauses between mouse increments are randomized between 1ms and 5ms.
- **Keystroke Simulator**: Simulates human typing speeds based on WPM. Character delays vary from 50% to 250% of the calculated WPM base delay, interspersed with randomized cognitive pauses (200–500ms) on a percentage of characters.
- **Non-linear scrolling**: Scrolls pages using JavaScript `window.scrollBy` divided into random increments. The step delay and scroll size adjust dynamically according to the persona's `scroll_aggressiveness` factor.

---

### 4. Session Profile Seeding & Isolation

Located in `session_isolation.py`, this subsystem isolates profiles to prevent account tracking:

- **Unique Directory & Port Allocation**: Allocates isolated profile directories (`temp_sessions/session_XXXXXXXX/`) and checks localhost sockets to bind unique ports (15000–25000) for debugger connections.
- **Preferences Seeding**: Prior to launching Chrome, writes a raw JSON `Preferences` file into the new profile folder (specifically under `Profile 1`). This seeds `has_seen_welcome_page=True` and `developer_mode=True` to prevent the initial Welcome wizard and enable extension loading.
- **Verified Extension ID Parsing**: Unpacked extensions require stable IDs to execute scripts in cross-origin frames. The manager reads `_metadata/verified_contents.json`, decodes the JWS signed-content payload via Base64url, and extracts the authentic Chrome Web Store `item_id` (falling back to MD5 if missing).
- **Toolbar Pinning**: Invokes `extension_configurator.py` to pin the loaded extension IDs directly in Chrome's internal registry, ensuring their icons are visible on the toolbar from the start.
- **Stale Cleanups**: Performs directory garbage collection on startup, deleting profiles older than 3600 seconds.

---

### 5. Claude Proxy Fallback Integration

Located in `ai_captcha/claude_proxy_bridge.py`, this module routes AI solver calls through a local proxy:

- **Proxy Endpoint**: When the local proxy toggle is checked (or no OpenRouter keys are set), requests are sent to `http://localhost:8080/v1/chat/completions`.
- **API Payload Matching**: Translates standard OpenRouter requests to local proxy-compatible formats, swapping model identifiers to local models (e.g. `gemini-3-flash`) and bypassing authorization.
- **Health Verification**: Periodically pings `http://localhost:8080/health` using `httpx` (falling back to `requests` if missing) to check proxy availability.
- **OCR Cache**: Captcha solutions are saved in `ai_captcha/ocr_results.txt` to prevent duplicate API requests for identical captcha challenges.

---

### 6. Telegram Reporting Subsystem

Sends notifications to a Telegram channel or chat:

- **Custom Formatting**: Formats valid credentials and captures fields into a structured notification message.
- **Filter large payloads**: Automatically excludes large HTML payloads (`inner_html`, `outer_html`) to keep messages readable.
- **Safety Clamping**: Messages are capped at 4000 characters (Telegram limit: 4096) to prevent API payload errors.

---

### 7. Tab Monitoring & Port Scan Daemon

Located in `tab_monitor.py`, this utility runs alongside the checker to monitor active sessions:

- **Brute-Force Scanner**: Scans localhost ports (10000–20000) in chunks of 500. It queries `/json/version` to locate active Chrome CDP ports.
- **Tab Monitoring**: Connects to the active port's `/json` endpoint every 500ms, logging the URLs, page titles, and IDs of all open pages to `tab_monitor.log`.

---

## Extensions & Solvers

CRX extensions in `chrome_extensions/` are auto-extracted to `_ext_unpacked/` at runtime:
1. `Reviews-rektCaptcha-reCaptcha-Solver.crx` (Auto-solves reCAPTCHA v2/v3).
2. `Moodle-Eacads-Captcha-Solver-Chrome-Web-Store.crx` (Moodle captcha solver).
3. `Shaparak-Captcha-Solver-Chrome-Web-Store.crx` (Shaparak payment solver).

### rektCaptcha Auto-Patching
To ensure captcha solving is always active, UC modifies `background.js` during extension extraction:
- Sets `recaptcha_auto_open = true`
- Sets `recaptcha_auto_solve = true`

---

## Proxy Support

Supports multiple formats (`host:port`, `host:port:user:pass`, `socks5://host:port`) and modes:
- **Round-Robin**: Rotates through proxies sequentially.
- **Random**: Assigns a random proxy per account.
- **Single**: Applies one proxy for the entire run.

---

## Results & Output

Each run creates a timestamped results directory containing:
- `valid.txt`: Valid credentials.
- `invalid.txt`: Invalid credentials.
- `unknown.txt`: Accounts that failed due to CAPTCHA or timeout issues.
- `checked.db`: SQLite history database.
- `screenshots/`: PNG screenshots of valid logins.

---

## Configuration Files

- `engine/registry/ai_config.json`: Model configurations.
- `engine/registry/captcha_settings.json`: Solver parameters.
- `engine/registry/settings.pkl`: Persisted GUI settings.
- `engine/registry/configs/`: Directory containing prebuilt selector configurations:
  - `my_digiseller_com.txt` (Digiseller login configuration)
  - `gmail_config.txt` (Gmail configuration)
  - `honey_config.txt` (Honey extension login configuration)
  - `pastebin_config.txt` (Pastebin login configuration)

---

## Known Limitations

- **Windows Only**: Uses Windows-specific registry calls and paths.
- **Chrome Compatibility**: Requires Google Chrome version 120+.
- **invisible CAPTCHAs**: Invisible reCAPTCHA challenges may fail if the target site detects automation.

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
