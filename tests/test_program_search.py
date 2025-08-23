import logging
import os
import random
import sys
import tempfile
import unittest

from program_searcher.exceptions import InvalidProgramSearchArgumentValue
from program_searcher.history_tracker import CsvStepsTracker
from program_searcher.mutation_strategy import (
    RemoveStatementMutationStrategy,
    ReplaceStatementMutationStrategy,
    TournamentSelectionOperator,
    UpdateStatementArgsMutationStrategy,
)
from program_searcher.program_model import Program, Statement, WarmStartProgram
from program_searcher.program_search import ProgramSearch
from program_searcher.stop_condition import MaxStepsStopCondition


class TestProgramSearchValidation(unittest.TestCase):
    def setUp(self):
        self.correct_args = {
            "program_name": "test_program",
            "program_arg_names": ["x"],
            "return_program_var_count": 1,
            "available_functions": {"add": 2},
            "min_program_statements": 1,
            "max_program_statements": 5,
            "stop_condition": MockStopCondition(),
            "evaluate_program_func": lambda p: 0.0,
            "config": {
                "pop_size": 10,
                "mutation_strategies": {
                    RemoveStatementMutationStrategy: 0.3,
                    ReplaceStatementMutationStrategy: 0.3,
                    UpdateStatementArgsMutationStrategy: 0.4,
                },
                "logger": logging.getLogger("test_logger"),
            },
        }

    def test_min_greater_than_max(self):
        args = self.correct_args.copy()
        args["min_program_statements"] = 6
        args["max_program_statements"] = 5
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_negative_pop_size(self):
        args = self.correct_args.copy()
        args["config"]["pop_size"] = -1
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_invalid_mutation_strategies_sum(self):
        args = self.correct_args.copy()
        args["config"]["mutation_strategies"] = {
            ReplaceStatementMutationStrategy: 0.5,
            RemoveStatementMutationStrategy: 0.5,
            UpdateStatementArgsMutationStrategy: 0.5,
        }
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_mutation_strategies_negative_value(self):
        args = self.correct_args.copy()
        args["config"]["mutation_strategies"] = {
            RemoveStatementMutationStrategy: -0.1,
            ReplaceStatementMutationStrategy: 0.6,
            UpdateStatementArgsMutationStrategy: 0.5,
        }
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_mutation_strategies_value_greater_than_one(self):
        args = self.correct_args.copy()
        args["config"]["mutation_strategies"] = {
            RemoveStatementMutationStrategy: 1.1,
            ReplaceStatementMutationStrategy: -0.05,
            UpdateStatementArgsMutationStrategy: -0.05,
        }
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_search_with_defaults_should_not_raise_any(self):
        logger = logging.getLogger("program_searcher")
        logger.handlers = []
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        program_search = ProgramSearch(
            program_name="test",
            program_arg_names=["a", "b"],
            return_program_var_count=1,
            available_functions=available_functions,
            stop_condition=MaxStepsStopCondition(max_steps=100),
            evaluate_program_func=eval_func,
            min_program_statements=1,
            max_program_statements=5,
            config={"pop_size": 100, "restart_steps": 10, "logger": logger},
        )

        result_pr, result_fitness = program_search.search()
        print(result_fitness)
        print(result_pr.program_str)

    def test_search_should_not_raise_any(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "program_search.log")
            csv_dir = tmpdir

            logger = logging.getLogger("program_searcher")
            logger.setLevel(logging.DEBUG)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            warm_start_program = Program(
                program_name="test", program_arg_names=["a", "b"]
            )
            warm_start_program.insert_statement(
                Statement(["a", "b"], func="op.substract")
            )
            warm_start_program.insert_statement(
                Statement(["a", "b"], func="op.multiply")
            )
            warm_start = WarmStartProgram(warm_start_program)

            mutation_strategies = {
                UpdateStatementArgsMutationStrategy(): 1 / 4,
                RemoveStatementMutationStrategy(): 1 / 4,
                ReplaceStatementMutationStrategy(
                    available_functions={
                        "op.add": 2,
                        "op.substract": 2,
                        "const": 1,
                        "op.multipy": 2,
                    }
                ): 1 / 2,
            }

            evolution_operator = TournamentSelectionOperator(tournament_size=20)

            program_search = ProgramSearch(
                program_name="test",
                program_arg_names=["a", "b"],
                return_program_var_count=1,
                available_functions=available_functions,
                stop_condition=MaxStepsStopCondition(max_steps=100),
                evaluate_program_func=eval_func,
                min_program_statements=1,
                max_program_statements=5,
                config={
                    "pop_size": 100,
                    "restart_steps": 15,
                    "logger": logger,
                    "mutation_strategies": mutation_strategies,
                    "warm_start_program": warm_start,
                    "step_trackers": [
                        CsvStepsTracker(file_dir=csv_dir, save_batch_size=5)
                    ],
                    "evolution_operator": evolution_operator,
                    "seed": 42,
                },
            )

            result_pr, result_fitness = program_search.search()
            print(result_fitness)
            print(result_pr.program_str)


class MockStopCondition:
    def is_met(self):
        return True

    def step(self):
        pass


class Operations:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def substract(a, b):
        return a - b

    @staticmethod
    def multiply(a, b):
        return a * b


op = Operations()
available_functions = {
    "op.add": 2,
    "op.substract": 2,
    "const": 1,
    "op.multiply": 2,
}


def eval_func(program: Program):
    tries = 50
    errors = 0
    for _ in range(tries):
        rand_a = random.randint(1, 100)
        rand_b = random.randint(1, 100)

        try:
            program.abstract_execution(available_functions)

            real_res = rand_a - rand_b + rand_a * rand_b
            res = program.execute(
                program_args={"a": rand_a, "b": rand_b}, global_args={"op": op}
            )

            errors += abs(real_res - res)

        except Exception:
            return -1_000_000

    return -errors / tries


if __name__ == "__main__":
    unittest.main()
