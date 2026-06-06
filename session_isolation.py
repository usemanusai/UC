import socket
import random
import os
import json
import shutil
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


# IDs of Chrome's built-in component extensions that Chrome auto-installs in
# every fresh profile.  These are NOT user extensions and should be ignored.
_CHROME_COMPONENT_EXTENSION_IDS = {
    "ghbmnnjooekpmoecnnnilnnbdlolhkhi",  # Chrome Web Store Payments
    "jelniggicmclhfgnlapbkgfibmgelfnp",  # Google Chrome PDF Viewer (component)
    "lmjegmlicamnimmfhcmpkclmigmmcbeh",  # Chrome Media Router
    "nmmhkkegccagdldgiimedpiccmgmieda",  # Google Pay
}


class SessionIsolationManager:
    """
    Manages isolated browser sessions by assigning unique ports and directories.

    Extension support:
    - When load_extensions=True is passed to get_isolated_session(), a minimal
      Chrome Preferences file is written into the isolated profile directory
      BEFORE Chrome launches.  This tells Chrome the profile is established
      (not a fresh "Welcome" state), which is required for --load-extension=
      to be honoured reliably in fresh temp profiles.
    - The built-in component extensions Chrome auto-installs in every fresh
      profile (Google Pay, Media Router, etc.) are Chrome internals and cannot
      be prevented.  They do not interfere with user extensions.
    """

    def __init__(self, base_temp_dir: str = "temp_sessions"):
        self.base_temp_dir = os.path.abspath(base_temp_dir)
        if not os.path.exists(self.base_temp_dir):
            os.makedirs(self.base_temp_dir, exist_ok=True)

    def create_session(self, session_id: str) -> Tuple[int, str]:
        """Generates a unique port and data directory for a session."""
        port = self._find_free_port()
        data_dir = os.path.join(self.base_temp_dir, f"session_{session_id}")
        
        # Terminate any zombie Chrome processes using this directory first
        # to ensure that shutil.rmtree doesn't fail silently due to file locks.
        try:
            from engine.kernel.browser_factory import _kill_chrome_processes_for_profile
            _kill_chrome_processes_for_profile(data_dir)
        except Exception as ke:
            logger.warning(f"[Isolation] Pre-session cleanup process kill failed: {ke}")
            
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"[Isolation] Created session {session_id} on port {port} at {data_dir}")
        return port, data_dir

    def cleanup_session(self, session_id: str):
        """Deletes the data directory for a completed session."""
        data_dir = os.path.join(self.base_temp_dir, f"session_{session_id}")
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir, ignore_errors=True)
            logger.info(f"[Isolation] Cleaned up session {session_id}")

    def _find_free_port(self) -> int:
        """Finds an available high-range port."""
        for _ in range(50):
            port = random.randint(15000, 25000)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    return port
                except socket.error:
                    continue
        return 9222  # Fallback

    def purge_all(self):
        """Deletes all session directories."""
        if os.path.exists(self.base_temp_dir):
            shutil.rmtree(self.base_temp_dir, ignore_errors=True)
            os.makedirs(self.base_temp_dir, exist_ok=True)
            logger.info("[Isolation] All sessions purged.")

    def seed_profile_for_extensions(
        self, data_dir: str, profile_directory: str = "Profile 1",
        ext_dirs: Optional[list] = None,
    ) -> None:
        """
        Writes a Chrome Preferences file into the isolated session's profile dir
        BEFORE Chrome starts, doing three things:


        1. Marks the profile as 'previously-used' so Chrome skips the Welcome flow.
        2. Enables developer_mode so --load-extension= is honoured without dialogs.
        3. Pre-registers each extension directory in extensions.settings so Chrome
           loads them without needing any --load-extension= at all.  This is the
           most reliable path because Chrome reads Preferences before processing
           CLI flags.

        Parameters
        ----------
        data_dir : str
            Root temp session directory (e.g. temp_sessions/session_xxx/).
        profile_directory : str
            Chrome profile sub-dir name (default 'Profile 1').
        ext_dirs : list of str, optional
            Absolute paths to unpacked extension directories.  If provided each
            dir is registered in extensions.settings.
        """
        import json as _json

        if not profile_directory:
            profile_directory = "Default"

        profile_dir = os.path.join(data_dir, profile_directory)
        os.makedirs(profile_dir, exist_ok=True)
        prefs_path = os.path.join(profile_dir, "Preferences")
        if os.path.isfile(prefs_path):
            return  # Already seeded; don't overwrite.

        # Build extension settings entries for each unpacked dir so Chrome
        # treats them as developer-loaded extensions from the start.
        ext_settings = {}
        if ext_dirs:
            for ext_path in ext_dirs:
                manifest_file = os.path.join(ext_path, "manifest.json")
                if not os.path.isfile(manifest_file):
                    continue
                try:
                    with open(manifest_file, "r", encoding="utf-8") as mf:
                        mdata = _json.load(mf)
                    ext_version = mdata.get("version", "1.0")

                    # ── Derive real Chrome extension ID ───────────────────────────
                    # Chrome derives the extension ID from the signed_content payload
                    # in _metadata/verified_contents.json.  Using the real ID (not an
                    # MD5 placeholder) is required for content scripts (e.g. Buster's
                    # #solver-button) to be injected into cross-origin iframes.
                    real_ext_id = None
                    verified_path = os.path.join(
                        ext_path, "_metadata", "verified_contents.json"
                    )
                    if os.path.isfile(verified_path):
                        try:
                            import base64 as _b64
                            with open(verified_path, "r", encoding="utf-8") as vf:
                                vdata = _json.load(vf)
                            # The structure is [{..., "signed_content": {"payload": "<b64>"}}]
                            _payload_b64 = vdata[0]["signed_content"]["payload"]
                            # Add padding if needed
                            _pad = 4 - len(_payload_b64) % 4
                            if _pad < 4:
                                _payload_b64 += "=" * _pad
                            _payload = _json.loads(
                                _b64.urlsafe_b64decode(_payload_b64).decode("utf-8")
                            )
                            real_ext_id = _payload.get("item_id")
                        except Exception as _ve:
                            logger.debug(
                                f"[Isolation] Could not parse verified_contents.json "
                                f"for {ext_path}: {_ve}"
                            )

                    if not real_ext_id:
                        # Fallback: stable placeholder; Chrome ignores mismatched IDs
                        # but developer_mode=True + --load-extension= will still work
                        import hashlib as _hlib
                        real_ext_id = _hlib.md5(ext_path.encode()).hexdigest()[:32]
                        logger.debug(
                            f"[Isolation] No verified ID for {os.path.basename(ext_path)}; "
                            f"using MD5 placeholder: {real_ext_id}"
                        )
                    else:
                        logger.debug(
                            f"[Isolation] Using real extension ID for "
                            f"{os.path.basename(ext_path)}: {real_ext_id}"
                        )

                    # Extract permissions from manifest to grant content script injection rights
                    _api_perms = mdata.get("permissions", [])
                    _host_perms = mdata.get("host_permissions", [])
                    # Keep only string API permissions (not objects)
                    _api_perms_str = [p for p in _api_perms if isinstance(p, str)]

                    ext_settings[real_ext_id] = {
                        "active_permissions": {
                            "api": _api_perms_str,
                            "explicit_host": _host_perms,
                            "manifest_permissions": [],
                            "scriptable_host": _host_perms,
                        },
                        "from_bookmark": False,
                        "from_webstore": True,  # treat as webstore for full privilege grant
                        "granted_permissions": {
                            "api": _api_perms_str,
                            "explicit_host": _host_perms,
                            "manifest_permissions": [],
                            "scriptable_host": _host_perms,
                        },
                        "install_time": "13000000000000000",
                        "location": 4,   # 4 = LOAD (developer-loaded unpacked)
                        "manifest": mdata,
                        "path": ext_path,
                        "state": 1,      # 1 = ENABLED
                        "version": ext_version,
                        "was_installed_by_default": False,
                        "was_installed_by_oem": False,
                    }


                except Exception as _e:
                    logger.warning(
                        f"[Isolation] Could not read manifest for {ext_path}: {_e}"
                    )

        minimal_prefs = {
            "browser": {
                "has_seen_welcome_page": True,
                "show_home_button": False,
            },
            "profile": {
                "content_settings": {"exceptions": {}},
                "exit_type": "Normal",
                "exited_cleanly": True,
            },
            "extensions": {
                "alerts": {"initialized": True},
                "last_chrome_version": "",
                "settings": ext_settings,
                "ui": {
                    "developer_mode": True,   # ← critical: enables --load-extension=
                },
            },
            "privacy_sandbox": {"m1": {"consent_decision_made": True}},
        }

        try:
            with open(prefs_path, "w", encoding="utf-8") as fh:
                _json.dump(minimal_prefs, fh, indent=2)
            logger.info(
                f"[Isolation] Seeded Preferences (+developer_mode) in {profile_dir} "
                f"with {len(ext_settings)} pre-registered extension(s)."
            )
        except Exception as e:
            logger.warning(f"[Isolation] Could not seed Preferences: {e}")

        # ── PIN ALL EXTENSIONS TO TOOLBAR ────────────────────────────────────
        # After the Preferences file is written, immediately call
        # pin_extensions_in_preferences() so every loaded extension appears
        # pinned in the Chrome toolbar — users won't need to click the puzzle
        # icon and manually pin each one every session.
        if ext_settings:
            try:
                import sys as _sys
                _proj_root = os.path.dirname(os.path.abspath(__file__))
                if _proj_root not in _sys.path:
                    _sys.path.insert(0, _proj_root)
                from extension_configurator import pin_extensions_in_preferences as _pin
                _pin(prefs_path, list(ext_settings.keys()))
            except Exception as _pe:
                logger.warning(f"[Isolation] Toolbar pinning skipped: {_pe}")


    def _collect_all_ext_dirs(self, project_root: Optional[str] = None) -> list:
        """
        Collect all valid unpacked extension directories from both:
          1. _ext_unpacked/  (CRX files that were successfully unpacked)
          2. chrome_extensions/<subdir>/  (pre-unpacked dirs placed by the user)

        Returns list of absolute paths to directories containing manifest.json.
        """
        if project_root is None:
            project_root = os.path.dirname(os.path.abspath(__file__))

        ext_dirs = []

        # Source 1: _ext_unpacked/
        ext_root = os.path.join(project_root, "_ext_unpacked")
        if os.path.isdir(ext_root):
            for entry in os.scandir(ext_root):
                if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "manifest.json")):
                    ext_dirs.append(entry.path)

        # Source 2: chrome_extensions/<subdir>/ (pre-unpacked, user-placed)
        chrome_ext_root = os.path.join(project_root, "chrome_extensions")
        if os.path.isdir(chrome_ext_root):
            for entry in os.scandir(chrome_ext_root):
                if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "manifest.json")):
                    if entry.path not in ext_dirs:
                        ext_dirs.append(entry.path)

        return ext_dirs

    def get_extension_load_arg(self, project_root: Optional[str] = None) -> Optional[str]:
        """
        Returns a --load-extension=<dir1>,<dir2>,... CLI arg built from all
        valid unpacked extension directories under _ext_unpacked/ and any
        pre-unpacked subdirectories under chrome_extensions/.

        Inject the returned string into account_chromedriver_args so it reaches
        the physical Chrome process in attachment mode (Chrome v140+).

        Parameters
        ----------
        project_root : str, optional
            Path to the project root.  Defaults to the directory containing
            session_isolation.py.

        Returns
        -------
        str or None
            The --load-extension= arg, or None if no extensions are found.
        """
        valid_dirs = self._collect_all_ext_dirs(project_root)

        if not valid_dirs:
            logger.debug("[Isolation] No valid unpacked extensions found.")
            return None

        arg = "--load-extension=" + ",".join(valid_dirs)
        logger.info(f"[Isolation] Extension load arg built for {len(valid_dirs)} extension(s).")
        return arg

    def get_isolated_session(
        self,
        account_identifier: str,
        load_extensions: bool = False,
        profile_directory: str = "Profile 1",
        project_root: Optional[str] = None,
    ) -> dict:
        """
        Returns a dict with 'port', 'dir', and 'ext_arg' keys.

        Parameters
        ----------
        account_identifier : str
            A unique string (e.g. email) used to name the session directory.
        load_extensions : bool
            When True, seeds the profile Preferences file and returns the
            --load-extension= CLI arg under the 'ext_arg' key.
        profile_directory : str
            Chrome profile sub-directory name (default 'Profile 1').
        project_root : str, optional
            Path to find _ext_unpacked/ and chrome_extensions/.

        Returns
        -------
        dict
            {'port': int, 'dir': str, 'ext_arg': str or None}
        """
        if not profile_directory:
            profile_directory = "Default"

        import hashlib
        safe_id = hashlib.md5(account_identifier.encode("utf-8")).hexdigest()[:12]
        port, data_dir = self.create_session(safe_id)

        if project_root is None:
            project_root = os.path.dirname(os.path.abspath(__file__))

        ext_arg = None
        if load_extensions:
            # 1. Collect ALL available unpacked extension dirs (from both sources)
            ext_dirs = self._collect_all_ext_dirs(project_root)

            # 2. Seed Preferences WITH developer_mode=True AND pre-registered ext dirs
            #    BEFORE Chrome launches — most reliable path for extension loading.
            self.seed_profile_for_extensions(
                data_dir, profile_directory, ext_dirs=ext_dirs if ext_dirs else None
            )

            # 3. Also return the --load-extension= CLI arg as belt-and-suspenders
            if ext_dirs:
                ext_arg = "--load-extension=" + ",".join(ext_dirs)
                logger.info(
                    f"[Isolation] Extension seeding + CLI arg ready for "
                    f"{len(ext_dirs)} extension(s) in session {safe_id}."
                )
            else:
                logger.warning(
                    "[Isolation] load_extensions=True but no unpacked extensions found. "
                    "Place unpacked extension folders in chrome_extensions/<id>/ or "
                    "run with Load Extensions enabled (non-isolated) first to unpack CRX files."
                )

        return {"port": port, "dir": data_dir, "ext_arg": ext_arg}

    def purge_stale_sessions(self, max_age_seconds: int = 3600):
        """
        Scans temp_sessions and removes any session directory older than
        max_age_seconds to prevent orphaned session data from accumulating.
        """
        import time
        if not os.path.exists(self.base_temp_dir):
            return
        now = time.time()
        for entry in os.scandir(self.base_temp_dir):
            try:
                if entry.is_dir():
                    age = now - os.path.getmtime(entry.path)
                    if age > max_age_seconds:
                        shutil.rmtree(entry.path, ignore_errors=True)
                        logger.info(
                            f"[Isolation] Removed stale session: {entry.name} (age: {int(age)}s)"
                        )
            except Exception as e:
                logger.warning(
                    f"[Isolation] Could not inspect session dir {entry.name}: {e}"
                )
