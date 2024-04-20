"""Testing package for CS 110 at Corpus Christi"""
import inspect
import unittest
import sys
import subprocess
from typing import Any
from pylint.reporters.text import ColorizedTextReporter
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
    print("Running type checks...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "mypy", "--disallow-untyped-defs", caller_file])
    except: # pylint: disable=bare-except
        print("")

    print("==========================================")
    print("Running linting...")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pylint", caller_file])
    except: # pylint: disable=bare-except
        print("")


def run_tests_only():
    """Runs only the tests without linting."""
    add_dynamic_tests()
    suite = unittest.TestLoader().loadTestsFromTestCase(Test)
    runner = CustomTestRunner(verbosity=2)  # Set verbosity to 0 to suppress default unittest output
    runner.run(suite)


def run_tests_then_lint():
    """Run only the tests and linting, but not typechecking. Throws error if fail."""
    run_tests_only()
    caller_frame = inspect.stack()[1]
    caller_file = caller_frame.filename
    if caller_file == "<stdin>":
        print("No need to lint the interpreter...")
        return
    
    print(f"Linting {caller_file}...")

    from pylint.lint import Run
    
    reporter = ColorizedTextReporter()

    results = Run(["--fail-under=7.0", caller_file], reporter=reporter, exit=False)
    
    if results.linter.stats.global_note < 9.0:
        raise Exception("Too many linting errors.")
    # print(f"The final score is: {results.linter.stats.global_note}")
    # print(reporter.out.getvalue())
    # print(f"The value: {reporter.out}")



if __name__ == '__main__':
    summarize()
