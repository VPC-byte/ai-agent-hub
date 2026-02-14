"""Safe calculator tool backed by AST expression evaluation."""

from __future__ import annotations

import ast
import math
from typing import Any

from ai_agent_hub.tools.base import BaseTool, ToolResult


class _SafeEvaluator(ast.NodeVisitor):
    """AST visitor that safely evaluates arithmetic expressions."""

    ALLOWED_BINOPS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a**b,
        ast.Mod: lambda a, b: a % b,
        ast.FloorDiv: lambda a, b: a // b,
    }
    ALLOWED_UNARYOPS = {
        ast.UAdd: lambda a: +a,
        ast.USub: lambda a: -a,
    }
    ALLOWED_FUNCS = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "abs": abs,
        "round": round,
    }

    def visit(self, node: ast.AST) -> float:
        return super().visit(node)

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> float:
        if not isinstance(node.value, (int, float)):
            raise ValueError("Only numeric constants are allowed")
        return float(node.value)

    def visit_Num(self, node: ast.Num) -> float:  # pragma: no cover (py<3.8 compat)
        return float(node.n)

    def visit_BinOp(self, node: ast.BinOp) -> float:
        op_type = type(node.op)
        if op_type not in self.ALLOWED_BINOPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = self.visit(node.left)
        right = self.visit(node.right)
        return self.ALLOWED_BINOPS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        op_type = type(node.op)
        if op_type not in self.ALLOWED_UNARYOPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = self.visit(node.operand)
        return self.ALLOWED_UNARYOPS[op_type](operand)

    def visit_Call(self, node: ast.Call) -> float:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only named function calls are allowed")
        func_name = node.func.id
        func = self.ALLOWED_FUNCS.get(func_name)
        if func is None:
            raise ValueError(f"Function not allowed: {func_name}")
        args = [self.visit(arg) for arg in node.args]
        return float(func(*args))

    def generic_visit(self, node: ast.AST) -> Any:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


class CalculatorTool(BaseTool):
    """Evaluate safe arithmetic expressions."""

    name = "calculator"
    description = "Evaluate mathematical expressions safely"

    async def run(self, **kwargs: Any) -> ToolResult:
        expression = str(kwargs.get("expression", "")).strip()
        if not expression:
            return ToolResult(success=False, output=None, error="Missing 'expression'")

        try:
            node = ast.parse(expression, mode="eval")
            value = _SafeEvaluator().visit(node)
            return ToolResult(success=True, output=value)
        except Exception as exc:
            return ToolResult(success=False, output=None, error=str(exc))
