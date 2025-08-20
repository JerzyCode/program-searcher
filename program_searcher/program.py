from typing import List


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
        elif self.func == self.RETURN_KEYWORD:
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
