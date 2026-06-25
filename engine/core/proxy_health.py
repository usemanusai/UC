import threading
import time
import socket
import logging

logger = logging.getLogger(__name__)

class ProxyHealthChecker(threading.Thread):
    """
    Automated Proxy Health Checker
    Runs in the background to periodically check the health of loaded proxies
    in the ProxyRotator via fast socket connections.
    """
    def __init__(self, proxy_rotator_cls, check_interval: int = 60, timeout: float = 2.0):
        super().__init__(daemon=True, name="ProxyHealthCheckerThread")
        self.proxy_rotator_cls = proxy_rotator_cls
        self.check_interval = check_interval
        self.timeout = timeout
        self._stop_event = threading.Event()

    def run(self):
        logger.info(f"ProxyHealthChecker started. Checking proxies every {self.check_interval}s.")
        while not self._stop_event.is_set():
            try:
                self._check_proxies()
            except Exception as e:
                logger.error(f"ProxyHealthChecker encountered an error: {e}")

            self._stop_event.wait(self.check_interval)

    def _check_proxies(self):
        if not self.proxy_rotator_cls.is_loaded():
            return

        with self.proxy_rotator_cls._lock:
            proxies_to_check = list(self.proxy_rotator_cls._proxies)

        import concurrent.futures

        def check_single_proxy(proxy_raw):
            if self._stop_event.is_set():
                return

            clean_proxy = proxy_raw.strip()
            if '://' in clean_proxy:
                clean_proxy = clean_proxy.split('://', 1)[1]
            if '@' in clean_proxy:
                clean_proxy = clean_proxy.split('@', 1)[1]

            parts = clean_proxy.split(':')
            if len(parts) >= 2:
                if len(parts) == 4:
                    host, port_str = parts[0], parts[1]
                else:
                    host, port_str = parts[0], parts[1]
            else:
                logger.warning(f"ProxyHealthChecker: Invalid proxy format: {proxy_raw}")
                return

            try:
                port = int(port_str)
            except ValueError:
                logger.warning(f"ProxyHealthChecker: Invalid port format: {proxy_raw}")
                return

            is_healthy = self._check_port_open(host, port)

            if is_healthy:
                self.proxy_rotator_cls.report_success(proxy_raw)
            else:
                self.proxy_rotator_cls.report_failure(proxy_raw)

        max_workers = min(32, max(1, len(proxies_to_check)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(check_single_proxy, p) for p in proxies_to_check]
            for future in concurrent.futures.as_completed(futures):
                if self._stop_event.is_set():
                    break

    def _check_port_open(self, host: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                return s.connect_ex((host, port)) == 0
        except socket.gaierror:
            # Could not resolve hostname
            return False
        except Exception:
            return False

    def stop(self):
        """Signals the daemon to stop."""
        self._stop_event.set()
