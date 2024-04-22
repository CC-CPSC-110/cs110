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
        print(f'\033[93mERROR: {errors} tests had errors\033[0m')

        if failures > 0 or errors > 0:
            raise Exception("There were errors or test failures!") #pylint: disable=broad-exception-raised, line-too-long

        return result

def summarize() -> None:
    """Run tests"""
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    
    printstr = f"Testing {caller_file}"
    print(header(printstr))
    print(printstr)
    

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


def blue(message: str) -> str:
    return f"\033[94m{message}\033[0m"

def header(message: str) -> str:
    return '='*len(message)

def typecheck(file_path: str) -> None:
    """Run mypy as a subprocess."""
    message = f"Running type checks on {file_path}"
    print(blue(header(message)))
    print(blue(message))
    
    command = ['mypy', "--disallow-untyped-defs", file_path]
    result = subprocess.run(command, text=True, capture_output=True)

    highlighted = re.sub(r"\berror\b", r"\033[91merror\033[0m", result.stdout)
    highlighted = re.sub(r"\bSuccess:\b", r"\033[92mSuccess\033[0m", result.stdout)

    print(highlighted)
    print(result.stderr)
        
    if result.returncode > 0:
        raise Exception("\033[91mFailure: please fix type errors.\033[0m")
    

def lint(filename: str) -> None:
    """Run linting."""
    message = "Running linting..."
    print(blue(header(message)))
    print(blue(message))

    reporter = ColorizedTextReporter()
    results = Run([
        "--rcfile=.pylintrc",
        filename
    ], reporter=reporter, exit=False)

    if results.linter.stats.global_note < 9.0:
        raise Exception("Too many linting errors.") #pylint: disable=broad-exception-raised


def ensure_init_py(root_dir: str) -> None:
    """Ensure that there's an __init__.py before running mypy or linting"""
    init_py_path = os.path.join(root_dir, '__init__.py')
    if not os.path.isfile(init_py_path):
        open(init_py_path, 'a').close() #pylint: disable=consider-using-with, unspecified-encoding
        print(f"Created __init__.py in {root_dir}")

def generate_config_files(student_repo_path: str) -> None:
    print(f"ignoring {student_repo_path}/tests_repo")
    pylint_config_content = f"""
[MASTER]
ignore={student_repo_path}/tests_repo

[MESSAGES CONTROL]
disable=C0301,C0103,C0303,C0304,R1732,R0903
"""
    print(f'Writing to: {student_repo_path}/.pylintrc')
    with open(f'{student_repo_path}/.pylintrc', 'w') as pylint_config_file:
        pylint_config_file.write(pylint_config_content)
    
    
    mypy_config_content = f"""
[mypy]
disallow_untyped_defs = True
exclude = {student_repo_path}/(tests-repo|venv|build|docs|.git)/

[mypy-*.migrations.*]
ignore_errors = True
"""
    print(f'Writing to: {student_repo_path}/mypy.ini')
    with open(f'{student_repo_path}/mypy.ini', 'w') as mypy_config_file:
        mypy_config_file.write(mypy_config_content)

    print_directory_contents(student_repo_path)
    

def print_directory_contents(path: str) -> None:
    """
    Prints the contents of the specified directory in a pretty format.
    
    :param path: Path to the directory whose contents are to be printed.
    """
    files = []
    directories = []
    
    # Get all entries in the directory specified by path
    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            directories.append(entry)
        else:
            files.append(entry)
    
    print("Directories:")
    for directory in sorted(directories):
        print(f"  [D] {directory}")
    
    print("\nFiles:")
    for file in sorted(files):
        print(f"  [F] {file}") 


def main(student_repo_path: str, filenames: list[str], tests_path: str) -> None:
    """Main function to import student modules, load tests and run them."""

    # Check if .pylintrc exists, if not, generate it
    if not os.path.exists('.pylintrc') and not os.path.exists('mypy.ini'):
        print("No .pylintrc or mypy.ini found, generating default configuration...")
        generate_config_files(student_repo_path)
    else:
        print(".pylintrc or mypy.ini already exists.")
    
    message = f"Running tests and linters for files {filenames} and tests in {tests_path}"
    print(blue(header(message)))
    print(blue(message))

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
    
    msg = "Running instructor tests...\n"
    print(blue(header(msg)))
    print(blue(msg))
    
    run_tests()
    ensure_init_py(student_repo_path)
    lint(student_repo_path)
    typecheck(student_repo_path)