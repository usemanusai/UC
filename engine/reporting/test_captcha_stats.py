import json
import os
import tempfile
import threading
import unittest
from engine.reporting.captcha_stats import CaptchaStatsManager

class TestCaptchaStatsManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.temp_path = self.temp_file.name

        # Reset the singleton instance before each test
        CaptchaStatsManager._instance = None
        self.manager = CaptchaStatsManager(storage_path=self.temp_path)

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

        # Reset the singleton instance after each test
        CaptchaStatsManager._instance = None

    def test_singleton_pattern(self):
        manager1 = CaptchaStatsManager()
        manager2 = CaptchaStatsManager()
        self.assertIs(manager1, manager2)

    def test_record_attempt(self):
        self.manager.record_attempt("capsolver", success=True, duration=1.5)
        self.manager.record_attempt("capsolver", success=False, duration=0.5)

        stats = self.manager.get_stats()
        self.assertIn("capsolver", stats)
        self.assertEqual(stats["capsolver"]["attempts"], 2)
        self.assertEqual(stats["capsolver"]["successes"], 1)
        self.assertEqual(stats["capsolver"]["failures"], 1)
        self.assertEqual(stats["capsolver"]["total_time"], 2.0)

    def test_persistence(self):
        self.manager.record_attempt("2captcha", success=True, duration=2.0)

        # Force re-instantiation to test loading from disk
        CaptchaStatsManager._instance = None
        new_manager = CaptchaStatsManager(storage_path=self.temp_path)

        stats = new_manager.get_stats()
        self.assertIn("2captcha", stats)
        self.assertEqual(stats["2captcha"]["attempts"], 1)
        self.assertEqual(stats["2captcha"]["successes"], 1)

    def test_concurrent_access(self):
        def worker():
            for _ in range(100):
                self.manager.record_attempt("concurrent_service", success=True, duration=0.1)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = self.manager.get_stats()
        self.assertEqual(stats["concurrent_service"]["attempts"], 1000)

if __name__ == "__main__":
    unittest.main()
