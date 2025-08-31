import unittest

from program_searcher.evolution_operator import TournamentSelectionOperator
from program_searcher.exceptions import InvalidMutationStrategiesError
from program_searcher.mutation_strategy import (
    RemoveStatementMutationStrategy,
    ReplaceStatementMutationStrategy,
    UpdateStatementArgsMutationStrategy,
)


class TestTorunamentSelectionEvolutionStrategy(unittest.TestCase):
    def test_invalid_mutation_strategies_sum(self):
        mutation_strategies = {
            ReplaceStatementMutationStrategy: 0.5,
            RemoveStatementMutationStrategy: 0.5,
            UpdateStatementArgsMutationStrategy: 0.5,
        }
        with self.assertRaises(InvalidMutationStrategiesError):
            TournamentSelectionOperator(
                tournament_size=1, mutation_strategies=mutation_strategies
            )

    def test_mutation_strategies_negative_value(self):
        mutation_strategies = {
            RemoveStatementMutationStrategy: -0.1,
            ReplaceStatementMutationStrategy: 0.6,
            UpdateStatementArgsMutationStrategy: 0.5,
        }
        with self.assertRaises(InvalidMutationStrategiesError):
            TournamentSelectionOperator(
                tournament_size=1, mutation_strategies=mutation_strategies
            )

    def test_mutation_strategies_value_greater_than_one(self):
        mutation_strategies = {
            RemoveStatementMutationStrategy: 1.1,
            ReplaceStatementMutationStrategy: -0.05,
            UpdateStatementArgsMutationStrategy: -0.05,
        }
        with self.assertRaises(InvalidMutationStrategiesError):  # noqa: F821
            TournamentSelectionOperator(
                tournament_size=1, mutation_strategies=mutation_strategies
            )
