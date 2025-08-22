import logging
from collections import deque

from typing_extensions import Callable, Dict, List, Tuple

from program_searcher.exceptions import InvalidProgramSearchArgumentValue
from program_searcher.history_tracker import Step
from program_searcher.mutation_strategy import (
    RemoveStatementMutationStrategy,
    UpdateStatementArgsMutationStrategy,
)
from program_searcher.program_model import Program, Statement
from program_searcher.stop_condition import StopCondition

_DEFAULT_MUTATION_STRATEGIES = {
    UpdateStatementArgsMutationStrategy(): 1 / 2,
    RemoveStatementMutationStrategy(): 1 / 2,
}


class ProgramSearch:
    def __init__(
        self,
        program_name: str,
        program_arg_names: List[str],
        available_functions: Dict[str, int],
        stop_condition: StopCondition,
        evaluate_program_func: Callable[[Program], float],
        min_program_statements: int = 1,
        max_program_statements: int = 10,
        config: dict = None,
    ):
        """
        Initialize ProgramSearch.

        Args:
            program_name (str): Name of the program.
            program_arg_names (List[str]): Names of the program arguments.
            available_functions (Dict[str,int]): Mapping of function name to number of arguments.
            stop_condition (StopCondition): Stop condition for search.
            evaluate_program_func (Callable): Function to evaluate a program.
            min_program_statements (int): Minimum number of statements in programs.
            max_program_statements (int): Maximum number of statements in programs.
            config (dict, optional): Dictionary of optional parameters. Possible keys and their defaults:
                - pop_size (int, default=1000): Population size.
                - tournament_size (int, default=2): Tournament size for selection.
                - replace_arg_for_const_prob (float, default=0.25): Probability to replace argument with a constant.
                - mutation_strategies (Dict[MutationStrategy,float], default=_DEFAULT_MUTATION_STRATEGIES): Mutation strategies with probabilities.
                - restart_steps (int, default=None): Number of steps after which to restart search.
                - warm_start_program (WarmStartProgram, default=None): Program to initialize population with.
                - logger (logging.Logger, default=logging.getLogger(__name__)): Logger for informational and error messages.
                - step_trackers (List[StepsTracker], default=[]): List of step trackers for recording step statistics.
        """
        self.program_name = program_name
        self.program_arg_names = program_arg_names
        self.available_functions = available_functions
        self.stop_condition = stop_condition
        self.evaluate_program_func = evaluate_program_func
        self.min_program_statements = min_program_statements
        self.max_program_statements = max_program_statements

        config = config or {}
        self.pop_size = config.get("pop_size", 1000)
        self.tournament_size = config.get("tournament_size", 2)
        self.replace_arg_for_const_prob = config.get("replace_arg_for_const_prob", 0.25)
        self.mutation_strategies = config.get(
            "mutation_strategies", _DEFAULT_MUTATION_STRATEGIES
        )
        self.restart_steps = config.get("restart_steps")
        self.warm_start_program = config.get("warm_start_program")
        self.logger = config.get("logger") or logging.getLogger(__name__)
        self.step_trackers = config.get("step_trackers", [])

        self.population: deque[Program] = deque()
        self.fitnesess: Dict[Program, float] = {}
        self.error_programs: Dict[Program, bool] = {}
        self.tournament_winner = None
        self.tournament_winner_fitness = None
        self.best_program = None
        self.best_program_fitness = None

        self._validate_arguments()

    def search(self) -> Tuple[Program, float]:
        steps_counter = 1
        self._initialize_population()

        while not self.stop_condition.is_met():
            step = Step(step=self.step)
            step.start()

            self._evaluate_population()
            self._torunament_selection()
            self._mutate_tournament_winner()
            self._update_population()
            self._replace_error_programs()
            self._replace_equivalent_programs()

            self.stop_condition.step()
            step.stop()

            self._on_step_is_done(step)
            steps_counter += 1

    def _initialize_population(self):
        pass

    def _evaluate_population(self):
        pass

    def _mutate_tournament_winner(self):
        pass

    def _torunament_selection(self):
        pass

    def _update_population(self):
        pass

    def _replace_error_programs(self):
        pass

    def _replace_equivalent_programs(self):
        pass

    def _get_program_replacement(self):
        pass

    def _generate_random_program(self):
        pass

    def _generate_random_statement(self, program_vars: str) -> Statement:
        pass

    def _on_step_is_done(self, step: Step):
        pass

    def _init_seeds(self, seed: int):
        pass

    def _validate_arguments(self):
        if self.min_program_statements > self.max_program_statements:
            raise InvalidProgramSearchArgumentValue(
                f"min_program_statements ({self.min_program_statements}) cannot be greater than "
                f"max_program_statements ({self.max_program_statements})."
            )

        if self.pop_size < 0:
            raise InvalidProgramSearchArgumentValue(
                f"pop_size must be non-negative, got {self.pop_size}."
            )

        if self.tournament_size < 0:
            raise InvalidProgramSearchArgumentValue(
                f"tournament_size must be non-negative, got {self.tournament_size}."
            )

        if self.tournament_size > self.pop_size:
            raise InvalidProgramSearchArgumentValue(
                f"tournament_size ({self.tournament_size}) cannot be greater than pop_size ({self.pop_size})."
            )

        if self.replace_arg_for_const_prob < 0 or self.replace_arg_for_const_prob > 1:
            raise InvalidProgramSearchArgumentValue(
                f"replace_arg_for_const_prob must be between 0 and 1, got {self.replace_arg_for_const_prob}."
            )

        if abs(sum(self.mutation_strategies.values()) - 1.0) > 1e-6:
            raise InvalidProgramSearchArgumentValue(
                f"sum of mutation_strategies values must be 1.0, but is {sum(self.mutation_strategies.values())}."
            )

        if any(value < 0 for value in self.mutation_strategies.values()):
            raise InvalidProgramSearchArgumentValue(
                f"all mutation_strategies values must be >= 0. current values: {self.mutation_strategies}."
            )

        if any(value > 1 for value in self.mutation_strategies.values()):
            raise InvalidProgramSearchArgumentValue(
                f"all mutation_strategies values must be <= 1. current values: {self.mutation_strategies}."
            )
