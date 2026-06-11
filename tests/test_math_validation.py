# tests/test_math_validation.py
"""
Mathematical validation test suite for the NTFMC framework.
Asserts correct behavior of Langevin motor control, TDA persistent homology,
Z3 formal verification, Vector Clocks, and structural entropy.
"""

import unittest
import os
import tempfile
import sqlite3
import time
import numpy as np
import site

# Enable user site packages
site.ENABLE_USER_SITE = True
site.main()

# Import mathematical modules
from engine.kernel.math_engine.langevin import (
    generate_fbm,
    compute_bubble_entropy,
    FLEMotorControl
)
from engine.kernel.math_engine.tda import (
    compute_persistence_homology,
    compute_wasserstein_distance,
    mapper_algorithm,
    compute_tmd
)
from engine.kernel.math_engine.verification import (
    Z3ActionVerifier,
    verify_semantic_similarity,
    VerifierInTheLoop
)
from engine.kernel.math_engine.state import (
    VectorClock,
    LockFreeStateDB,
    MG1QueueMonitor
)
from engine.kernel.math_engine.entropy import (
    calculate_cde,
    calculate_aicc,
    StructuralEntropyMonitor
)

class TestLangevinEngine(unittest.TestCase):
    def test_fbm_generation(self):
        # Generate fBm path
        N = 50
        H = 0.5
        path = generate_fbm(N, H, sigma=1.0)
        self.assertEqual(len(path), N)
        self.assertAlmostEqual(path[0], 0.0)

    def test_bubble_entropy(self):
        # A perfectly ordered sequence has bubble entropy 0
        ordered = np.arange(20, dtype=float)
        ben_ordered = compute_bubble_entropy(ordered, m=2)
        self.assertAlmostEqual(ben_ordered, 0.0)
        
        # A chaotic random sequence has higher bubble entropy
        np.random.seed(42)
        random_seq = np.random.rand(30)
        ben_random = compute_bubble_entropy(random_seq, m=2)
        self.assertTrue(ben_random > 0.1)

    def test_fle_motor_control(self):
        motor = FLEMotorControl()
        start = (100.0, 100.0)
        target = (500.0, 400.0)
        path = motor.generate_path(start, target, steps=40, dt=0.03, k_p=5.0, k_d=0.5)
        
        self.assertEqual(len(path), 40)
        self.assertAlmostEqual(path[0][0], 100.0)
        self.assertAlmostEqual(path[0][1], 100.0)
        # Verify it progresses towards the target
        final_dist = np.hypot(path[-1][0] - target[0], path[-1][1] - target[1])
        # Trajectory should have approached the target (initial distance was ~424px, approach within 150px)
        self.assertTrue(final_dist < 150.0)

class TestTDAEngine(unittest.TestCase):
    def test_persistence_homology(self):
        # Create coordinates for a simple triangle (3 points)
        points = np.array([
            [0.0, 0.0],
            [10.0, 0.0],
            [5.0, 8.66]
        ])
        pers = compute_persistence_homology(points)
        # Should have computed persistence diagrams
        self.assertTrue(isinstance(pers, list))

    def test_wasserstein_distance(self):
        diag1 = [(0.1, 0.5), (0.2, 0.8)]
        diag2 = [(0.1, 0.6), (0.2, 0.8)]
        dist = compute_wasserstein_distance(diag1, diag2)
        self.assertTrue(dist >= 0.0)
        # Self distance is 0
        self.assertAlmostEqual(compute_wasserstein_distance(diag1, diag1), 0.0)

    def test_mapper_algorithm(self):
        points = np.random.rand(30, 2)
        graph = mapper_algorithm(points, projection_method="pca", num_intervals=4)
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertTrue(isinstance(graph["nodes"], dict))

    def test_tmd(self):
        # Mock DOM tree dict
        tree = {
            "id": "root",
            "children": [
                {
                    "id": "body",
                    "children": [
                        {"id": "div1", "children": []},
                        {"id": "div2", "children": []}
                    ]
                }
            ]
        }
        barcode = compute_tmd(tree)
        self.assertTrue(len(barcode) > 0)
        # Verify birth and death types
        for birth, death in barcode:
            self.assertTrue(birth >= death)

class TestVerificationEngine(unittest.TestCase):
    def test_z3_action_verifier_sat(self):
        verifier = Z3ActionVerifier()
        # Valid action sequence: click within viewport bounds, timed correctly
        valid_actions = [
            {"type": "click", "x": 100, "y": 150, "width": 50, "height": 30, "timestamp": 1000},
            {"type": "type", "x": 200, "y": 250, "width": 100, "height": 30, "text": "hello", "timestamp": 1200},
            {"type": "submit", "timestamp": 1500}
        ]
        is_valid, msg, _ = verifier.verify_sequence(valid_actions)
        self.assertTrue(is_valid, f"Expected SAT: {msg}")

    def test_z3_action_verifier_unsat_out_of_bounds(self):
        verifier = Z3ActionVerifier()
        # Invalid action sequence: coordinates exceed viewport width (1920)
        invalid_actions = [
            {"type": "click", "x": 2000, "y": 150, "width": 50, "height": 30, "timestamp": 1000}
        ]
        is_valid, msg, _ = verifier.verify_sequence(invalid_actions)
        self.assertFalse(is_valid, "Expected UNSAT for out-of-bounds click")

    def test_z3_action_verifier_unsat_negative_size(self):
        verifier = Z3ActionVerifier()
        # Invalid action sequence: negative width
        invalid_actions = [
            {"type": "type", "x": 100, "y": 150, "width": -10, "height": 30, "text": "test", "timestamp": 1000}
        ]
        is_valid, msg, _ = verifier.verify_sequence(invalid_actions)
        self.assertFalse(is_valid, "Expected UNSAT for negative element size")

    def test_semantic_similarity(self):
        self.assertTrue(verify_semantic_similarity("click submit login button", "btn_submit_login", threshold=0.35))
        self.assertFalse(verify_semantic_similarity("type username", "cancel_button_link", threshold=0.35))

    def test_verifier_in_the_loop(self):
        verifier = Z3ActionVerifier()
        vitl = VerifierInTheLoop(verifier)
        
        # Generator returning invalid sequence on attempt 1, valid sequence on attempt 2
        calls = 0
        def mock_generator(prompt: str):
            nonlocal calls
            calls += 1
            if "VERIFICATION FAILURE" in prompt or calls > 1:
                return [{"type": "click", "x": 100, "y": 150, "width": 50, "height": 30, "timestamp": 1000}]
            else:
                return [{"type": "click", "x": -50, "y": 150, "width": 50, "height": 30, "timestamp": 1000}] # Invalid x=-50
                
        is_valid, actions, msg = vitl.run_verification_loop(mock_generator, "Generate click", max_attempts=3)
        self.assertTrue(is_valid)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["x"], 100)

    def test_z3_unsat_token_limit(self):
        verifier = Z3ActionVerifier()
        # Single input exceeds 256 chars limit
        actions_single_exceeded = [
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 257, "timestamp": 1000}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_single_exceeded)
        self.assertFalse(is_valid, "Expected UNSAT for single input exceeding 256 characters")

        # Total input exceeds 1024 chars limit
        actions_total_exceeded = [
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 200, "timestamp": 1000},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 200, "timestamp": 1200},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 200, "timestamp": 1400},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 200, "timestamp": 1600},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 200, "timestamp": 1800},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "text": "a" * 200, "timestamp": 2000}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_total_exceeded)
        self.assertFalse(is_valid, "Expected UNSAT for total input exceeding 1024 characters")

    def test_z3_unsat_navigation_order(self):
        verifier = Z3ActionVerifier()
        # Password before email/username
        actions_wrong_order = [
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "field": "password", "text": "pw123", "timestamp": 1000},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "field": "email", "text": "user@example.com", "timestamp": 1200}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_wrong_order)
        self.assertFalse(is_valid, "Expected UNSAT when password input occurs before email")

        # Multi-step flow next button order violation (email -> password -> next)
        actions_next_order = [
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "field": "email", "text": "user@example.com", "timestamp": 1000},
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "field": "password", "text": "pw123", "timestamp": 1200},
            {"type": "click", "x": 100, "y": 250, "width": 50, "height": 30, "field": "next", "timestamp": 1400}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_next_order)
        self.assertFalse(is_valid, "Expected UNSAT when next button clicked after password")

    def test_z3_unsat_tag_mismatch(self):
        verifier = Z3ActionVerifier()
        # Cannot type into button tag
        actions_type_button = [
            {"type": "type", "x": 100, "y": 150, "width": 50, "height": 30, "tag": "BUTTON", "text": "test", "timestamp": 1000}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_type_button)
        self.assertFalse(is_valid, "Expected UNSAT when typing is targeted at a BUTTON tag")

        # Cannot click hidden element
        actions_click_hidden = [
            {"type": "click", "x": 100, "y": 150, "width": 50, "height": 30, "tag": "HIDDEN", "timestamp": 1000}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_click_hidden)
        self.assertFalse(is_valid, "Expected UNSAT when clicking a hidden element")

    def test_z3_unsat_consecutive_clicks_cooldown(self):
        verifier = Z3ActionVerifier()
        # Click twice on same coordinates within 200ms (threshold is 300ms)
        actions_too_fast = [
            {"type": "click", "x": 100, "y": 150, "width": 50, "height": 30, "timestamp": 1000},
            {"type": "click", "x": 100, "y": 150, "width": 50, "height": 30, "timestamp": 1200}
        ]
        is_valid, msg, _ = verifier.verify_sequence(actions_too_fast)
        self.assertFalse(is_valid, "Expected UNSAT when consecutive clicks on same coordinates have < 300ms delay")

class TestStateEngine(unittest.TestCase):
    def test_vector_clocks(self):
        v1 = VectorClock("nodeA")
        v2 = VectorClock("nodeB")
        
        v1.increment()
        v2.increment()
        
        # Concurrent clocks
        self.assertEqual(VectorClock.compare(v1.serialize(), v2.serialize()), 'CONCURRENT')
        
        # v1 merges v2 and increments
        v1.update(v2.serialize())
        self.assertEqual(VectorClock.compare(v2.serialize(), v1.serialize()), 'A_BEFORE_B')
        
        v1.increment()
        self.assertEqual(VectorClock.compare(v1.serialize(), v2.serialize()), 'B_BEFORE_A')

    def test_lock_free_db_concurrent_write(self):
        # Create a temp DB file
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            db = LockFreeStateDB(db_path)
            
            # Write key state
            def tx_write(conn):
                conn.execute("INSERT OR REPLACE INTO state_registry (key, value) VALUES ('k1', 'v1')")
                
            db.run_concurrent_write(tx_write)
            
            # Read key state
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM state_registry WHERE key = 'k1'")
            row = cursor.fetchone()
            self.assertEqual(row[0], 'v1')
            conn.close()

    def test_mg1_queue_monitor(self):
        monitor = MG1QueueMonitor()
        # Record dummy arrivals and services
        now = time.time()
        for i in range(10):
            monitor.arrival_times.append(now - (10 - i) * 0.1) # arrival interval 0.1s -> lambda = 10 requests/s
            monitor.service_times.append(0.02) # mean service = 0.02s -> mu = 50 transactions/s
            
        # Rho = 10 / 50 = 0.2 < target_utilization (0.8) -> no throttle
        delay = monitor.calculate_throttle_delay()
        self.assertEqual(delay, 0.0)

class TestEntropyEngine(unittest.TestCase):
    def test_aicc_and_cde(self):
        # Create a temp python file to parse
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
            f.write("""
def add(a, b):
    return a + b

def multiply(x, y):
    val = x * y
    return val
""")
            temp_path = f.name
            
        try:
            aicc = calculate_aicc(temp_path)
            cde = calculate_cde(temp_path)
            
            self.assertTrue(aicc > 0)
            self.assertTrue(cde > 0)
        finally:
            os.remove(temp_path)

    def test_structural_entropy_monitor(self):
        # Scan current math_engine directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        math_engine_dir = os.path.join(base_dir, "engine", "kernel", "math_engine")
        if os.path.exists(math_engine_dir):
            monitor = StructuralEntropyMonitor(math_engine_dir)
            report = monitor.scan_project()
            self.assertTrue(report["files_count"] >= 5)
            self.assertTrue(report["graph_energy"] >= 0.0)
            self.assertTrue(report["laplacian_energy"] >= 0.0)

if __name__ == '__main__':
    unittest.main()
