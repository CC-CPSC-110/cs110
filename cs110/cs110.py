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


def install(package: str, *args) -> None:
    """Install the given package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, *args])
    except subprocess.CalledProcessError as e:
        print(f"{RED}Failed to install package: {package}. Error: {e}{RESET}")
        sys.exit(1)


# ANSI color codes
RED = "\033[1;31m"
YELLOW = "\033[33m"
CYAN = "\033[1;36m"
BLUE =  "\033[34m"
GREEN = "\033[1;32m"
RESET = "\033[0m"

def colorize_message(message):
    """Apply colorization to the message for better readability."""
    lines = message.strip().split('\n')
    colored_lines = []

    for line in lines:
        file_part_match = re.search(r"^(.*?\.py:\d+:)", line)
        if file_part_match:
            file_part = file_part_match.group(0)
            line = line.replace(file_part, f"{YELLOW}{file_part}{RESET}")

        error_note_match = re.search(r"(error:|note:)", line)
        if error_note_match:
            type_part = error_note_match.group(0)
            start = line.index(type_part)
            pre_text = line[:start]
            post_text = line[start + len(type_part):]
            colored_type_part = f"{RED}{type_part}{RESET}"

            suggestion_match = re.search(r"(\[.*?\])$", post_text)
            if suggestion_match:
                suggestion_part = suggestion_match.group(0)
                post_text = post_text.replace(suggestion_part, f"{GREEN}{suggestion_part}{RESET}")

            message_part = f"{CYAN}{post_text.strip()}{RESET}"
            line = f"{pre_text}{colored_type_part}{message_part}"
        else:
            line = f"{CYAN}{line}{RESET}"

        colored_lines.append(line)

    return "\n".join(colored_lines)


__version__ = '0.0.1'
sys.tracebacklimit = 0


test_cases = []


def expect(result, *args, equals=None, tolerance=None, description=None):
    """
    Append a test case for later evaluation, with flexibility for keyword and positional 'expected'.
    """
    
    # Handle both cases: positional 'expected' or keyword 'equals'
    if equals is not None:
        expected = equals
    elif len(args) > 0:
        expected = args[0]
    else:
        raise ValueError("Expected value must be provided either positionally or with 'equals' keyword.")
    
    # If no description is provided, use the result itself (less informative)
    if description is None:
        description = f"Result: {result}"
    
    # Special handling for comparing None values using `is`
    if result is None or expected is None:
        test_cases.append((result is expected, description, True, tolerance))
    else:
        # Store the description along with the result, expected value, and tolerance
        test_cases.append((result, description, expected, tolerance))


class Test(unittest.TestCase):
    """Dynamic test case class which will contain dynamically added test methods."""
    pass


class TestUtilities:
    """Utility to dynamically add test cases and run them."""

    @staticmethod
    def add_dynamic_tests() -> None:
        """Create and add dynamic test methods to TestCase based on global test_cases."""
        for index, (result, description, expected, tolerance) in enumerate(test_cases, start=1):
            test_method_name = f'test_{index}: {description} = {expected}'
            test_method = TestUtilities.create_test_method(result, expected, tolerance)
            setattr(Test, test_method_name, test_method)

    @staticmethod
    def create_test_method(result, expected, tolerance):
        """Factory method to create a test method."""
        def test_method(self: Test) -> None:
            if tolerance is not None:
                self.assertAlmostEqual(result, expected, delta=tolerance)
            else:
                self.assertEqual(result, expected)
        return test_method


class CustomTestRunner(unittest.TextTestRunner):
    """Customized Test runner that highlights test results and reports summary."""

    def run(self, test: Any) -> unittest.TestResult:
        result = super().run(test)
        run, errors, failures = result.testsRun, len(result.errors), len(result.failures)
        passed = run - errors - failures
        print(f'{GREEN}PASS: {passed} tests passed{RESET}')
        print(f'{RED}FAIL: {failures} tests failed{RESET}')
        print(f'{BLUE}ERROR: {errors} tests had errors{RESET}')

        if failures > 0 or errors > 0:
            raise Exception("There were errors or test failures!")
        return result


def summarize() -> None:
    """Run dynamically added tests using a custom test runner."""
    TestUtilities.add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)
    
    print(f"{GREEN}Running student-defined tests...{RESET}")
    
    try:
        runner.run(suite)
    except Exception as e:
        print(f"{RED}Error during test execution: {e}{RESET}")

    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename

    try:
        generate_config_files(os.getcwd())

        if caller_file == "<stdin>":
            print("No need to lint the interpreter...")
            return

        lint(caller_file)
        type_check(caller_file)
    except (FileNotFoundError, ImportError, subprocess.CalledProcessError) as e:
        print(f"{RED}An error occurred during code quality checks: {e}{RESET}")


def lint(path: str) -> None:
    """Run pylint on the given path."""
    try:
        print(f"{GREEN}Linting {path}...{RESET}")
        Run([path], reporter=ColorizedTextReporter(), exit=False)
    except FileNotFoundError as e:
        print(f"{RED}Pylint file not found: {e}{RESET}")
    except Exception as e:
        print(f"{RED}Linting error: {e}{RESET}")


def type_check(path: str, config=None) -> None:
    """Run mypy type checking on the given path."""
    try:
        print(f"{GREEN}Type checking {path}...{RESET}")
        cmd = ['mypy', path]
        if config:
            cmd.append(f"--config={config}")
        result = subprocess.run(cmd, text=True, capture_output=True)

        print(colorize_message(result.stdout))
        if result.returncode > 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)
    except FileNotFoundError as e:
        print(f"{RED}Mypy not found: {e}{RESET}")
    except subprocess.CalledProcessError as e:
        print(f"{RED}Type checking failed: {e}{RESET}")
    except Exception as e:
        print(f"{RED}Type checking error: {e}{RESET}")


def generate_config_files(repo_path: str) -> None:
    """Generate pylint and mypy configuration files at the given repository path."""
    pylint_config_path = os.path.join(repo_path, '.pylintrc')
    mypy_config_path = os.path.join(repo_path, 'mypy.ini')

    try:
        if not os.path.exists(pylint_config_path):
            with open(pylint_config_path, 'w') as file:
                file.write("""
[MASTER]
ignore=tests

[MESSAGES CONTROL]
disable=C0301,C0103,C0303,C0304,R1732,R0903,R1705
""")

        if not os.path.exists(mypy_config_path):
            with open(mypy_config_path, 'w') as file:
                file.write("""
[mypy]
disallow_untyped_defs = True
exclude = (tests_repo|tests|venv|build|docs|.git)/

[mypy-*.migrations.*]
ignore_errors = True
""")
        print(f"{GREEN}Configuration files generated.{RESET}")
    except IOError as e:
        print(f"{RED}Error writing config files: {e}{RESET}")


def main(student_repo_path: str, filenames: List[str], tests_path: str) -> None:
    """Main function that sets up testing environment and runs tests."""
    try:
        sys.path.extend([os.path.abspath(student_repo_path), os.path.abspath(tests_path)])
        instructor_tests = importlib.import_module("lesson_tests")
        generate_config_files(student_repo_path)
        
        for filename in filenames:
            module_name = os.path.splitext(os.path.basename(filename))[0]
            student_module = importlib.import_module(module_name)    
            instructor_tests.TestBuilder().build_tests(expect, student_module)

        for filename in filenames:
            lint(os.path.abspath(filename))
        
        type_check(student_repo_path, config=os.path.join(student_repo_path, 'mypy.ini'))
    except (FileNotFoundError, ImportError) as e:
        print(f"{RED}Error: {e}{RESET}")
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{RESET}")
