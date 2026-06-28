import socket
import threading
import time
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Regex to extract host and port from standard proxy strings
_PROXY_EXTRACT_RE = re.compile(
    r'(?:[a-zA-Z0-9+\-.]*://)?'           # optional scheme
    r'(?:[^:@\s]+:[^@\s]+@)?'             # optional user:pass@
    r'([^:/@\s]+)'                        # host (IP or domain)
    r':(\d{2,5})',                        # port
    re.IGNORECASE
)

def check_proxy_health(proxy_str: str, timeout: float = 1.0) -> bool:
    """
    Checks if a proxy is alive by attempting a TCP connection to its host and port.
    Uses socket.connect_ex (similar to tab_monitor.py logic) for fast verification.
    """
    match = _PROXY_EXTRACT_RE.match(proxy_str.strip())
    if not match:
        logger.warning(f"Failed to parse proxy string for health check: {proxy_str}")
        return False

    host, port_str = match.groups()
    port = int(port_str)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.debug(f"Proxy health check exception for {host}:{port} -> {e}")
        return False

class ProxyHealthDaemon(threading.Thread):
    """
    Background daemon that periodically checks the health of proxies loaded into the ProxyRotator.
    If a proxy is unreachable, it reports the failure back to the ProxyRotator.
    """
    def __init__(self, proxy_rotator_cls: Any, check_interval: float = 30.0, timeout: float = 1.0):
        super().__init__(daemon=True, name="ProxyHealthDaemonThread")
        self.proxy_rotator_cls = proxy_rotator_cls
        self.check_interval = check_interval
        self.timeout = timeout
        self._stop_event = threading.Event()

    def run(self) -> None:
        logger.info("ProxyHealthDaemon started.")
        while not self._stop_event.is_set():
            try:
                self._check_all_proxies()
            except Exception as e:
                logger.error(f"ProxyHealthDaemon encountered an error: {e}")

            # Wait for check_interval, but allow quick shutdown
            self._stop_event.wait(self.check_interval)

    def _check_all_proxies(self) -> None:
        # Access proxies safely if possible. We assume proxy_rotator_cls has _proxies list
        # and a report_failure method. We acquire the lock if it's exposed, but to avoid
        # blocking the rotator during network calls, we take a snapshot of the list.

        if not hasattr(self.proxy_rotator_cls, '_proxies'):
            return

        if hasattr(self.proxy_rotator_cls, '_lock'):
            with self.proxy_rotator_cls._lock:
                proxies_snapshot = list(self.proxy_rotator_cls._proxies)
        else:
            proxies_snapshot = list(self.proxy_rotator_cls._proxies)

        for proxy in proxies_snapshot:
            if self._stop_event.is_set():
                break

            if not check_proxy_health(proxy, timeout=self.timeout):
                logger.debug(f"[ProxyHealth] Proxy {proxy} failed health check. Reporting failure.")
                if hasattr(self.proxy_rotator_cls, 'report_failure'):
                    self.proxy_rotator_cls.report_failure(proxy)
            else:
                logger.debug(f"[ProxyHealth] Proxy {proxy} is healthy. Reporting success.")
                if hasattr(self.proxy_rotator_cls, 'report_success'):
                    self.proxy_rotator_cls.report_success(proxy)

    def stop(self) -> None:
        """Signals the daemon to stop."""
        self._stop_event.set()
