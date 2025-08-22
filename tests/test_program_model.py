import unittest

from program_searcher.exceptions import (
    ExecuteProgramError,
    RemoveStatementError,
    UpdateStatementArgumentsError,
)
from program_searcher.program_model import Program, Statement


class TestStatement(unittest.TestCase):
    def test_to_code(self):
        stmt1 = Statement(args=["a", "b"], func="add")
        stmt1.set_result_var_name("c")
        self.assertEqual(stmt1.to_code(), "c=add(a, b)")

        stmt2 = Statement(args=["a", "b"], func="op.substract")
        stmt2.set_result_var_name("d")
        self.assertEqual(stmt2.to_code(), "d=op.substract(a, b)")

        stmt3 = Statement(args=["a", "b", "c"], func="sum")
        stmt3.set_result_var_name("res")
        self.assertEqual(stmt3.to_code(), "res=sum(a, b, c)")

        stmt4 = Statement(args=[12.0], func="const")
        stmt4.set_result_var_name("c")
        self.assertEqual(stmt4.to_code(), "c=12.0")

        stmt5 = Statement(args=["X", 13.23, "'test'"], func="return")
        stmt5.set_result_var_name("c")
        self.assertEqual(stmt5.to_code(), "return X, 13.23, 'test'")

        stmt6 = Statement(args=[], func="get_data")
        stmt6.set_result_var_name("X")
        self.assertEqual(stmt6.to_code(), "X=get_data()")

    def test_equal(self):
        stmt1 = Statement(args=["x", "y"], func="add")
        stmt2 = Statement(args=["x", "y"], func="add")
        self.assertEqual(stmt1, stmt2)

        stmt_copy = stmt1.copy()
        self.assertEqual(stmt1, stmt_copy)
        self.assertIsNot(stmt1, stmt_copy)

        stmt1 = Statement(args=["x", "y"], func="add")
        stmt2 = Statement(args=["x", "y"], func="substract")
        stmt3 = Statement(args=["a", "y"], func="substract")

        self.assertNotEqual(stmt1, stmt2)
        self.assertNotEqual(stmt1, stmt3)
        self.assertNotEqual(stmt2, stmt3)


class TestProgram(unittest.TestCase):
    def setUp(self):
        self.prog = Program("test_program", ["a", "b"])

    def test_insert_statement_adds_variable_and_return(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)

        self.assertEqual(len(self.prog._statements), 1)
        self.assertTrue(stmt._result_var_name.startswith("x"))
        self.assertIn(stmt._result_var_name, self.prog._variables)

    def test_insert_statement_sets_return_flag(self):
        stmt = Statement(["a"], Statement.RETURN_KEYWORD)
        self.prog.insert_statement(stmt)

        self.assertTrue(self.prog.has_return_statement)

    def test_update_statement_full_updates_func_and_args(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)

        new_args = ["b", "a"]
        new_func = "multiply"
        self.prog.update_statement_full(0, new_func, new_args)

        updated_stmt = self.prog._statements[0]
        self.assertEqual(updated_stmt.func, new_func)
        self.assertEqual(updated_stmt.args, new_args)

    def test_update_statement_full_empty_program_raises(self):
        with self.assertRaises(RemoveStatementError):
            self.prog.update_statement_full(0, "add", ["a", "b"])

    def test_remove_statement_success(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)
        idx = self.prog._statements.index(stmt)

        self.prog.remove_statement(idx)
        self.assertEqual(len(self.prog._statements), 0)

    def test_remove_statement_invalid_index(self):
        with self.assertRaises(RemoveStatementError):
            self.prog.remove_statement(5)

    def test_remove_statement_referenced_variable(self):
        stmt1 = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt1)
        stmt2 = Statement([stmt1._result_var_name], "neg")
        self.prog.insert_statement(stmt2)

        with self.assertRaises(RemoveStatementError):
            self.prog.remove_statement(0)

    def test_update_statement_args_success(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)

        self.prog.update_statment_args(0, ["c", "d"])
        self.assertEqual(self.prog._statements[0].args, ["c", "d"])

    def test_update_statement_args_wrong_length(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)

        with self.assertRaises(UpdateStatementArgumentsError):
            self.prog.update_statment_args(0, ["a"])

    def test_generate_code_contains_function_signature(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)
        code = self.prog.generate_code()

        self.assertIn("def test_program(a, b):", code)
        self.assertIn("add", code)

    def test_abstract_execution_valid(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)
        stmt2 = Statement([stmt._result_var_name], "return")
        self.prog.insert_statement(stmt2)

        allowed = {"add": 2, "return": 1}
        self.prog.abstract_execution(allowed)  # should not raise

    def test_abstract_execution_missing_return(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)

        allowed = {"add": 2}
        with self.assertRaises(ExecuteProgramError):
            self.prog.abstract_execution(allowed)

    def test_abstract_execution_undefined_variable(self):
        stmt = Statement(["z"], "neg")
        self.prog.insert_statement(stmt)
        stmt2 = Statement([stmt._result_var_name], "return")
        self.prog.insert_statement(stmt2)

        allowed = {"neg": 1, "return": 1}
        with self.assertRaises(ExecuteProgramError):
            self.prog.abstract_execution(allowed)

    def test_abstract_execution_wrong_arg_count(self):
        stmt = Statement(["a", "b"], "neg")
        self.prog.insert_statement(stmt)
        stmt2 = Statement([stmt._result_var_name], "return")
        self.prog.insert_statement(stmt2)

        allowed = {"neg": 1, "return": 1}
        with self.assertRaises(ExecuteProgramError):
            self.prog.abstract_execution(allowed)

    def test_to_hash_equivalence_for_isomorphic_programs(self):
        prog1 = Program("prog1", ["a"])
        stmt1 = Statement(["a"], "neg")
        prog1.insert_statement(stmt1)
        stmt2 = Statement([stmt1._result_var_name], "return")
        prog1.insert_statement(stmt2)

        prog2 = Program("prog2", ["x"])
        stmt3 = Statement(["x"], "neg")
        prog2.insert_statement(stmt3)
        stmt4 = Statement([stmt3._result_var_name], "return")
        prog2.insert_statement(stmt4)

        self.assertEqual(prog1.to_hash(), prog2.to_hash())

    def test_copy_creates_independent_program(self):
        stmt = Statement(["a", "b"], "add")
        self.prog.insert_statement(stmt)
        prog_copy = self.prog.copy()

        self.assertNotEqual(id(self.prog), id(prog_copy))
        self.assertNotEqual(id(self.prog._statements[0]), id(prog_copy._statements[0]))


if __name__ == "__main__":
    unittest.main()
