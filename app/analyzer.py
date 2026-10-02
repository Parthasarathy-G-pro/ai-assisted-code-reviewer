
import ast
import re

PROBLEMS = {
    "two_sum": {
        "name": "Two Sum",
        "time": "O(n)",
        "space": "O(n)",
        "advice": (
            "Use a hash map to store previously visited "
            "numbers and their indices. For each number, "
            "check whether its complement is already stored. "
            "This gives expected O(n) time and O(n) space."
        )
    },
    "contains_duplicate": {
        "name": "Contains Duplicate",
        "time": "O(n) expected",
        "space": "O(n)",
        "advice": (
            "Use a hash set to track visited values. "
            "If a value already exists in the set, "
            "a duplicate has been found."
        )
    },
    "sorted_search": {
        "name": "Search in Sorted Array",
        "time": "O(log n)",
        "space": "O(1)",
        "advice": (
            "Use iterative binary search. Compare the "
            "target with the middle element and discard "
            "half of the remaining search range each time."
        )
    },
    "top_k": {
        "name": "Top K Elements",
        "time": "O(n log k)",
        "space": "O(k)",
        "advice": (
            "Maintain a min-heap of size k while scanning "
            "the array. This avoids sorting all n elements."
        )
    },
    "frequency": {
        "name": "Frequency Counting",
        "time": "O(n) expected",
        "space": "O(u)",
        "advice": (
            "Use a dictionary or Counter to count "
            "frequencies in one pass. u is the number "
            "of unique values."
        )
    },
    "general": {
        "name": "General Code",
        "time": "Context-dependent",
        "space": "Context-dependent",
        "advice": (
            "Specify the problem and input constraints "
            "to identify a suitable algorithm. The optimal "
            "complexity depends on the problem."
        )
    }
}


class LoopAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.depth = 0
        self.max_depth = 0
        self.loop_count = 0

    def visit_For(self, node):
        self.loop_count += 1
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)

        for child in node.body:
            self.visit(child)

        for child in node.orelse:
            self.visit(child)

        self.depth -= 1

    def visit_While(self, node):
        self.loop_count += 1
        self.depth += 1
        self.max_depth = max(self.max_depth, self.depth)

        for child in node.body:
            self.visit(child)

        for child in node.orelse:
            self.visit(child)

        self.depth -= 1


def analyze_complexity(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return {
            "estimate": "Unavailable",
            "confidence": "None",
            "notes": [
                f"Syntax error on line {error.lineno}: {error.msg}"
            ]
        }

    analyzer = LoopAnalyzer()
    analyzer.visit(tree)

    if analyzer.max_depth >= 3:
        estimate = "O(n³) or higher"
    elif analyzer.max_depth == 2:
        estimate = "O(n²)"
    elif analyzer.max_depth == 1:
        estimate = "O(n)"
    else:
        estimate = "O(1) apparent"

    # Recognize some common halving loops.
    source = ast.unparse(tree)
    if re.search(
        r"while\b[\s\S]*?(?://= *2|/= *2)",
        source
    ):
        estimate = "O(log n) likely"

    # Sorting operations often have O(n log n) cost.
    if any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "sort"
        for node in ast.walk(tree)
    ):
        estimate = "O(n log n) likely"

    return {
        "estimate": estimate,
        "confidence": "Heuristic",
        "notes": [
            f"Detected {analyzer.loop_count} loops.",
            f"Maximum loop nesting: {analyzer.max_depth}.",
            "Loop bounds and library calls may change the "
            "actual complexity.",
            "This estimate is not a formal proof."
        ]
    }


def scan_security(code):
    patterns = [
        (
            r"(?i)(execute|executemany)\s*\(\s*f[\"']",
            "Possible SQL injection",
            "High",
            "Use parameterized SQL queries instead of "
            "string interpolation."
        ),
        (
            r"(?i)(password|api_key|secret|token)\s*="
            r"\s*[\"'][^\"']{4,}[\"']",
            "Possible hardcoded secret",
            "High",
            "Use environment variables or a secrets manager."
        ),
        (
            r"\beval\s*\(",
            "Dynamic eval() usage",
            "High",
            "Avoid eval() on untrusted input. Use a safe parser."
        ),
        (
            r"\bpickle\.loads?\s*\(",
            "Unsafe deserialization risk",
            "High",
            "Never unpickle untrusted data. Prefer JSON."
        ),
        (
            r"\binput\s*\(",
            "Input validation required",
            "Medium",
            "Validate input types, ranges and lengths."
        ),
        (
            r"subprocess\.(run|Popen|call)\s*\("
            r".*shell\s*=\s*True",
            "Shell invocation risk",
            "High",
            "Prefer argument lists with shell=False."
        )
    ]

    findings = []

    for pattern, title, severity, advice in patterns:
        for match in re.finditer(pattern, code):
            line = code.count("\n", 0, match.start()) + 1

            findings.append({
                "title": title,
                "severity": severity,
                "line": line,
                "detail": advice
            })

    return findings


def analyze_code(code, problem="general"):
    complexity = analyze_complexity(code)
    security = scan_security(code)
    target = PROBLEMS.get(problem, PROBLEMS["general"])

    try:
        tree = ast.parse(code)
        functions = sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for node in ast.walk(tree)
        )
    except SyntaxError:
        functions = 0

    return {
        "summary": {
            "status": "complete",
            "complexity": complexity["estimate"],
            "security_issues": len(security)
        },
        "complexity": complexity,
        "optimization": {
            "problem": target["name"],
            "target_time": target["time"],
            "target_space": target["space"],
            "guidance": target["advice"]
        },
        "security": security,
        "metrics": {
            "lines": len(code.splitlines()),
            "characters": len(code),
            "functions": functions
        },
        "limitations": [
            "Complexity is estimated using static heuristics.",
            "The selected problem's target is a common "
            "algorithmic bound, not a proof of optimality.",
            "Security findings are pattern-based and "
            "require manual verification."
        ]
    }