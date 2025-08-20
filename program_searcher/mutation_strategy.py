from abc import ABC, abstractmethod
from typing import override

from program_searcher.program_model import Program


class MutationStrategy(ABC):
    @abstractmethod
    def mutate(self, program: Program):
        raise NotImplementedError


class RemoveStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError


class InsertStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError

    def _generate_random_statement(self):
        pass


class UpdateStatementArgsMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError
