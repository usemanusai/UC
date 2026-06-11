import os
import re
import sys

# Mermaid diagrams to inject at the top of the export markdown
MERMAID_DIAGRAMS = """# UC System Architecture & Structural Flows

## 1. High-Level Architecture Diagram
```mermaid
graph TD
    UI[Tkinter GUI: validator_pro_v2.py]
    EDF[EDF Priority Scheduler: scheduler.py]
    SI[Session Isolation Manager: session_isolation.py]
    BF[Browser Factory: browser_factory.py]
    HE[Heuristic CSS Engine: heuristics.py]
    TDA[Topological DOM Matcher: tda.py]
    CR[Zero-Trust Cryptography: crypto.py]
    EN[Thermodynamic Entropy Monitor: entropy.py]
    CDP[Chrome DevTools Protocol - CDP]

    UI -->|Schedules validation tasks| EDF
    EDF -->|Executes checked tasks| SI
    SI -->|Configures temp profiles & rotates HWID| BF
    BF -->|Launches Undetected Chrome| CDP
    CDP -->|Validates page states| HE
    HE -->|Fallback on obfuscation| TDA
    TDA -->|Tree Edit Distance matching| CDP
    SI -->|Encrypts registry & settings| CR
    BF -->|Verifies fingerprint distribution| EN
```

## 2. Topological Element Selection Sequence
```mermaid
sequenceDiagram
    autonumber
    participant V as validator_pro_v2.py
    participant H as heuristics.py
    participant T as tda.py (Zhang-Shasha TED)
    participant C as Chrome Browser (CDP)

    V->>C: Look up element via Config Selector (Tier 1)
    alt Selector Found
        C-->>V: Return element
    else Selector Missing / Obfuscated (Timeout)
        V->>H: Query common fallback patterns (Tier 2)
        H->>C: Scan 80+ CSS selectors & placeholders
        alt Heuristics Match
            C-->>V: Return element & update UI config
        else Heuristics Fail
            V->>T: Retrieve page DOM Tree (Tier 3)
            T->>C: Extract current accessibility / DOM tree
            C-->>T: Return target DOM Node tree
            T->>T: Compute Tree Edit Distance (ZSS) against reference template
            T->>T: Verify Lipschitz Continuity Constraint (L2C2) on coordinates
            T-->>V: Return closest structural match
            V->>C: Execute pyautogui human-jitter click on match
        end
    end
```

## 3. Cryptographic Key Derivation & State Protection
```mermaid
graph LR
    PW[User Master Password / Key] --> KDF[Argon2id KDF: derive_key_argon2id]
    RAM[System Physical RAM Detection] -->|Scales Memory Cost: 19MB - 64MB| KDF
    KDF -->|Derives 256-bit Key| AES[AES-GCM Encryption Engine]
    TPM[TPM 2.0 Silicon sealing] -->|Seals derived keys| AES
    DPAPI[Windows DPAPI Backup] -->|Fallback if TPM absent| AES
    AES -->|Encrypts| DB[(sessions_registry.db: clock_json, data_dir, value)]
    AES -->|Encrypts| CFG[(settings.json: GUI state, credentials)]
```

---

"""

# Exclusion criteria
EXCLUDE_DIRS = {
    'node_modules', '.venv', 'venv', 'env', '.git', 'temp_sessions', 
    '_ext_unpacked', '_ext_test_7z', '_ext_test_output', 'output', 
    'scratch', '.vscode', '.idea', 'DELETED', 'all_results', 'RESULTS', 
    '__pycache__', 'media', 'data', 'configs'
}

EXCLUDE_PREFIXES = ('results_', '2026-')

EXCLUDE_FILES = {
    'settings.json', 'settings.json.bak', 'settings.pkl', 'settings.pkl.bak',
    'discovery_results.db', 'checked.db', 'test_accounts.db', 'ocr_results.txt',
    'System_Audit_Log.json', 'application.log', 'auto_click_direct.log',
    'auto_click_v2.log', 'tab_monitor.log', 'validator_captured.log',
    'validator_direct.log', 'validator_err.log', 'run_validator_captured_out.log',
    'chromedriver.exe', 'chromedriver143.exe', 'honeygain.txt', 
    'mercadolivre1.txt', 'miniapps_clean.txt', 'pastebin.com_userpass.txt',
    'codebase_export.md', 'plan.md', 'export_architecture.py'
}

ALLOWED_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.js', '.mjs', '.ts', '.sh'}

def redact_secrets(content: str) -> str:
    """Redacts potential secrets, passwords, or API keys from strings."""
    # Redact variables containing tokens or keys followed by string literals
    patterns = [
        (r'(?i)(api_key|openrouter_key|token|bot_token|password|pass|secret|auth)\s*(=|:)\s*([\'"])(?:[^\'"]{4,})(?:\3)', r'\1 \2 \3[REDACTED]\3'),
        (r'(?i)(telegram_token|client_secret)\s*=\s*([\'"])[^\'"]+\2', r'\1 = \2[REDACTED]\2')
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content

def should_process_dir(dir_name: str) -> bool:
    """Checks if directory should be skipped."""
    if dir_name in EXCLUDE_DIRS:
        return False
    for prefix in EXCLUDE_PREFIXES:
        if dir_name.startswith(prefix):
            return False
    return True

def should_process_file(file_name: str) -> bool:
    """Checks if file should be skipped."""
    if file_name in EXCLUDE_FILES:
        return False
    ext = os.path.splitext(file_name)[1]
    return ext in ALLOWED_EXTENSIONS

def generate_export():
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(project_root, 'codebase_export.md')
    
    print(f"Starting codebase export from: {project_root}")
    print(f"Export target path: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8', newline='\n') as out:
        out.write("# UC Codebase Architecture & Source Export\n\n")
        out.write("This file contains the complete codebase source and architectural flowcharts for NotebookLM research.\n\n")
        
        # Inject Mermaid diagrams
        out.write(MERMAID_DIAGRAMS)
        
        # Walk directories
        file_count = 0
        for root, dirs, files in os.walk(project_root):
            # Prune directories in-place to prevent os.walk from entering them
            dirs[:] = [d for d in dirs if should_process_dir(d)]
            
            for file in sorted(files):
                if not should_process_file(file):
                    continue
                
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, project_root).replace('\\', '/')
                
                print(f"Exporting: {rel_path}")
                
                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_content = f.read()
                    
                    redacted = redact_secrets(raw_content)
                    
                    # Markdown section header
                    out.write(f"## File: `{rel_path}`\n\n")
                    
                    # Language identifier for syntax highlighting
                    ext = os.path.splitext(file)[1]
                    lang = 'python'
                    if ext == '.md':
                        lang = 'markdown'
                    elif ext in ('.js', '.mjs'):
                        lang = 'javascript'
                    elif ext == '.ts':
                        lang = 'typescript'
                    elif ext == '.sh':
                        lang = 'bash'
                    elif ext == '.json':
                        lang = 'json'
                    elif ext == '.txt':
                        lang = 'text'
                        
                    out.write(f"```{lang}\n")
                    out.write(redacted)
                    if not redacted.endswith('\n'):
                        out.write('\n')
                    out.write("```\n\n---\n\n")
                    
                    file_count += 1
                except Exception as e:
                    print(f"Error reading file {rel_path}: {e}", file=sys.stderr)
                    
        print(f"\nExport complete! Exported {file_count} files successfully.")

if __name__ == '__main__':
    generate_export()
