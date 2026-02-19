from dataclasses import dataclass
import time


@dataclass
class Ratelimit:
    limit: int
    remaining: int
    reset: int

    def is_reset(self):
        return self.reset < time.time()

    def is_limited(self):
        return not self.is_reset() and self.remaining <= 0

    def remaining_now(self):
        if self.is_reset():
            return self.limit
        return self.remaining
