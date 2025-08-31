import random
from abc import ABC, abstractmethod
from collections import deque

from typing_extensions import Dict, override

from program_searcher.exceptions import InvalidMutationStrategiesError
from program_searcher.mutation_strategy import MutationStrategy
from program_searcher.program_model import Program


class EvolutionOperator(ABC):
    @abstractmethod
    def apply(self, population: deque[Program], fitnesses: Dict[Program, float]):
        """
        Applies an evolution step to the population.

        Parameters
        ----------
        population : deque[Program]
            Current population of programs.
        fitnesses : Dict[Program, float]
            Mapping from program to its fitness.
        """
        raise NotImplementedError


class TournamentSelectionOperator(EvolutionOperator, ABC):
    """
    Evolution operator that applies tournament selection followed by mutation.

    At each step, a subset of the population (tournament) is randomly chosen,
    the program with the highest fitness is selected as the tournament winner,
    and then mutated using the provided mutation strategies. The mutated winner
    replaces the oldest program in the population (FIFO style).

    Attributes
    ----------
    tournament_size : int
        The number of programs to include in each tournament.
    """

    def __init__(
        self, tournament_size: int, mutation_strategies: Dict[MutationStrategy, float]
    ):
        self.tournament_size = tournament_size
        self.mutation_strategies = mutation_strategies

        self._validate_mutation_strategies()

    @override
    def apply(self, population: deque[Program], fitnesses: Dict[Program, float]):
        tournament_programs = random.choices(population, k=self.tournament_size)
        tournament_winner = max(tournament_programs, key=lambda prog: fitnesses[prog])

        program = population.popleft()
        fitnesses.pop(program)

        strategies = list(self.mutation_strategies.keys())
        weights = list(self.mutation_strategies.values())

        chosen_strategy = random.choices(strategies, weights=weights, k=1)[0]
        mutated_program = chosen_strategy.mutate(tournament_winner)

        population.append(mutated_program)

    def _validate_mutation_strategies(self):
        if abs(sum(self.mutation_strategies.values()) - 1.0) > 1e-6:
            raise InvalidMutationStrategiesError(
                f"sum of mutation_strategies values must be 1.0, but is {sum(self.mutation_strategies.values())}."
            )

        if any(value < 0 for value in self.mutation_strategies.values()):
            raise InvalidMutationStrategiesError(
                f"all mutation_strategies values must be >= 0. current values: {self.mutation_strategies}."
            )

        if any(value > 1 for value in self.mutation_strategies.values()):
            raise InvalidMutationStrategiesError(
                f"all mutation_strategies values must be <= 1. current values: {self.mutation_strategies}."
            )


class FullPopulationMutationOperator(EvolutionOperator):
    """
    Evolution operator that mutates every program in the population.

    This operator iterates through the entire population and applies a mutation
    strategy to each program according to the provided probabilities. Unlike
    tournament-based operators, it does not perform selection; it modifies
    all programs, ensuring maximum exploration of the search space.

    Methods
    -------
    apply(population, fitnesses, mutation_strategies)
        Mutates each program in-place using the specified mutation strategies.

    Notes
    -----
    - The population is modified directly; no new list is returned.
    - Each program is mutated independently, and fitnesses are not updated
      within this method.
    """

    def __init__(self, mutation_strategies: Dict[MutationStrategy, float]):
        self.mutation_strategies = mutation_strategies

    @override
    def apply(self, population: deque[Program], fitnesses: Dict[Program, float]):
        for index, program in enumerate(population):
            chosen_strategy = random.choices(
                list(self.mutation_strategies.keys()),
                weights=list(self.mutation_strategies.values()),
                k=1,
            )[0]

            mutated = chosen_strategy.mutate(program)
            population[index] = mutated
