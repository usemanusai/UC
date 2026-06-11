# browser_reinstaller.py
import os
import shutil
import logging
import winreg
import uuid
import subprocess
import platform
import sqlite3
import json
import time
from typing import Optional, Dict

# Import Vector Clock and lock-free DB helpers
from engine.kernel.math_engine.state import LockFreeStateDB, VectorClock

logger = logging.getLogger(__name__)

# Fallback functions if browser_factory cannot be imported
try:
    from engine.kernel.browser_factory import _kill_all_chrome_processes, purge_stale_chromedriver
except ImportError:
    def _kill_all_chrome_processes():
        pass
    def purge_stale_chromedriver():
        pass

class BrowserReinstaller:
    """
    Hard Isolation Engine: Purges all traces of previous browser activity,
    and rotates system identifiers (HWID) synchronized via logical Vector Clocks.
    """

    @staticmethod
    def full_purge():
        """
        Kills all browser processes and purges all cached/local data.
        """
        logger.info('[Reinstaller] Initiating Hard Purge...')
        _kill_all_chrome_processes()
        purge_stale_chromedriver()

        appdata = os.environ.get('LOCALAPPDATA')
        if appdata:
            chrome_data = os.path.join(appdata, 'Google', 'Chrome', 'User Data')
            if os.path.exists(chrome_data):
                try:
                    shutil.rmtree(chrome_data, ignore_errors=True)
                    logger.info(f'[Reinstaller] Purged Chrome User Data: {chrome_data}')
                except Exception as e:
                    logger.error(f'[Reinstaller] Failed to purge Chrome data: {e}')

    @staticmethod
    def rotate_hwid(node_id: Optional[str] = None) -> bool:
        """
        Rotates the Windows MachineGuid to simulate a fresh OS environment.
        Uses Vector Clocks to prevent redundant/concurrent writes across processes.
        REQUIRES ADMIN PRIVILEGES.
        """
        if platform.system() != 'Windows':
            return False

        if not node_id:
            node_id = f"node_{platform.node()}_{os.getpid()}"

        db_dir = os.path.abspath("temp_sessions")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "sessions_registry.db")
        state_db = LockFreeStateDB(db_path)

        # 1. Fetch current global HWID clock state
        def check_hwid_tx(conn: sqlite3.Connection) -> Tuple[Optional[str], Optional[str]]:
            cursor = conn.cursor()
            cursor.execute("SELECT value, clock_json FROM state_registry WHERE key = 'global_hwid'")
            return cursor.fetchone()

        row = state_db.run_concurrent_write(check_hwid_tx)
        
        # Parse clock
        if row:
            db_guid, clock_json = row
            db_clock = json.loads(clock_json)
        else:
            db_guid = None
            db_clock = {}

        # Initialize local vector clock representing our knowledge
        local_clock = VectorClock(node_id)
        local_clock.update(db_clock)
        
        # Compare clocks: if another process has already updated it (we are behind),
        # we pull the existing GUID from the DB and skip the physical write!
        comparison = VectorClock.compare(local_clock.serialize(), db_clock)
        if comparison == 'B_BEFORE_A' or comparison == 'EQUAL':
            # We are up-to-date or ahead in causal history, we can perform the rotation!
            pass
        else:
            # Another node already rotated the HWID, sync to that GUID and skip writing registry
            logger.info(f"[Reinstaller] HWID already rotated by another node in causal logical time (GUID: {db_guid}). Skipping registry write.")
            return True

        try:
            new_guid = str(uuid.uuid4())
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography', 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, 'MachineGuid', 0, winreg.REG_SZ, new_guid)
            winreg.CloseKey(key)

            new_digital_id = os.urandom(164)
            key2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion', 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key2, 'DigitalProductId', 0, winreg.REG_BINARY, new_digital_id)
            winreg.CloseKey(key2)

            # 2. Write the new GUID and increment the causal clock in the database
            local_clock.increment()
            
            def update_hwid_tx(conn: sqlite3.Connection):
                conn.execute("""
                    INSERT OR REPLACE INTO state_registry (key, value, clock_json, last_node, updated_at)
                    VALUES ('global_hwid', ?, ?, ?, ?)
                """, (new_guid, json.dumps(local_clock.serialize()), node_id, time.time()))

            state_db.run_concurrent_write(update_hwid_tx)
            logger.info(f'[Reinstaller] HWID (MachineGuid + DigitalProductId) Rotated successfully: {new_guid}')
            return True
        except PermissionError:
            logger.warning('[Reinstaller] Permission denied rotating HWID. Run as Admin if required.')
            return False
        except Exception as e:
            logger.error(f'[Reinstaller] HWID rotation failed: {e}')
            return False

    @staticmethod
    def reinstall_portable_chrome(target_dir: str) -> bool:
        """
        Prepares a fully clean isolated Chrome user-data directory.
        Wipes all state subdirectories that persist fingerprint data.
        """
        FINGERPRINT_STATE_DIRS = [
            'Cache', 'Code Cache', 'GPUCache', 'Network', 'Sessions', 'IndexedDB',
            'Local Storage', 'Session Storage', 'databases', 'FileSystem', 'QuotaManager',
            'Extension State', 'Service Worker', 'blob_storage'
        ]
        FINGERPRINT_STATE_FILES = [
            'Cookies', 'Cookies-journal', 'Visited Links', 'History', 'History-journal',
            'Web Data', 'Web Data-journal', 'Origin Bound Certs', 'Network Action Predictor',
            'QuotaManager', 'TransportSecurity'
        ]

        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                logger.info(f'[Reinstaller] Created fresh sandbox dir: {target_dir}')
                return True

            for root_path, dirs, files in os.walk(target_dir):
                for d in list(dirs):
                    if d in FINGERPRINT_STATE_DIRS:
                        full_path = os.path.join(root_path, d)
                        try:
                            shutil.rmtree(full_path, ignore_errors=True)
                            logger.info(f'[Reinstaller] Wiped state dir: {full_path}')
                        except PermissionError as pe:
                            logger.warning(f'[Reinstaller] Permission denied wiping {full_path}: {pe}')
                        except Exception as e:
                            logger.error(f'[Reinstaller] Failed to wipe {full_path}: {e}')

                for fname in files:
                    if fname in FINGERPRINT_STATE_FILES:
                        full_path = os.path.join(root_path, fname)
                        try:
                            os.remove(full_path)
                            logger.info(f'[Reinstaller] Removed fingerprint file: {full_path}')
                        except PermissionError as pe:
                            logger.warning(f'[Reinstaller] Permission denied removing {full_path}: {pe}')
                        except Exception as e:
                            logger.error(f'[Reinstaller] Failed to remove {full_path}: {e}')

            logger.info(f'[Reinstaller] Portable Chrome sandbox fully prepared at: {target_dir}')
            return True
        except Exception as e:
            logger.error(f'[Reinstaller] reinstall_portable_chrome critically failed: {e}')
            return False

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    BrowserReinstaller.full_purge()
    BrowserReinstaller.rotate_hwid()
