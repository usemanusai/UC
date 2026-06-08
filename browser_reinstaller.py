import os
import shutil
import logging
import winreg
import uuid
import subprocess
import platform
from typing import Optional

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
    Hard Isolation Engine: Purges all traces of previous browser activity
    and rotates system identifiers (HWID).
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
    def rotate_hwid() -> bool:
        """
        Rotates the Windows MachineGuid to simulate a fresh OS environment.
        REQUIRES ADMIN PRIVILEGES.
        """
        if platform.system() != 'Windows':
            return False

        try:
            new_guid = str(uuid.uuid4())
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography', 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, 'MachineGuid', 0, winreg.REG_SZ, new_guid)
            winreg.CloseKey(key)

            new_digital_id = os.urandom(164)
            key2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion', 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key2, 'DigitalProductId', 0, winreg.REG_BINARY, new_digital_id)
            winreg.CloseKey(key2)

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
        Wipes all state subdirectories that persist fingerprint data:
        Cache, Code Cache, GPUCache, Network, Sessions, IndexedDB, Local Storage,
        Session Storage, Cookies, Visited Links, History, Web Data, Origin Bound Certs.
        Returns True on success, False on failure.
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
