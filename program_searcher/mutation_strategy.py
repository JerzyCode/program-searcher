import random
from abc import ABC, abstractmethod

from typing_extensions import override

from program_searcher.exceptions import RemoveStatementError
from program_searcher.program_model import Program, Statement


class MutationStrategy(ABC):
    @abstractmethod
    def mutate(self, program: Program):
        raise NotImplementedError


class RemoveStatementMutationStrategy(MutationStrategy, ABC):
    def __init__(self, remove_retries: int = 3):
        self.remove_retries = remove_retries

    @override
    def mutate(self, program: Program):
        max_index = len(program) - (1 if program.has_return_statement else 0)

        if max_index <= 0:
            return

        for _ in range(self.remove_retries):
            try:
                statement_to_remove_idx = random.randrange(max_index)
                program.remove_statement(statement_to_remove_idx)
                break
            except RemoveStatementError:
                pass


class ReplaceStatementMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError

    def _generate_random_statement(self, program_len: int) -> Statement:
        raise NotImplementedError


class UpdateStatementArgsMutationStrategy(MutationStrategy, ABC):
    @override
    def mutate(self, program: Program):
        raise NotImplementedError
