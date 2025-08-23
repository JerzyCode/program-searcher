import random
import unittest

from program_searcher.mutation_strategy import (
    RemoveStatementMutationStrategy,
    ReplaceStatementMutationStrategy,
    UpdateStatementArgsMutationStrategy,
)
from program_searcher.program_model import Program, Statement


def make_program_with_return():
    prog = Program(program_name="dummy", program_arg_names=["X", "y"])
    prog.insert_statement(Statement(args=["X", "y"], func="add"))  # x1
    prog.insert_statement(Statement(args=["x1", "y"], func="substract"))  # x2
    prog.insert_statement(Statement(args=["x2", "x1"], func="divide"))  # x3
    prog.insert_statement(Statement(args=["x3"], func="return"))
    return prog


def make_program_no_return():
    prog = Program(program_name="dummy", program_arg_names=["X", "y"])
    prog.insert_statement(Statement(args=["X", "y"], func="add"))  # x1
    prog.insert_statement(Statement(args=["x1", "y"], func="substract"))  # x2
    prog.insert_statement(Statement(args=["x2", "x1"], func="divide"))  # x3
    return prog


class TestRemoveStatementMutationStrategy(unittest.TestCase):
    def setUp(self):
        random.seed(42)
        self.sut = RemoveStatementMutationStrategy(remove_retries=3)

    def test_remove_simple_statement(self):
        prog = make_program_no_return()
        len_pr_before = len(prog)
        strat = RemoveStatementMutationStrategy(remove_retries=3)

        strat.mutate(prog)

        self.assertEqual(len(prog), len_pr_before - 1)

    def test_does_not_remove_return_statement(self):
        prog = make_program_with_return()
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


class TestReplaceStatementMutationStrategy(unittest.TestCase):
    def setUp(self):
        random.seed(42)
        self.available_functions = {
            "add": 2,
            "substract": 2,
            "divide": 2,
            "negate": 1,
        }
        self.strategy = ReplaceStatementMutationStrategy(self.available_functions)

    def test_replaces_function_and_args(self):
        prog = make_program_no_return()
        max_index = len(prog) - 1
        self.strategy.mutate(prog)

        for stmt in prog._statements[:max_index]:
            self.assertIn(stmt.func, self.available_functions)
            self.assertEqual(len(stmt.args), self.available_functions[stmt.func])

    def test_replacement_does_not_remove_statements(self):
        prog = make_program_no_return()
        before = len(prog)
        self.strategy.mutate(prog)
        after = len(prog)

        self.assertEqual(before, after)

    def test_return_statement_not_replaced(self):
        prog = make_program_with_return()
        self.strategy.mutate(prog)

        self.assertTrue(any(stmt.func == "return" for stmt in prog._statements))

    def test_only_return_program_remains_unchanged(self):
        prog = Program(program_name="dummy", program_arg_names=["X"])
        prog.insert_statement(Statement(args=["X"], func="return"))

        before_funcs = [stmt.func for stmt in prog._statements]
        self.strategy.mutate(prog)
        after_funcs = [stmt.func for stmt in prog._statements]

        self.assertEqual(before_funcs, after_funcs)

    def test_empty_program_remains_unchanged(self):
        prog = Program(program_name="dummy", program_arg_names=["X"])
        self.strategy.mutate(prog)
        self.assertEqual(len(prog), 0)


class TestUpdateStatementArgsMutationStrategy(unittest.TestCase):
    def setUp(self):
        random.seed(42)
        self.strategy = UpdateStatementArgsMutationStrategy()

    def test_arguments_are_replaced(self):
        prog = make_program_no_return()
        original_args = [stmt.args[:] for stmt in prog._statements]

        self.strategy.mutate(prog)

        for orig, stmt in zip(original_args, prog._statements):
            self.assertEqual(len(orig), len(stmt.args))

        for stmt in prog._statements:
            for arg in stmt.args:
                self.assertIn(arg, prog.variables)

    def test_single_statement_updated(self):
        prog = make_program_no_return()
        original_args = [stmt.args[:] for stmt in prog._statements]

        self.strategy.mutate(prog)

        self.assertTrue(
            any(
                orig != stmt.args for orig, stmt in zip(original_args, prog._statements)
            )
        )

    def test_return_statement_can_be_updated(self):
        prog = make_program_with_return()
        return_stmt_index = len(prog._statements) - 1
        original_args = prog.get_statement(return_stmt_index).args[:]

        self.strategy.mutate(prog)

        self.assertEqual(
            len(original_args), len(prog.get_statement(return_stmt_index).args)
        )

    def test_empty_program_no_crash(self):
        prog = Program(program_name="dummy", program_arg_names=["X"])
        self.strategy.mutate(prog)
        self.assertEqual(len(prog), 0)

    def test_at_least_one_statement_args_changed(self):
        prog = make_program_no_return()
        original_args = [stmt.args[:] for stmt in prog._statements]

        self.strategy.mutate(prog)

        self.assertTrue(
            any(
                orig != stmt.args for orig, stmt in zip(original_args, prog._statements)
            ),
            "Żaden statement nie zmienił argumentów",
        )


if __name__ == "__main__":
    unittest.main()
