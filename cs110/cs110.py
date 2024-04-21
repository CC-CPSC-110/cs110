"""
Testing package for CS 110 at Corpus Christi
install with: pip install git+https://github.com/CC-CPSC-110/cs110.git#egg=cs110 --force
"""
import inspect
import unittest
import os
import sys
import importlib
import subprocess
from typing import Any
import re
from pylint.reporters.text import ColorizedTextReporter
from pylint.lint import Run


__version__ = '0.0'

sys.tracebacklimit = 0

test_cases = []


def expect(func: Any, *args: Any, expected: Any, tolerance: Any=None) -> None:
    """ Get the caller's stack frame and extract the file name"""
    test_cases.append((func, args, expected, tolerance))


class Test(unittest.TestCase):
    """Wrapper for unittest.TestCase"""


def add_dynamic_tests() -> None:
    """Add dynamic tests."""
    for i, (func, args, expected, tolerance) in enumerate(test_cases, start=1):
        test_method_name = f'test_{i}: {func.__name__}{args} = {expected}'
        test_method = create_test_method(func, args, expected, tolerance)
        setattr(Test, test_method_name, test_method)


def create_test_method(func: Any, args: Any, expected: Any, tolerance: Any) -> Any:
    """create test method"""
    def test(self: Any) -> Any:
        actual = func(*args)
        if tolerance is not None:
            self.assertAlmostEqual(actual, expected, delta=tolerance)
        else:
            self.assertEqual(actual, expected)
    return test


class CustomTestRunner(unittest.TextTestRunner): # pylint: disable=too-few-public-methods
    """Customized Test runner"""
    def run(self: Any, test: Any) -> Any:
        "Run the given test case or test suite."
        result = super().run(test)
        run = result.testsRun
        errors = len(result.errors)
        failures = len(result.failures)
        passed = run - errors - failures

        # Update to ensure no leading characters like periods in output lines
        print(f'\033[92mPASS: {passed} tests passed\033[0m')
        print(f'\033[91mFAIL: {failures} tests failed\033[0m')
        print(f'\033[94mERROR: {errors} tests had errors\033[0m')

        if failures > 0 or errors > 0:
            raise Exception("There were errors or test failures!") #pylint: disable=broad-exception-raised, line-too-long

        return result

def summarize() -> None:
    """Run tests"""
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    
    printstr = f"Testing {caller_file}"
    print("=" * len(printstr))
    print(printstr)
    print("=" * len(printstr))

    add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)  # Set verbosity to 0 to suppress default unittest output
    runner.run(suite)

    if caller_file == "<stdin>":
        print("No need to lint the interpreter...")
        return
    
    lint(caller_file)
    typecheck(caller_file)


def build_instructor_tests(student_module: Any, tests: Any) -> Any:
    """Run specified tests on the student module."""
    builder = tests.TestBuilder()
    builder.build_tests(expect, student_module)


def run_tests() -> None:
    """Runs only the tests without linting."""
    add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)  # Set verbosity to 0 to suppress default unittest output
    runner.run(suite)


def typecheck(file_path: str) -> None:
    """Run mypy as a subprocess."""
    print("==========================================")
    print(f"\033[94mRunning type checks on {file_path}\033[0m")

        # subprocess.check_call(
        #     [sys.executable,
        #      "-m", "mypy",
        #      "--disallow-untyped-defs",
        #      "--exclude='.git/'",
        #      file_path])
        
    command = ['mypy', "--disallow-untyped-defs", "--exclude='.git/'", file_path]
    result = subprocess.run(command, text=True, capture_output=True)

    # print(f'\033[92mPASS: {passed} tests passed\033[0m')
    # print(f'\033[91mFAIL: {failures} tests failed\033[0m')
    
    highlighted = re.sub(r"\berror\b", r"\033[91merror\033[0m", result.stdout)

    print(highlighted)
    print(result.stderr)
        
    if result.returncode > 0:
        raise Exception("Failure: please fix type errors.")
    

def lint(filename: str) -> None:
    """Run linting."""
    print("==========================================")
    print("Running linting...")

    reporter = ColorizedTextReporter()
    results = Run(["--disable=C0103,C0303,C0304,R1732,R0903", 
                   filename], reporter=reporter, exit=False)
    if results.linter.stats.global_note < 9.0:
        raise Exception("Too many linting errors.") #pylint: disable=broad-exception-raised


def ensure_init_py(root_dir: str) -> None:
    """Ensure that there's an __init__.py before running mypy or linting"""
    init_py_path = os.path.join(root_dir, '__init__.py')
    if not os.path.isfile(init_py_path):
        open(init_py_path, 'a').close() #pylint: disable=consider-using-with, unspecified-encoding
        print(f"Created __init__.py in {root_dir}")


def main(student_repo_path: str, filenames: list[str], tests_path: str) -> None:
    """Main function to import student modules, load tests and run them."""

    print(f"Running tests and linters for files {filenames} and tests in {tests_path}")
    # Add the student repository path to sys.path to make it available for import
    if student_repo_path not in sys.path:
        sys.path.append(student_repo_path)

    if tests_path not in sys.path:
        sys.path.append(tests_path)

    try:
        tests = importlib.import_module("lesson_tests")
    except ImportError as e:
        print(f"Error importing instructor test module: {e}")
        raise e

    for filename in filenames:
        module_name = os.path.splitext(os.path.basename(filename))[0]
        print(f"Attmpting to import {module_name}.py and build tests...")
        try:
            # Import the module
            student_module = importlib.import_module(module_name)
            print(f"Student module {module_name} imported successfully.")
            build_instructor_tests(student_module, tests)

        except ImportError as e:
            print(f"Error importing module {module_name}: {e}")
            raise e
    
    msg = "Running instructor tests..."
    print("=" * len(msg))
    print("Running instructor tests...\n")
    
    run_tests()
    ensure_init_py(student_repo_path)
    lint(student_repo_path)
    typecheck(student_repo_path)