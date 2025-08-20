import csv
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import override


class Step:
    def __init__(self, step: int):
        self.step = step
        self.start_time = None
        self.end_time = None
        self.pop_best_program_fitness = None
        self.pop_best_program_code = None
        self.working_programs_percent = None
        self.overall_best_fitness = None
        self.overall_best_program_code = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time

    def insert_stats(
        self,
        pop_best_program_fitness: float,
        pop_best_program_code: str,
        working_programs_percent: float,
        overall_best_fitness: float,
        overall_best_program_code: str = None,
    ):
        self.pop_best_program_fitness = pop_best_program_fitness
        self.pop_best_program_code = pop_best_program_code
        self.working_programs_percent = working_programs_percent
        self.overall_best_fitness = overall_best_fitness
        self.overall_best_program_code = overall_best_program_code

    def to_row(self):
        return [
            self.step,
            self.duration,
            self.pop_best_program_fitness,
            self.working_programs_percent,
            self.overall_best_fitness,
            self.pop_best_program_code,
            self.overall_best_program_code,
        ]


class StepsTracker(ABC):
    @abstractmethod
    def track(self, step: Step):
        pass


class CsvStepsTracker(StepsTracker):
    def __init__(self, file_dir, save_batch_size: int):
        super().__init__()
        self.save_batch_size = save_batch_size
        self.steps = []

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"program_search_{date_str}.csv"
        self.file_path = os.path.join(file_dir, filename)

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        self.columns = [
            "step",
            "duration",
            "pop_best_program_fitness",
            "working_programs_percent",
            "overall_best_fitness",
            "pop_best_program_code",
            "overall_best_program_code",
        ]

        if not os.path.exists(self.file_path):
            with open(self.file_path, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)

    @override
    def track(self, step: Step):
        self.steps.append(step)

        if len(self.steps) >= self.save_batch_size:
            self.append_to_csv()
            self.steps.clear()

    def append_to_csv(self):
        if not self.steps:
            return

        with open(self.file_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            for s in self.steps:
                writer.writerow(s.to_row())
