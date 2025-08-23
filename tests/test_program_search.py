import logging
import unittest

from program_searcher.exceptions import InvalidProgramSearchArgumentValue
from program_searcher.mutation_strategy import (
    RemoveStatementMutationStrategy,
    ReplaceStatementMutationStrategy,
    UpdateStatementArgsMutationStrategy,
)
from program_searcher.program_search import ProgramSearch


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
                "tournament_size": 2,
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

    def test_negative_tournament_size(self):
        args = self.correct_args.copy()
        args["config"]["tournament_size"] = -1
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_tournament_larger_than_pop(self):
        args = self.correct_args.copy()
        args["config"]["tournament_size"] = 20
        args["config"]["pop_size"] = 10
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


class MockStopCondition:
    def is_met(self):
        return True

    def step(self):
        pass


if __name__ == "__main__":
    unittest.main()
