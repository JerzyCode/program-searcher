import random
import unittest

from program_searcher.mutation_strategy import RemoveStatementMutationStrategy
from program_searcher.program_model import Program, Statement


class TestRemoveStatementMutationStrategy(unittest.TestCase):
    def setUp(self):
        random.seed(42)
        self.sut = RemoveStatementMutationStrategy(remove_retries=3)

    def make_program_with_return(self):
        prog = Program(program_name="dummy", program_arg_names=["X", "y"])
        prog.insert_statement(Statement(args=["X", "y"], func="add"))  # x1
        prog.insert_statement(Statement(args=["x1", "y"], func="substract"))  # x2
        prog.insert_statement(Statement(args=["x2", "x1"], func="divide"))  # x3
        prog.insert_statement(Statement(args=["x3"], func="return"))  # return
        return prog

    def make_program_no_return(self):
        prog = Program(program_name="dummy", program_arg_names=["X", "y"])
        prog.insert_statement(Statement(args=["X", "y"], func="add"))  # x1
        prog.insert_statement(Statement(args=["x1", "y"], func="substract"))  # x2
        prog.insert_statement(Statement(args=["x2", "x1"], func="divide"))  # x3
        return prog

    def test_remove_simple_statement(self):
        prog = self.make_program_no_return()
        len_pr_before = len(prog)
        strat = RemoveStatementMutationStrategy(remove_retries=3)

        strat.mutate(prog)

        self.assertEqual(len(prog), len_pr_before - 1)

    def test_does_not_remove_return_statement(self):
        prog = self.make_program_with_return()
        prog.has_return_statement = True
        strat = RemoveStatementMutationStrategy(remove_retries=3)

        strat.mutate(prog)

        self.assertTrue(any(stmt.func == "return" for stmt in prog._statements))

    def test_dependency_blocks_removal(self):
        prog = Program(program_name="dummy", program_arg_names=["X"])
        prog.insert_statement(Statement(args=["X"], func="negate"))  # x1
        prog.insert_statement(Statement(args=["x1"], func="square"))  # x2
        prog.insert_statement(Statement(args=["x2"], func="return"))  # return

        before = len(prog)
        self.sut.mutate(prog)
        after = len(prog)

        self.assertEqual(before, after)

    def test_empty_program(self):
        prog = Program(program_name="dummy", program_arg_names=["X", "y"])
        self.sut.mutate(prog)
        self.assertEqual(len(prog), 0)

    def test_program_with_only_return(self):
        prog = Program(program_name="dummy", program_arg_names=["X"])
        prog.insert_statement(Statement(args=["X"], func="return"))

        before = len(prog)
        self.sut.mutate(prog)
        after = len(prog)

        self.assertEqual(before, after)
        self.assertTrue(all(stmt.func == "return" for stmt in prog._statements))


if __name__ == "__main__":
    unittest.main()
