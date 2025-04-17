from collections import defaultdict, deque
from time import time
from typing import Deque, Dict

class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: Dict[str, Deque[float]] = defaultdict(deque)

    def is_limited(self, identifier: str) -> bool:
        """
        Checks if the identifier has exceeded the maximum number of attempts within the time window.
        If the limit is exceeded, it returns True, otherwise it returns False.
        """
        now = time()
        queue = self.attempts[identifier]

        # Remove timestamps that are outside the time window
        while queue and queue[0] < now - self.window_seconds:
            queue.popleft()

        if len(queue) >= self.max_attempts:
            return True

        queue.append(now)
        return False

    def reset(self, identifier: str):
        """
        Resets the attempts for the given identifier.
        This is useful for clearing the attempts after a successful action or when the identifier is no longer relevant.
        """
        if identifier in self.attempts:
            del self.attempts[identifier]
