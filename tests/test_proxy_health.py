import unittest
from unittest.mock import patch, MagicMock
from engine.core.proxy_health import check_proxy_health, ProxyHealthDaemon

class DummyProxyRotator:
    def __init__(self):
        self._proxies = []
        self.failures_reported = []
        self.successes_reported = []

    def report_failure(self, proxy):
        self.failures_reported.append(proxy)

    def report_success(self, proxy):
        self.successes_reported.append(proxy)

class TestProxyHealth(unittest.TestCase):

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_proxy_health_success(self, mock_socket):
        # Setup mock socket to return 0 (success)
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 0
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        result = check_proxy_health("192.168.1.1:8080")
        self.assertTrue(result)
        mock_sock_instance.connect_ex.assert_called_with(("192.168.1.1", 8080))

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_proxy_health_failure(self, mock_socket):
        # Setup mock socket to return error code
        mock_sock_instance = MagicMock()
        mock_sock_instance.connect_ex.return_value = 111
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        result = check_proxy_health("http://user:pass@10.0.0.1:9090")
        self.assertFalse(result)
        mock_sock_instance.connect_ex.assert_called_with(("10.0.0.1", 9090))

    def test_check_proxy_health_invalid_format(self):
        result = check_proxy_health("invalid_proxy_string")
        self.assertFalse(result)

    @patch('engine.core.proxy_health.check_proxy_health')
    def test_daemon_reports_correctly(self, mock_check):
        # First proxy healthy, second proxy unhealthy
        def side_effect(proxy, timeout):
            return proxy == "1.1.1.1:80"
        mock_check.side_effect = side_effect

        rotator = DummyProxyRotator()
        rotator._proxies = ["1.1.1.1:80", "2.2.2.2:80"]

        daemon = ProxyHealthDaemon(proxy_rotator_cls=rotator, check_interval=0.1)
        daemon._check_all_proxies()

        self.assertIn("1.1.1.1:80", rotator.successes_reported)
        self.assertIn("2.2.2.2:80", rotator.failures_reported)

if __name__ == '__main__':
    unittest.main()
