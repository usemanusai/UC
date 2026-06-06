import unittest
from unittest.mock import patch, MagicMock

from engine.core.discovery_bridge import _fetch_page_html

class TestDiscoveryBridge(unittest.TestCase):
    @patch('requests.get')
    def test_fetch_page_html_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Hello World</h1></body></html>"
        mock_get.return_value = mock_response

        mock_log_callback = MagicMock()

        result = _fetch_page_html("http://example.com", mock_log_callback)

        self.assertEqual(result, "<html><body><h1>Hello World</h1></body></html>")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "http://example.com")
        self.assertIn("headers", kwargs)
        self.assertEqual(kwargs["timeout"], 30)
        self.assertTrue(kwargs["allow_redirects"])

        mock_response.raise_for_status.assert_called_once()

        # Verify log_callback was called at least twice (fetching and fetched)
        self.assertTrue(mock_log_callback.call_count >= 2)
        mock_log_callback.assert_any_call("[Bridge] Fetching page HTML...")
        mock_log_callback.assert_any_call(f"[Bridge] Fetched {len(mock_response.text)} chars of HTML (status 200).")

    @patch('requests.get')
    def test_fetch_page_html_error(self, mock_get):
        mock_get.side_effect = Exception("Mocked connection error")
        mock_log_callback = MagicMock()

        result = _fetch_page_html("http://example.com", mock_log_callback)

        self.assertEqual(result, "")
        mock_log_callback.assert_called_with("[Bridge] HTML fetch failed: Mocked connection error. AI will work from URL context only.")

if __name__ == '__main__':
    unittest.main()
