import copy
import hashlib

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
        self._result_var_name = None
        self.args = args
        self.func = func

    def set_result_var_name(self, result_var_name: str):
        self._result_var_name = result_var_name

    def to_code(self) -> str:
        if not len(self.args):
            return f"{self._result_var_name}={self.func}()"
        elif len(self.args) == 1:
            args_str = self.args[0]
        else:
            args_str = ", ".join(map(str, self.args))

        if self.func == self.CONST_KEYWORD:
            return f"{self._result_var_name}={args_str}"
        if self.func == self.RETURN_KEYWORD:
            return f"return {args_str}"

        return f"{self._result_var_name}={self.func}({args_str})"

    def copy(self):
        args_copy = self.args.copy()

        new_stmt = Statement(args_copy, self.func)
        new_stmt._result_var_name = self._result_var_name
        return new_stmt

    def __eq__(self, value):
        if not isinstance(value, Statement):
            return False

        return self.func == value.func and self.args == value.args

    def __hash__(self):
        return hash((self.func, tuple(self.args)))


class Program:
    def __init__(
        self,
        program_name: str,
        program_arg_names: List[str],
        return_vars_count: int = 1,
    ):
        self.program_name = program_name
        self.program_arg_names = program_arg_names
        self.reutrn_vars_count = return_vars_count

        self._variables = program_arg_names.copy()
        self._statements: List[Statement] = []
        self.last_variable_index = 1
        self.has_return_statement = False

    def insert_statement(self, statement: Statement, index: int = -1):
        variable_name = f"x{self.last_variable_index}"
        self.last_variable_index += 1

        statement.set_result_var_name(variable_name)
        self._variables.append(variable_name)

        if statement.func == Statement.RETURN_KEYWORD:
            self.has_return_statement = True

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

        for stmt in self._statements:
            if stmt_to_remove._result_var_name in stmt.args:
                raise RemoveStatementError(
                    f"Variable '{stmt_to_remove._result_var_name}' is still referenced by another statement – cannot remove."
                )

        self._statements.remove(stmt_to_remove)
        self._variables.remove(stmt_to_remove._result_var_name)

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

        return program_str

    def execute(
        self, progrma_args: Dict[str, object] = {}, global_args: Dict[str, object] = {}
    ):
        if set(progrma_args.keys()) != set(self.program_arg_names):
            raise ExecuteProgramError(
                f"Invalid arguments for program execution. "
                f"Expected keys: {set(self.program_arg_names)}, "
                f"but got: {set(progrma_args.keys())}."
            )

        exec(self.program_str, global_args, progrma_args)

        func_args = {k: progrma_args[k] for k in self.program_arg_names}
        return_value = progrma_args[self.program_name](**func_args)

        return return_value

    def abstract_execution(self, allowed_func: Dict[str, int]):
        defined_vars = set(self.program_arg_names)

        if not self.has_return_statement:
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

            defined_vars.add(stmt._result_var_name)

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

            if stmt._result_var_name not in var_mapping:
                var_mapping[stmt._result_var_name] = f"v{canonical_counter}"
                canonical_counter += 1
            result_var = var_mapping[stmt._result_var_name]

            canonical_repr.append((stmt.func, tuple(canon_args), result_var))

        repr_str = str(canonical_repr).encode("utf-8")
        return hashlib.sha256(repr_str).hexdigest()

    def copy(self):
        new_program = Program(self.program_name, self.program_arg_names.copy())
        new_program._statements = [copy.deepcopy(stmt) for stmt in self._statements]
        new_program._variables = self._variables.copy()
        new_program.last_variable_index = self.last_variable_index
        return new_program

    def to_python_func(self, global_args: Dict[str, object] = {}) -> Callable:
        local_ns = {}
        exec(self.program_str, global_args, local_ns)
        func = local_ns[self.program_arg_names]

        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def _add_return_statement_if_not_contained(self):
        if self.has_return_statement:
            return

        return_vars = self._variables[-self.reutrn_vars_count :]
        return_stmt = Statement("return", return_vars)
        self._statements.append(return_stmt)

    def _ensure_proper_stmt_index(self, index: int):
        if index < 0 or index > len(self._statements) - 1:
            raise InvalidStatementIndexError(
                f"Invalid index {index}. Expected 0 <= index <= {len(self._statements) - 1} "
                f"(number of statements: {len(self._statements)})."
            )

    def __len__(self):
        return len(self._statements)


class WarmStartProgram:
    def __init__(self, program: Program, fitness: float):
        self.program = program
        self.fitness = fitness
