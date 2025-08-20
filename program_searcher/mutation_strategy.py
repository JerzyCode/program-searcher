from abc import ABC, abstractmethod

from typing_extensions import override

from program_searcher.program_model import Program, Statement


class MutationStrategy(ABC):
    @abstractmethod
    def mutate(self, program: Program, **kwargs):
        raise NotImplementedError


class RemoveStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError


class ReplaceStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError

    def _generate_random_statement(self, program_len: int) -> Statement:
        raise NotImplementedError


class InsertStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError


class UpdateStatementArgsMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError
