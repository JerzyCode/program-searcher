import unittest

from program_searcher.exceptions import InvalidProgramSearchArgumentValue
from program_searcher.mutation_strategy import (
    InsertStatementMutationStrategy,
    RemoveStatementMutationStrategy,
    UpdateStatementArgsMutationStrategy,
)
from program_searcher.program_search import ProgramSearch


class TestProgramSearchValidation(unittest.TestCase):
    def setUp(self):
        self.correct_args = {
            "program_name": "test_program",
            "program_arg_names": ["x"],
            "available_functions": {"add": 2},
            "min_program_statements": 1,
            "max_program_statements": 5,
            "stop_condition": MockStopCondition(),
            "evaluate_program_func": lambda p: 0.0,
            "pop_size": 10,
            "tournament_size": 2,
            "replace_arg_for_const_prob": 0.5,
            "mutation_probs": {
                RemoveStatementMutationStrategy: 0.3,
                InsertStatementMutationStrategy: 0.3,
                UpdateStatementArgsMutationStrategy: 0.4,
            },
        }

    def test_valid_arguments(self):
        try:
            ProgramSearch(**self.correct_args)
        except InvalidProgramSearchArgumentValue:
            self.fail(
                "Valid arguments raised InvalidProgramSearchArgumentValue unexpectedly."
            )

    def test_min_greater_than_max(self):
        args = self.correct_args.copy()
        args["min_program_statements"] = 6
        args["max_program_statements"] = 5
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_negative_pop_size(self):
        args = self.correct_args.copy()
        args["pop_size"] = -1
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_negative_tournament_size(self):
        args = self.correct_args.copy()
        args["tournament_size"] = -1
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_tournament_larger_than_pop(self):
        args = self.correct_args.copy()
        args["tournament_size"] = 20
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_replace_arg_for_const_prob_not_allowed(self):
        args = self.correct_args.copy()
        args["replace_arg_for_const_prob"] = 1.5
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

        args["replace_arg_for_const_prob"] = -1
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_invalid_mutation_probs_sum(self):
        args = self.correct_args.copy()
        args["mutation_probs"] = {
            InsertStatementMutationStrategy: 0.5,
            RemoveStatementMutationStrategy: 0.5,
            UpdateStatementArgsMutationStrategy: 0.5,
        }
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_mutation_probs_negative_value(self):
        args = self.correct_args.copy()
        args["mutation_probs"] = {
            RemoveStatementMutationStrategy: -0.1,
            InsertStatementMutationStrategy: 0.6,
            UpdateStatementArgsMutationStrategy: 0.5,
        }
        with self.assertRaises(InvalidProgramSearchArgumentValue):
            ProgramSearch(**args)

    def test_mutation_probs_value_greater_than_one(self):
        args = self.correct_args.copy()
        args["mutation_probs"] = {
            RemoveStatementMutationStrategy: 1.1,
            InsertStatementMutationStrategy: -0.05,
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
