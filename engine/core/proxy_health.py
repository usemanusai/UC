import threading
import logging
import socket
import time
from typing import Any

logger = logging.getLogger(__name__)

class ProxyHealthDaemon(threading.Thread):
    """
    A background daemon thread that actively checks the TCP health of proxies
    loaded in the given proxy_rotator_cls using socket.connect_ex.
    """
    def __init__(
        self,
        proxy_rotator_cls: Any,
        check_interval: int = 30,
        timeout: int = 2
    ):
        super().__init__(daemon=True, name="ProxyHealthDaemonThread")
        self.proxy_rotator_cls = proxy_rotator_cls
        self.check_interval = check_interval
        self.timeout = timeout
        self._stop_event = threading.Event()

    def run(self) -> None:
        logger.info(f"ProxyHealthDaemon started. Checking proxies every {self.check_interval}s with {self.timeout}s timeout.")
        while not self._stop_event.is_set():
            try:
                self._check_proxies()
            except Exception as e:
                logger.error(f"ProxyHealthDaemon failed during health check: {e}")

            # Wait for check_interval, allowing quick shutdown
            self._stop_event.wait(self.check_interval)

    def _check_proxies(self) -> None:
        import concurrent.futures

        # Get a snapshot of loaded proxies
        with self.proxy_rotator_cls._lock:
            proxies = list(self.proxy_rotator_cls._proxies)

        def check_and_report(proxy_str):
            if self._stop_event.is_set():
                return
            host, port = self._parse_proxy(proxy_str)
            if not host or not port:
                return
            is_healthy = self._check_tcp(host, port)
            if is_healthy:
                self.proxy_rotator_cls.report_success(proxy_str)
            else:
                self.proxy_rotator_cls.report_failure(proxy_str)

        # Execute checks concurrently using a ThreadPoolExecutor
        max_workers = min(32, len(proxies) + 1) if proxies else 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(check_and_report, p) for p in proxies]
            for future in concurrent.futures.as_completed(futures):
                if self._stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

    def _parse_proxy(self, proxy_str: str) -> tuple[str, int]:
        """
        Extracts host and port from a proxy string.
        Handles format: [scheme://][user:pass@]host:port
        """
        try:
            clean_str = proxy_str.strip()
            if '://' in clean_str:
                clean_str = clean_str.split('://', 1)[1]
            if '@' in clean_str:
                clean_str = clean_str.split('@', 1)[1]

            host, port_str = clean_str.rsplit(':', 1)
            return host, int(port_str)
        except Exception:
            return "", 0

    def _check_tcp(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            try:
                return s.connect_ex((host, port)) == 0
            except Exception:
                return False

    def stop(self) -> None:
        """Signals the daemon thread to stop."""
        self._stop_event.set()
