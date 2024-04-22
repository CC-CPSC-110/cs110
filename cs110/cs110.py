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
YELLOW = "\033[43m"
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
RESET = "\033[0m"

def colorize_message(message):
    # Split the message into lines
    lines = message.strip().split('\n')
    colored_lines = []

    for line in lines:
        # Apply yellow color to file and line part
        file_part_match = re.search(r"^(.*?\.py:\d+:)", line)
        if file_part_match:
            file_part = file_part_match.group(0)
            line = line.replace(file_part, YELLOW + file_part + RESET)

        # Identify and color 'error:', 'note:', and their messages differently
        error_note_match = re.search(r"(error:|note:)", line)
        if error_note_match:
            type_part = error_note_match.group(0)
            start = line.index(type_part)
            pre_text = line[:start]
            post_text = line[start+len(type_part):]

            # Apply red to 'error:' or 'note:'
            colored_type_part = RED +    + RESET

            # Color code suggestion if it exists
            suggestion_match = re.search(r"(\[.*?\])$", post_text)
            if suggestion_match:
                suggestion_part = suggestion_match.group(0)
                post_text = post_text.replace(suggestion_part, GREEN + suggestion_part + RESET)

            # Apply cyan to the rest of the message part
            message_part = CYAN + post_text.strip() + RESET
            line = pre_text + colored_type_part + message_part

        else:
            # This applies to lines that don't start with the file reference, like summary lines
            line = CYAN + line + RESET

        colored_lines.append(line)

    return "\n".join(colored_lines)


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
            test_method_name = f'test_{index}_{func.__name__}({args}) = {expected}'
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
        print(f'{GREEN}PASS: {passed} tests passed{RESET}')
        print(f'{RED}FAIL: {failures} tests failed{RESET}')
        print(f'{YELLOW}ERROR: {errors} tests had errors{RESET}')

        if failures > 0 or errors > 0:
            raise Exception("There were errors or test failures!")
        return result


def summarize() -> None:
    """Run dynamically added tests using a custom test runner."""
    TestUtilities.add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)
    
    print(f"{GREEN}Running student-defined tests...{RESET}")
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
    print(f"{GREEN}Linting {path}...{RESET}")
    Run([path], reporter=ColorizedTextReporter(), exit=False)


def type_check(path: str) -> None:
    """Run mypy type checking on the given path."""
    print(f"{GREEN}Type checking {path}...{RESET}")
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

