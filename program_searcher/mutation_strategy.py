from abc import ABC, abstractmethod
from typing import override

from program_searcher.program_model import Program


class MutationStrategy(ABC):
    @abstractmethod
    def mutate(self, program: Program) -> Program:
        raise NotImplementedError


class RemoveStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program) -> Program:
        raise NotImplementedError


class InsertStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program) -> Program:
        raise NotImplementedError


class UpdateStatementArgsMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program) -> Program:
        raise NotImplementedError
