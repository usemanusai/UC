# engine/kernel/math_engine/scheduler.py
"""
Earliest Deadline First (EDF) Scheduler for Validator Pro.
Utilizes a binary min-heap to prioritize background execution of asynchronous tasks,
ensuring high-priority items (like CAPTCHA timeouts, session cookie rotation) run 
before routine logging and rendering.
"""

import heapq
import time
import threading
import logging
from typing import Callable, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class EDFTask:
    """Represents a scheduled task under the EDF paradigm."""
    def __init__(self, deadline: float, name: str, fn: Callable[..., Any], *args, priority: int = 0, **kwargs):
        self.deadline = deadline
        self.name = name
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.priority = priority  # Tie-breaker (lower number runs first if deadlines are equal)
        self.created_at = time.time()

    def __lt__(self, other: 'EDFTask') -> bool:
        # Heap comparison: sort by deadline first, then by priority, then by creation time
        if self.deadline != other.deadline:
            return self.deadline < other.deadline
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at

class EDFScheduler:
    """
    Thread-safe Earliest Deadline First (EDF) scheduler.
    """
    def __init__(self):
        self._heap = []
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._running = False
        self._thread = None

    def schedule(self, relative_deadline: float, name: str, fn: Callable[..., Any], *args, priority: int = 0, **kwargs) -> EDFTask:
        """
        Schedules a task to run before target deadline (current time + relative_deadline).
        """
        deadline = time.time() + relative_deadline
        task = EDFTask(deadline, name, fn, *args, priority=priority, **kwargs)
        with self._lock:
            heapq.heappush(self._heap, task)
            logger.debug(f"[EDFScheduler] Scheduled task '{name}' with deadline in {relative_deadline:.2f}s")
            self._cond.notify_all()
        return task

    def start(self):
        """Starts the background worker thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._worker_loop, name="EDFSchedulerWorker", daemon=True)
            self._thread.start()
            logger.info("[EDFScheduler] Background worker thread started.")

    def stop(self):
        """Stops the scheduler and waits for the worker thread to exit."""
        with self._lock:
            self._running = False
            self._cond.notify_all()
        if self._thread:
            self._thread.join(timeout=2.0)
            logger.info("[EDFScheduler] Background worker thread stopped.")

    def _worker_loop(self):
        while True:
            task = None
            with self._lock:
                while self._running and not self._heap:
                    self._cond.wait()
                
                if not self._running:
                    break
                    
                # Look at the earliest deadline task
                now = time.time()
                next_task = self._heap[0]
                
                if now >= next_task.deadline:
                    task = heapq.heappop(self._heap)
                else:
                    # Wait until deadline or new task arrival
                    wait_time = next_task.deadline - now
                    self._cond.wait(timeout=wait_time)
                    
                    # Recheck queue
                    if self._heap:
                        next_task = self._heap[0]
                        if time.time() >= next_task.deadline:
                            task = heapq.heappop(self._heap)
            
            if task:
                try:
                    logger.debug(f"[EDFScheduler] Executing task '{task.name}' (deadline delta: {task.deadline - time.time():.2f}s)")
                    task.fn(*task.args, **task.kwargs)
                except Exception as e:
                    logger.error(f"[EDFScheduler] Error executing task '{task.name}': {e}", exc_info=True)
