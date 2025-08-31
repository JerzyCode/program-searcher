import copy
import hashlib

import networkx as nx
from typing_extensions import Callable, Dict, List

from program_searcher.exceptions import (
    ExecuteProgramError,
    InvalidStatementIndexError,
    RemoveStatementError,
    UpdateStatementArgumentsError,
)


class Statement:
    RETURN_KEYWORD = "return"
    CONST_KEYWORD = "const"

    def __init__(self, args: List, func: str):
        self.result_var_name = None
        self.args = args
        self.func = func

    def set_result_var_name(self, result_var_name: str):
        self.result_var_name = result_var_name

    def to_code(self) -> str:
        if not len(self.args):
            return f"{self.result_var_name}={self.func}()"
        elif len(self.args) == 1:
            args_str = self.args[0]
        else:
            args_str = ", ".join(map(str, self.args))

        if self.func == self.CONST_KEYWORD:
            return f"{self.result_var_name}={args_str}"
        if self.func == self.RETURN_KEYWORD:
            return f"return {args_str}"

        return f"{self.result_var_name}={self.func}({args_str})"

    def copy(self):
        args_copy = self.args.copy()

        new_stmt = Statement(args_copy, self.func)
        new_stmt.result_var_name = self.result_var_name
        return new_stmt

    def is_equivalent(self, other: "Statement"):
        return self.func == other.func and self.args == other.args


class Program:
    def __init__(
        self,
        program_name: str,
        program_arg_names: List[str],
        return_vars_count: int = 1,
    ):
        self.program_name = program_name
        self.program_arg_names = program_arg_names
        self.return_vars_count = return_vars_count

        self.variables = program_arg_names.copy()
        self._statements: List[Statement] = []
        self.last_variable_index = 1
        self.execution_error = None
        self.program_str = None
        self.graph: nx.Graph = None

    def get_statement(self, index: int):
        self._ensure_proper_stmt_index(index)
        return self._statements[index]

    def insert_statement(self, statement: Statement, index: int = -1):
        variable_name = f"x{self.last_variable_index}"
        self.last_variable_index += 1

        statement.set_result_var_name(variable_name)
        self.variables.append(variable_name)

        if index == -1:
            self._statements.append(statement)
        else:
            self._statements.insert(index, statement)

    def remove_statement(self, index: int):
        if not self._statements:
            raise RemoveStatementError(
                "Program has 0 statements. There is nothing to remove."
            )

        self._ensure_proper_stmt_index(index)
        stmt_to_remove = self._statements[index]

        if stmt_to_remove.result_var_name not in self.variables:
            raise RemoveStatementError(
                f"Variable '{stmt_to_remove.result_var_name}' is not contained in program variables."
            )

        for stmt in self._statements:
            if stmt_to_remove.result_var_name in stmt.args:
                raise RemoveStatementError(
                    f"Variable '{stmt_to_remove.result_var_name}' is still referenced by another statement – cannot remove."
                )

        self._statements.remove(stmt_to_remove)

        if stmt_to_remove.result_var_name is not None:
            self.variables.remove(stmt_to_remove.result_var_name)

    def update_statement_full(self, index: int, new_func, new_args):
        if not self._statements:
            raise RemoveStatementError(
                "Program has 0 statements. There is nothing to replace."
            )

        self._ensure_proper_stmt_index(index)
        stmt = self._statements[index]
        stmt.args = new_args
        stmt.func = new_func

    def update_statment_args(self, index: int, new_args: List):
        self._ensure_proper_stmt_index(index)

        stmt_to_modify = self._statements[index]
        if len(stmt_to_modify.args) != len(new_args):
            raise UpdateStatementArgumentsError(
                f"Cannot update statement at index {index}: expected {len(stmt_to_modify.args)} "
                f"arguments, but got {len(new_args)}."
            )

        stmt_to_modify.args = new_args

    def generate_code(self) -> str:
        self._add_return_statement_if_not_contained()

        program_str = f"def {self.program_name}"
        if self.program_arg_names:
            program_str += f"({', '.join(self.program_arg_names)}):\n"
        else:
            program_str += "():\n"

        for stmt in self._statements:
            program_str += f"   {stmt.to_code()}\n"

        self.program_str = program_str

    def execute(
        self, program_args: Dict[str, object] = {}, global_args: Dict[str, object] = {}
    ):
        """
        Executes the compiled program with the given arguments.

        This method runs the program string (`self.program_str`) in the provided
        global and local contexts, then calls the program's entry function
        (`self.program_name`) with the required arguments.

        Parameters
        ----------
        program_args : Dict[str, object], optional
            A dictionary of arguments passed to the program function.
            Keys must exactly match `self.program_arg_names`.
        global_args : Dict[str, object], optional
            A dictionary of global variables or functions that should be
            available during program execution.

        Returns
        -------
        object
            The return value of the executed program's entry function.

        Raises
        ------
        ExecuteProgramError
            If the provided arguments do not match the expected names.
        Exception
            Any exception raised during execution of the program will be
            re-raised after marking `self.has_errors = True`.

        Notes
        -----
        - Mutates `self.has_errors` depending on whether execution succeeds.
        - `program_args` are executed as the local namespace, and `global_args`
        as the global namespace when evaluating `self.program_str`.
        """
        if set(program_args.keys()) != set(self.program_arg_names):
            raise ExecuteProgramError(
                f"Invalid arguments for program execution. "
                f"Expected keys: {set(self.program_arg_names)}, "
                f"but got: {set(program_args.keys())}."
            )

        if self.program_str is None:
            self.generate_code()

        try:
            exec(self.program_str, global_args, program_args)

            func_args = {k: program_args[k] for k in self.program_arg_names}
            return_value = program_args[self.program_name](**func_args)
            self.execution_error = None

            return return_value
        except Exception as e:
            self.execution_error = e
            raise e

    def abstract_execution(self, allowed_func: Dict[str, int]):
        self._add_return_statement_if_not_contained()
        allowed_func = allowed_func.copy()
        allowed_func[Statement.RETURN_KEYWORD] = self.return_vars_count

        defined_vars = set(self.program_arg_names)

        if not self.has_return_statement():
            raise ExecuteProgramError(
                "Program must contain a return statement, but none was found."
            )

        for i, stmt in enumerate(self._statements):
            func_name = stmt.func
            args = stmt.args

            if func_name not in allowed_func:
                raise ExecuteProgramError(
                    f"Statement {i}: Function '{func_name}' is not in allowed_func. "
                    f"Allowed functions: {list(allowed_func.keys())}"
                )

            expected_arg_count = allowed_func[func_name]
            if len(args) != expected_arg_count:
                raise ExecuteProgramError(
                    f"Statement {i}: Function '{func_name}' expects {expected_arg_count} args, "
                    f"but got {len(args)} ({args})."
                )

            for arg in args:
                if arg not in defined_vars:
                    raise ExecuteProgramError(
                        f"Statement {i}: Variable '{arg}' is not defined before usage in '{func_name}'. "
                        f"Currently defined variables: {defined_vars}"
                    )

            defined_vars.add(stmt.result_var_name)

    def generate_graph(self) -> nx.DiGraph:
        if not self.has_return_statement():
            raise ExecuteProgramError(
                "Program must contain a return statement to generate graph."
            )

        G = nx.DiGraph()
        func_counts: Dict[str, int] = {}
        arg_counts: Dict[str, int] = {}
        var_stmts: Dict[str, Statement] = {}
        stmt_nodes: Dict[Statement, str] = {}

        def create_func_node(stmt: Statement):
            node_id = f"{stmt.func}_{func_counts.get(stmt.func, 0)}"
            G.add_node(node_id, label=stmt.func, type="func")
            func_counts[stmt.func] = func_counts.get(stmt.func, 0) + 1
            stmt_nodes[stmt] = node_id
            return node_id

        def create_input_node(arg):
            if arg not in self.program_arg_names:
                return
            node_id = f"{arg}_{arg_counts.get(arg, 0)}"
            G.add_node(node_id, label=arg, type="input")
            arg_counts[arg] = arg_counts.get(arg, 0) + 1
            return node_id

        for stmt in self._statements:
            create_func_node(stmt)
            var_stmts[stmt.result_var_name] = stmt

        for stmt, node_id in stmt_nodes.items():
            for idx, arg in enumerate(stmt.args):
                if arg in self.program_arg_names:
                    arg_node_id = create_input_node(arg)
                    G.add_edge(arg_node_id, node_id, arg_pos=idx)
                else:
                    res_stmt = var_stmts[arg]
                    prev_node_id = stmt_nodes[res_stmt]
                    G.add_edge(prev_node_id, node_id, arg_pos=idx)

        self.graph = G

    def to_hash(self):
        var_mapping = {}
        canonical_counter = 0

        for i, arg in enumerate(self.program_arg_names):
            var_mapping[arg] = f"in{i}"

        canonical_repr = []

        for stmt in self._statements:
            canon_args = []
            for arg in stmt.args:
                if arg not in var_mapping:
                    var_mapping[arg] = f"v{canonical_counter}"
                    canonical_counter += 1
                canon_args.append(var_mapping[arg])

            if stmt.result_var_name not in var_mapping:
                var_mapping[stmt.result_var_name] = f"v{canonical_counter}"
                canonical_counter += 1
            result_var = var_mapping[stmt.result_var_name]

            canonical_repr.append((stmt.func, tuple(canon_args), result_var))

        repr_str = str(canonical_repr).encode("utf-8")
        return hashlib.sha256(repr_str).hexdigest()

    def copy(self):
        new_program = Program(self.program_name, self.program_arg_names.copy())
        new_program._statements = [copy.deepcopy(stmt) for stmt in self._statements]
        new_program.variables = self.variables.copy()
        new_program.last_variable_index = self.last_variable_index
        return new_program

    def to_python_func(self, global_args: Dict[str, object] = {}) -> Callable:
        local_ns = {}
        exec(self.program_str, global_args, local_ns)
        func = local_ns[self.program_name]

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def _add_return_statement_if_not_contained(self):
        if self.has_return_statement():
            return

        return_vars = self.variables[-self.return_vars_count :]
        return_stmt = Statement(func="return", args=return_vars)
        self._statements.append(return_stmt)

    def _ensure_proper_stmt_index(self, index: int):
        if index < 0 or index > len(self._statements) - 1:
            raise InvalidStatementIndexError(
                f"Invalid index {index}. Expected 0 <= index <= {len(self._statements) - 1} "
                f"(number of statements: {len(self._statements)})."
            )

    def has_return_statement(self):
        return any(stmt.func == Statement.RETURN_KEYWORD for stmt in self._statements)

    def __len__(self):
        return len(self._statements)


class WarmStartProgram:
    def __init__(self, program: Program, fitness: float = None):
        self.program = program
        self.fitness = fitness
