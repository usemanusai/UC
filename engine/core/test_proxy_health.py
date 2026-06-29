import unittest
from unittest.mock import MagicMock, patch
import threading
from engine.core.proxy_health import ProxyHealthDaemon

class MockProxyRotator:
    def __init__(self):
        self._lock = threading.Lock()
        self._proxies = []

    def load(self, proxies):
        self._proxies = proxies

    def report_success(self, proxy_str):
        pass

    def report_failure(self, proxy_str):
        pass


class TestProxyHealthDaemon(unittest.TestCase):
    def setUp(self):
        self.mock_rotator = MockProxyRotator()
        self.mock_rotator.report_success = MagicMock()
        self.mock_rotator.report_failure = MagicMock()
        self.daemon = ProxyHealthDaemon(
            proxy_rotator_cls=self.mock_rotator,
            check_interval=1,
            timeout=1
        )

    def test_parse_proxy(self):
        tests = [
            ("http://192.168.1.1:8080", "192.168.1.1", 8080),
            ("https://user:pass@10.0.0.1:3128", "10.0.0.1", 3128),
            ("socks5://user:pass@example.com:1080", "example.com", 1080),
            ("127.0.0.1:9050", "127.0.0.1", 9050),
        ]

        for proxy_str, expected_host, expected_port in tests:
            host, port = self.daemon._parse_proxy(proxy_str)
            self.assertEqual(host, expected_host)
            self.assertEqual(port, expected_port)

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_tcp_success(self, mock_socket):
        # Mock connect_ex to return 0 (success)
        mock_instance = mock_socket.return_value.__enter__.return_value
        mock_instance.connect_ex.return_value = 0

        result = self.daemon._check_tcp("127.0.0.1", 8080)
        self.assertTrue(result)
        mock_instance.connect_ex.assert_called_with(("127.0.0.1", 8080))

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_tcp_failure(self, mock_socket):
        # Mock connect_ex to return non-zero (failure)
        mock_instance = mock_socket.return_value.__enter__.return_value
        mock_instance.connect_ex.return_value = 111  # Connection refused

        result = self.daemon._check_tcp("127.0.0.1", 8080)
        self.assertFalse(result)

    @patch.object(ProxyHealthDaemon, '_check_tcp')
    def test_check_proxies_reports(self, mock_check_tcp):
        # Setup proxies
        self.mock_rotator.load([
            "http://1.1.1.1:80",
            "https://2.2.2.2:443"
        ])

        # mock_check_tcp returns True for first proxy, False for second
        mock_check_tcp.side_effect = [True, False]

        self.daemon._check_proxies()

        self.mock_rotator.report_success.assert_called_once_with("http://1.1.1.1:80")
        self.mock_rotator.report_failure.assert_called_once_with("https://2.2.2.2:443")

    def test_stop_event(self):
        self.assertFalse(self.daemon._stop_event.is_set())
        self.daemon.stop()
        self.assertTrue(self.daemon._stop_event.is_set())

if __name__ == '__main__':
    unittest.main()
