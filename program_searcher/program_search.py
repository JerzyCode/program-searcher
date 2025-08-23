import logging
import random
from collections import deque

from typing_extensions import Callable, Dict, List, Tuple

from program_searcher.exceptions import InvalidProgramSearchArgumentValue
from program_searcher.history_tracker import Step, StepsTracker
from program_searcher.mutation_strategy import (
    EvolutionOperator,
    MutationStrategy,
    RemoveStatementMutationStrategy,
    TournamentSelectionOperator,
    UpdateStatementArgsMutationStrategy,
)
from program_searcher.program_model import Program, Statement, WarmStartProgram
from program_searcher.stop_condition import StopCondition

_DEFAULT_MUTATION_STRATEGIES = {
    UpdateStatementArgsMutationStrategy(): 1 / 2,
    RemoveStatementMutationStrategy(): 1 / 2,
}

_DEFAULT_EVOLUTION_OPERATOR = TournamentSelectionOperator(tournament_size=2)


class ProgramSearch:
    def __init__(
        self,
        program_name: str,
        program_arg_names: List[str],
        return_program_var_count: int,
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
            return_program_var_count (int): Number of variables that program has to return.
            available_functions (Dict[str,int]): Mapping of function name to number of arguments.
            stop_condition (StopCondition): Stop condition for search.
            evaluate_program_func (Callable): Function to evaluate a program.
            min_program_statements (int): Minimum number of statements in programs.
            max_program_statements (int): Maximum number of statements in programs.
            config (dict, optional): Dictionary of optional parameters. Possible keys and their defaults:
                - pop_size (int, default=1000): Population size.
                - evolution_operator (EvolutionOperator, default=TournamentSelectionOperator): operator that performs operations and update population.
                - mutation_strategies (Dict[MutationStrategy,float], default=_DEFAULT_MUTATION_STRATEGIES): Mutation strategies with probabilities.
                - restart_steps (int, default=None): Number of steps after which to restart search.
                - warm_start_program (WarmStartProgram, default=None): Program to initialize population with.
                - logger (logging.Logger, default=logging.getLogger(__name__)): Logger for informational and error messages.
                - step_trackers (List[StepsTracker], default=[]): List of step trackers for recording step statistics.
                - seed (int, default=None). Seed for random.
        """
        self.program_name = program_name
        self.program_arg_names = program_arg_names
        self.return_program_var_count = return_program_var_count
        self.available_functions = available_functions
        self.stop_condition = stop_condition
        self.evaluate_program_func = evaluate_program_func
        self.min_program_statements = min_program_statements
        self.max_program_statements = max_program_statements

        config = config or {}
        self.pop_size: int = config.get("pop_size", 1000)
        self.evolution_operator: EvolutionOperator = config.get(
            "evolution_operator", _DEFAULT_EVOLUTION_OPERATOR
        )
        self.mutation_strategies: Dict[MutationStrategy, float] = config.get(
            "mutation_strategies", _DEFAULT_MUTATION_STRATEGIES
        )
        self.restart_steps: int = config.get("restart_steps")
        self.warm_start_program: WarmStartProgram = config.get("warm_start_program")
        self.logger: logging.Logger = config.get("logger") or logging.getLogger(
            __name__
        )
        self.step_trackers: List[StepsTracker] = config.get("step_trackers", [])
        self.seed: int = config.get("seed", None)

        self.population: deque[Program] = deque()
        self.fitnesses: Dict[Program, float] = {}
        self.error_programs: Dict[Program, bool] = {}
        self.tournament_winner = None
        self.tournament_winner_fitness = None
        self.best_program = None
        self.best_program_fitness = None

        self._validate_arguments()
        self._init_seeds()

    def search(self) -> Tuple[Program, float]:
        """
        Executes the program search using a genetic programming approach with a pluggable evolution operator.

        The search loop runs until the configured stop condition is met. At each step, it performs the following operations:

            1. Initializes the population if it hasn't been initialized yet.
            2. Evaluates the fitness of all programs in the population.
            3. Applies the configured evolution operator to the population, which may mutate one or more programs in-place.
            4. Replaces programs that caused execution errors.
            5. Replaces equivalent programs to maintain diversity.
            6. Optionally restarts the search at configured intervals (`self.restart_steps`).

        Each step is tracked via a `Step` object, and any registered step trackers are notified through `_on_step_is_done`.

        Returns
        -------
        Tuple[Program, float]
            A tuple containing:
                - The best program found during the search.
                - Its corresponding fitness value.

        Notes
        -----
        - The population is modified in-place; the evolution operator determines whether one or multiple programs are mutated per step.
        - Internal state such as `self.best_program` and `self.best_program_fitness` is updated continuously.
        - Step counters and optional logging/statistics are handled by `Step` objects and step trackers.
        """
        steps_counter = 1
        self._initialize_population()

        while not self.stop_condition.is_met():
            step = Step(step=steps_counter)
            step.start()

            self._evaluate_population()
            self.evolution_operator.apply(
                population=self.population,
                fitnesses=self.fitnesses,
                mutation_strategies=self.mutation_strategies,
            )
            self._replace_error_programs()
            self._replace_equivalent_programs()

            if self.restart_steps and steps_counter % self.restart_steps == 0:
                self._restart()

            self.stop_condition.step()
            step.stop()

            self._on_step_is_done(step)
            steps_counter += 1

        return self.best_program, self.best_program_fitness

    def _initialize_population(self):
        for _ in range(self.pop_size):
            if self.warm_start_program is not None:
                self.population.append(self.warm_start_program.program.copy())
            else:
                random_program = self._generate_random_program()
                self.population.append(random_program)

    def _evaluate_population(self):
        if (
            self.warm_start_program is not None
            and self.warm_start_program.fitness is None
        ):
            warm_start_program_fitness = self.evaluate_program_func(
                self.warm_start_program.program
            )
            self.warm_start_program.fitness = warm_start_program_fitness

        warm_hash = (
            self.warm_start_program.program.to_hash()
            if self.warm_start_program is not None
            else None
        )

        for program in self.population:
            if warm_hash is not None and program.to_hash() == warm_hash:
                self.fitnesses[program] = self.warm_start_program.fitness
            else:
                self.fitnesses[program] = self.evaluate_program_func(program)

    def _replace_error_programs(self):
        for index, program in enumerate(self.population):
            if program.execution_error is not None:
                self.logger.debug(
                    f"Replacing program at index {index} failed execution: {program.execution_error}"
                )
                self.population[index] = self._get_program_replacement()
                continue

    def _replace_equivalent_programs(self):
        seen_program_hashes = set()
        replaced_count = 0

        if self.warm_start_program is not None:
            warm_start_progrma_hash = self.warm_start_program.program.to_hash()

        for index, program in enumerate(self.population):
            program_hash = program.to_hash()
            is_warm_start = (
                self.warm_start_program and program_hash == warm_start_progrma_hash
            )

            if program_hash in seen_program_hashes and not is_warm_start:
                self.logger.debug(
                    f"Replacing program at index {index}. It is equivalent to other one."
                )
                self.population[index] = self._get_program_replacement()
                replaced_count += 1
            else:
                seen_program_hashes.add(program_hash)

        self.logger.debug(f"Replaced {replaced_count} equivalent programs")

    def _get_program_replacement(self):
        if self.warm_start_program is not None:
            return self.warm_start_program.program.copy()

        return self._generate_random_program()

    def _generate_random_program(self):
        num_statements = random.randint(
            self.min_program_statements, self.max_program_statements
        )
        program = Program(
            self.program_name,
            self.program_arg_names,
            return_vars_count=self.return_program_var_count,
        )

        for _ in range(num_statements):
            statement = self._generate_random_statement(program.variables)
            program.insert_statement(statement)

        return program

    def _generate_random_statement(self, program_vars: str) -> Statement:
        func_name = random.choice(list(self.available_functions.keys()))
        allowed_args_size = self.available_functions[func_name]
        args = random.choices(program_vars, k=allowed_args_size)
        return Statement(func=func_name, args=args)

    def _on_step_is_done(self, step: Step):
        pop_best_program, pop_best_fitness = max(
            self.fitnesses.items(), key=lambda x: x[1]
        )

        if self.best_program is None or pop_best_fitness > self.best_program_fitness:
            self.best_program = pop_best_program
            self.best_program_fitness = pop_best_fitness

        num_error_programs = sum(
            pr.execution_error is not None for pr in self.population
        )
        working_programs_percent = 1 - num_error_programs / self.pop_size

        step.insert_stats(
            pop_best_program_fitness=pop_best_fitness,
            pop_best_program_code=pop_best_program.program_str,
            overall_best_fitness=self.best_program_fitness,
            overall_best_program_code=self.best_program.program_str,
            working_programs_percent=working_programs_percent,
        )

        for step_tracker in self.step_trackers:
            step_tracker.track(step)

        self.logger.info(
            f"  Step: {step.step} | Time: {step.duration:.2f}s |  "
            f"Population best program fitness: {pop_best_fitness:.4f} | "
            f"Overall best fitness: {self.best_program_fitness:.4f}"
        )

    def _restart(self):
        self.population.clear()
        self.logger.debug("Population restart")
        self._initialize_population()

    def _init_seeds(self):
        if self.seed is not None:
            random.seed(self.seed)

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
