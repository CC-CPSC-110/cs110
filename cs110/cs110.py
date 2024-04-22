import os
import sys
import inspect
import subprocess
import importlib
import unittest
import re
from typing import Any, List, Tuple
from pylint.lint import Run
from pylint.reporters.text import ColorizedTextReporter



# ANSI color codes
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
RESET = "\033[0m"

def colorize_message(message):
    # Split the message into lines
    lines = message.strip().split('\n')
    colored_lines = []
    
    # Regex patterns to identify parts of the message
    error_pattern = re.compile(r"error:")
    note_pattern = re.compile(r"note:")
    suggestion_pattern = re.compile(r"\[.*\]$")
    file_line_pattern = re.compile(r"^\S+\.py:\d+:")
    
    for line in lines:
        # Apply yellow color to file and line part
        file_line_part = file_line_pattern.search(line)
        if file_line_part:
            start, end = file_line_part.span()
            line = (line[:start] + YELLOW + line[start:end] + RESET + line[end:])
        
        # Apply red color to 'error:'
        if "error:" in line:
            start = line.find("error:")
            end = start + len("error:")
            line = (line[:start] + RED + line[start:end] + RESET + line[end:])
        
        # Apply green color to 'note:' and suggestions
        if "note:" in line:
            start = line.find("note:")
            end = start + len("note:")
            line = (line[:start] + RED + line[start:end] + RESET + line[end:])

        suggestion_part = suggestion_pattern.search(line)
        if suggestion_part:
            start, end = suggestion_part.span()
            line = (line[:start] + GREEN + line[start:end] + RESET + line[end:])

        # Apply cyan color to the rest of the message
        if "error:" in line or "note:" in line:
            prefix_end = line.find(":") + 1
            line = line[:prefix_end] + CYAN + line[prefix_end:] + RESET

        colored_lines.append(line)

    return "\n".join(colored_lines)

# Example error message
message = """lesson01.py:7: error: Function is missing a return type annotation  [no-untyped-def]
lesson01.py:7: note: Use "-> None" if function does not return a value
Found 1 error in 1 file (checked 1 source file)"""

# Print the colorized message
print(colorize_message(message))


__version__ = '0.0.1'
sys.tracebacklimit = 0

test_cases: List[Tuple[Any, Tuple[Any, ...], Any, Any]] = []


def expect(func: Any, *args: Any, expected: Any, tolerance: Any = None) -> None:
    """Append a test case for later evaluation."""
    test_cases.append((func, args, expected, tolerance))


class Test(unittest.TestCase):
    """Dynamic test case class which will contain dynamically added test methods."""

    pass


class TestUtilities:
    """Utility to dynamically add test cases and run them."""

    @staticmethod
    def add_dynamic_tests() -> None:
        """Create and add dynamic test methods to TestCase based on global test_cases."""
        for index, (func, args, expected, tolerance) in enumerate(test_cases, start=1):
            test_method_name = f'test_{index}_{func.__name__}'
            test_method = TestUtilities.create_test_method(func, args, expected, tolerance)
            setattr(Test, test_method_name, test_method)

    @staticmethod
    def create_test_method(func: Any, args: Tuple[Any, ...], expected: Any, tolerance: Any) -> Any:
        """Factory method to create a test method."""
        def test_method(self: Test) -> None:
            actual = func(*args)
            if tolerance is not None:
                self.assertAlmostEqual(actual, expected, delta=tolerance)
            else:
                self.assertEqual(actual, expected)
        return test_method


class CustomTestRunner(unittest.TextTestRunner):
    """Customized Test runner that highlights test results and reports summary."""

    def run(self, test: Any) -> unittest.TestResult:
        result = super().run(test)
        run, errors, failures = result.testsRun, len(result.errors), len(result.failures)
        passed = run - errors - failures
        print(f'\033[92mPASS: {passed} tests passed\033[0m')
        print(f'\033[91mFAIL: {failures} tests failed\033[0m')
        print(f'\033[93mERROR: {errors} tests had errors\033[0m')

        if failures > 0 or errors > 0:
            raise Exception("There were errors or test failures!")
        return result


def summarize() -> None:
    """Run dynamically added tests using a custom test runner."""
    TestUtilities.add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)
    runner.run(suite)

    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    

    generate_config_files(os.getcwd())


    if caller_file == "<stdin>":
        print("No need to lint the interpreter...")
        return
    
    try:
        lint(caller_file)
        type_check(caller_file)
    except:
        pass


def lint(path: str) -> None:
    """Run pylint on the given path."""
    Run([path], reporter=ColorizedTextReporter(), exit=False)


def type_check(path: str) -> None:
    """Run mypy type checking on the given path."""
    result = subprocess.run(['mypy', path], text=True, capture_output=True)
    print(colorize_message(result.stdout))
    if result.returncode > 0:
        raise Exception("Type checking failed with errors")


def generate_config_files(repo_path: str) -> None:
    """Generate pylint and mypy configuration files at the given repository path."""
    pylint_config_path = os.path.join(repo_path, '.pylintrc')
    mypy_config_path = os.path.join(repo_path, 'mypy.ini')

    if not os.path.exists(pylint_config_path):
        with open(pylint_config_path, 'w') as file:
            file.write("""
[MASTER]
ignore=tests

[MESSAGES CONTROL]
disable=C0301,C0103,C0303,C0304,R1732,R0903
""")

    if not os.path.exists(mypy_config_path):
        with open(mypy_config_path, 'w') as file:
            file.write("""
[mypy]
disallow_untyped_defs = True
exclude = (tests|venv|build|docs|.git)/

[mypy-*.migrations.*]
ignore_errors = True
""")

    print("Configuration files generated.")


def main(student_repo_path: str, filenames: List[str], tests_path: str) -> None:
    """Main function that sets up testing environment and runs tests."""
    sys.path.extend([student_repo_path, tests_path])
    instructor_tests = importlib.import_module("lesson_tests")
    generate_config_files(student_repo_path)
    
    for filename in filenames:
        module_name = os.path.splitext(os.path.basename(filename))[0]
        student_module = importlib.import_module(module_name)    
        instructor_tests.TestBuilder().build_tests(expect, student_module)

    for filename in filenames:
        lint(filename)
    
    type_check(student_repo_path)

