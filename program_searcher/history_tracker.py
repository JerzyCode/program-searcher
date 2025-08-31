import csv
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime

from typing_extensions import override

from program_searcher.program_model import Program


class Step:
    """
    Helper class for tracking the execution of a single step and storing associated statistics.

    This class serves as a container for various metrics collected during a step of a process,
    such as execution duration, best program fitness, best program code, percentage of working programs,
    and overall best fitness/code. It can be used with a StepsTracker to collect and persist
    step-by-step statistics.

    Attributes:
        step (int): The index or number of the current step.
        start_time (float | None): Timestamp when the step started.
        end_time (float | None): Timestamp when the step ended.
        duration (float | None): Duration of the step (end_time - start_time).
        pop_best_program_fitness (float | None): Best fitness in the current population.
        pop_best_program_code (str | None): Code of the best program in the current population.
        working_programs_percent (float | None): Percentage of programs that executed successfully.
        overall_best_fitness (float | None): Best fitness observed overall (up to this step).
        overall_best_program_code (str | None): Code of the overall best program.

    Methods:
        start(): Records the start time of the step.
        stop(): Records the end time and computes the duration.
        insert_stats(...): Inserts statistics collected during the step.
        to_row(): Returns the step data as a list, suitable for logging or tabular storage.
    """

    def __init__(self, step: int):
        self.step = step
        self.start_time = None
        self.end_time = None
        self.pop_best_program_fitness = None
        self.pop_best_program = None
        self.working_programs_percent = None
        self.overall_best_fitness = None
        self.overall_best_program = None
        self.duration = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time

    def insert_stats(
        self,
        pop_best_program_fitness: float,
        pop_best_program: Program,
        working_programs_percent: float,
        overall_best_fitness: float,
        overall_best_program: Program = None,
    ):
        self.pop_best_program_fitness = pop_best_program_fitness
        self.pop_best_program = pop_best_program
        self.working_programs_percent = working_programs_percent
        self.overall_best_fitness = overall_best_fitness
        self.overall_best_program = overall_best_program


class StepsTracker(ABC):
    """
    Abstract base class for tracking steps of a process.

    Subclasses should implement the `track` method to handle storage, logging,
    or processing of Step instances.
    """

    @abstractmethod
    def track(self, step: Step):
        """
        Track a single Step instance.

        Args:
            step (Step): The step object containing statistics and timing information.
        """
        pass


class CsvStepsTracker(StepsTracker):
    """
    Tracks steps and saves them to a CSV file in batches.

    This tracker collects Step instances and writes them to a CSV file once
    the number of collected steps reaches `save_batch_size`. The CSV includes
    step index, duration, population best fitness, working programs percentage,
    overall best fitness, and program codes.

    Attributes:
        file_path (str): Path to the CSV file where steps are saved.
        save_batch_size (int): Number of steps to collect before saving to CSV.
        steps (List[Step]): Temporary storage of collected Step instances.
        columns (List[str]): CSV column headers.
    """

    def __init__(self, file_dir, save_batch_size: int):
        """
        Initialize a CsvStepsTracker.

        Args:
            file_dir (str): Directory where the CSV file will be created.
            save_batch_size (int): Number of steps to accumulate before saving.
        """
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
        """
        Add a Step to the tracker and save to CSV if batch size is reached.

        Args:
            step (Step): The Step instance to track.
        """
        self.steps.append(step)

        if len(self.steps) >= self.save_batch_size:
            self._append_to_csv()
            self.steps.clear()

    def _append_to_csv(self):
        if not self.steps:
            return

        with open(self.file_path, mode="a", newline="") as f:
            writer = csv.writer(f)
            for s in self.steps:
                writer.writerow(self.to_row(s))

    def to_row(self, step: Step):
        return [
            step.step,
            step.duration,
            step.pop_best_program_fitness,
            step.working_programs_percent,
            step.overall_best_fitness,
            step.pop_best_program.program_str,
            step.overall_best_program.program_str,
        ]
