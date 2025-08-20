from abc import ABC, abstractmethod
from datetime import datetime

from typing_extensions import override


class StopCondition(ABC):
    @abstractmethod
    def is_met(self):
        pass

    @abstractmethod
    def step(self):
        pass


class MaxStepsStopCondition(StopCondition, ABC):
    def __init__(self, max_steps: int = 1000):
        super().__init__()
        self.max_steps = max_steps
        self.steps = 0

    @override
    def is_met(self):
        return self.steps >= self.max_steps

    @override
    def step(self):
        self.steps += 1


class DateStopCondition(StopCondition):
    def __init__(self, end_time: datetime):
        self.end_time = end_time

    @override
    def is_met(self):
        return datetime.now() >= self.end_time

    @override
    def step(self):
        pass
