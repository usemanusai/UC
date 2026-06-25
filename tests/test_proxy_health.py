import unittest
from unittest.mock import patch, MagicMock
from engine.core.proxy_health import ProxyHealthChecker
import socket

class TestProxyHealthChecker(unittest.TestCase):
    def setUp(self):
        self.mock_proxy_rotator = MagicMock()
        self.mock_proxy_rotator.is_loaded.return_value = True
        self.mock_proxy_rotator._proxies = [
            "192.168.1.1:8080",
            "user:pass@10.0.0.1:3128",
            "http://proxy.example.com:80",
            "socks5://user:pass@127.0.0.1:9050"
        ]
        self.mock_proxy_rotator._lock = MagicMock()
        self.checker = ProxyHealthChecker(self.mock_proxy_rotator, check_interval=1)

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_proxies_all_healthy(self, mock_socket_cls):
        mock_socket_instance = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket_instance
        mock_socket_instance.connect_ex.return_value = 0 # Success

        self.checker._check_proxies()

        # Should call report_success for all proxies
        self.assertEqual(self.mock_proxy_rotator.report_success.call_count, 4)
        self.assertEqual(self.mock_proxy_rotator.report_failure.call_count, 0)

        # Verify connect_ex was called with correct host/port pairs
        from unittest.mock import call
        calls = [
            call(('192.168.1.1', 8080)),
            call(('10.0.0.1', 3128)),
            call(('proxy.example.com', 80)),
            call(('127.0.0.1', 9050))
        ]
        mock_socket_instance.connect_ex.assert_has_calls(calls, any_order=True)

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_proxies_mixed_health(self, mock_socket_cls):
        mock_socket_instance = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket_instance

        # Make the second proxy fail
        def connect_ex_side_effect(addr):
            if addr == ('10.0.0.1', 3128):
                return 111 # Connection refused
            return 0 # Success

        mock_socket_instance.connect_ex.side_effect = connect_ex_side_effect

        self.checker._check_proxies()

        self.assertEqual(self.mock_proxy_rotator.report_success.call_count, 3)
        self.assertEqual(self.mock_proxy_rotator.report_failure.call_count, 1)
        self.mock_proxy_rotator.report_failure.assert_called_with("user:pass@10.0.0.1:3128")

    @patch('engine.core.proxy_health.socket.socket')
    def test_check_proxies_gaierror(self, mock_socket_cls):
        mock_socket_instance = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket_instance

        # Simulate DNS resolution failure
        def connect_ex_side_effect(addr):
            raise socket.gaierror("Name or service not known")

        mock_socket_instance.connect_ex.side_effect = connect_ex_side_effect

        self.checker._check_proxies()

        self.assertEqual(self.mock_proxy_rotator.report_success.call_count, 0)
        self.assertEqual(self.mock_proxy_rotator.report_failure.call_count, 4)

    def test_check_proxies_invalid_format(self):
        self.mock_proxy_rotator._proxies = ["invalid_proxy_format"]
        self.checker._check_proxies()

        # Should skip invalid formats
        self.assertEqual(self.mock_proxy_rotator.report_success.call_count, 0)
        self.assertEqual(self.mock_proxy_rotator.report_failure.call_count, 0)

    def test_stop_event(self):
        self.checker.stop()
        self.assertTrue(self.checker._stop_event.is_set())

if __name__ == '__main__':
    unittest.main()
