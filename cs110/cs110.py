"""Testing package for CS 110 at Corpus Christi"""
import inspect
import unittest
import os
import sys
import importlib
import subprocess
from typing import Any, List
import json
from pylint.reporters.text import ColorizedTextReporter
from pylint.lint import Run
from io import StringIO

__version__ = '0.0'

sys.tracebacklimit = 0

test_cases = []


def expect(func: Any, *args: Any, expected: Any, tolerance: Any=None) -> None:
    """ Get the caller's stack frame and extract the file name"""
    test_cases.append((func, args, expected, tolerance))


class Test(unittest.TestCase):
    """Wrapper for unittest.TestCase"""


def add_dynamic_tests() -> None:
    """add tests"""
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
            raise Exception("There were errors or test failures!")
            
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

    print("==========================================")
    print("Running linting...")

    lint(caller_file)

    print("==========================================")
    print("Running type checks...")

    try:
        subprocess.check_call(
            [sys.executable, 
             "-m", "mypy", 
             "--disallow-untyped-defs", 
             "--exclude='/\.git/'",
             caller_file])
    except: # pylint: disable=bare-except
        print("")


def load_tests(config_file, module_name):
    """Load test configurations from a JSON file for a specific module."""
    with open(config_file, 'r') as file:
        all_tests = json.load(file)
        return all_tests.get(module_name, [])


def run_instructor_tests(student_module, tests):
    """Run specified tests on the student module."""
    for test in tests:
        func = getattr(student_module, test['function'], None)
        if func is None:
            print(f"Function {test['function']} not found in module.")
            continue
        
        for case in test['tests']:
            args = [convert_type(arg['value'], arg['type']) for arg in case['args']]
            expected = convert_type(case['expected']['value'], case['expected']['type'])
            kwargs = {}
            tolerance = case.get('tolerance')

            if tolerance is not None:
                expect(func, *args, **kwargs, expected=expected, tolerance=tolerance)
            else:
                expect(func, *args, **kwargs, expected=expected)
    run_tests_then_lint_directory(args.student_repo_path)


def convert_type(value, type_str):
    """Convert the value to the specified type."""
    if type_str == "int":
        return int(value)
    elif type_str == "float":
        return float(value)
    elif type_str == "str":
        return str(value)
    elif type_str == "bool":
        return bool(value)
    return value  # Default case if type is not recognized or not specified


def run_tests_only() -> None:
    """Runs only the tests without linting."""
    add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)  # Set verbosity to 0 to suppress default unittest output
    runner.run(suite)


def lint(filename) -> None:
    reporter = ColorizedTextReporter()
    results = Run(["--disable=C0103", filename], reporter=reporter, exit=False)
    if results.linter.stats.global_note < 9.0:
        raise Exception("Too many linting errors.")


def run_tests_then_lint_file() -> None:
    """Run only the tests and linting, but not typechecking. Throws error if fail."""
    run_tests_only()
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    
    if caller_file == "<stdin>":
        print("No need to lint the interpreter...")
        return
    
    print(f"Linting {caller_file}...")
    lint(caller_file)


def ensure_init_py(root_dir: str) -> None:
    init_py_path = os.path.join(root_dir, '__init__.py')
    if not os.path.isfile(init_py_path):
        open(init_py_path, 'a').close()
        print(f"Created __init__.py in {root_dir}")


def run_tests_then_lint_directory(STUDENT_REPO_PATH: str) -> None:
    """Run only the tests and linting, but not typechecking. Throws error if fail."""
    run_tests_only()
    ensure_init_py(STUDENT_REPO_PATH)
    print(f"Linting {STUDENT_REPO_PATH}...")
    lint(STUDENT_REPO_PATH)
    

def main(student_repo_path: str, filenames: List[str], config_file: str):
    """Main function to import student modules, load tests and run them."""

    # Add the student repository path to sys.path to make it available for import
    if student_repo_path not in sys.path:
        sys.path.append(student_repo_path)

    for filename in filenames:
        module_name = filename[:-3]  # Strip the .py from the filename to get the module name
        tests = load_tests(config_file, module_name)

        try:
            # Import the module
            student_module = importlib.import_module(module_name)
            print(f"Student module {module_name} imported successfully.")
            run_instructor_tests(student_module, tests)

        except ImportError as e:
            print(f"Error importing module {module_name}: {e}")
            continue