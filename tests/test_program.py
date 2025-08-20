import unittest

from program_searcher.program import Statement


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


if __name__ == "__main__":
    unittest.main()
