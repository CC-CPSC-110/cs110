from .cs110 import main  # Adjust this import based on your actual code structure
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests on a student's repository.")
    parser.add_argument("--path", dest="student_repo_path", required=True,
                        help="The path to the student's repository.")
    parser.add_argument("--files", dest="filenames", nargs='+', required=True,
                        help="The filename(s) of the python script(s) to test. Multiple filenames can be provided.")
    parser.add_argument("--tests", dest="tests", required=True,
                        help="Path to file for the tests.")
    
    args = parser.parse_args()
    
    main(args.student_repo_path, args.filenames, args.tests)